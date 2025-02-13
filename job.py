import streamlit as st
import sqlite3
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from fuzzywuzzy import fuzz
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import re
import webbrowser
import llm
import Selenium

nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
conn = sqlite3.connect('jobs.db')
cursor = conn.cursor()
# Preprocess text: Remove non-alphanumeric characters and lowercase the text
def preprocess_text(text):
    text = re.sub(r'[^a-z0-9\s]', '', text.lower())  # Remove non-alphanumeric characters
    return text

# Tokenize, remove stopwords, and lemmatize
def tokenize_and_lemmatize(text):
    lemmatizer = WordNetLemmatizer()
    stop_words = set(stopwords.words('english'))
    tokens = word_tokenize(text)
    cleaned_tokens = [lemmatizer.lemmatize(word) for word in tokens if word not in stop_words]
    return ' '.join(cleaned_tokens)

# TF-IDF Vectorizer for job description matching
def get_tfidf_vectorizer(corpus):
    tfidf = TfidfVectorizer()
    return tfidf.fit_transform(corpus)

# Fuzzy matching for user skills
def calculate_fuzzy_similarity(user_skill, job_skill):
    return fuzz.token_sort_ratio(preprocess_text(user_skill), preprocess_text(job_skill))

# Match user skills to job features using fuzzy string matching and TF-IDF for descriptions
def match_skills_and_description(user_skills, job_description, job_features, threshold=70):
    matched_skills = []
    
    # Fuzzy matching for user skills and job features
    for user_skill in user_skills:
        for job_tag in job_features:
            if calculate_fuzzy_similarity(user_skill, job_tag) >= threshold:
                matched_skills.append((user_skill, job_tag))
    
    # TF-IDF Vectorization for job descriptions
    job_description = preprocess_text(job_description)
    user_skills_str = ' '.join(user_skills)
    all_text = [job_description, user_skills_str]  # Combine job description and user skills for matching
    tfidf_matrix = get_tfidf_vectorizer(all_text)
    
    # Cosine Similarity for the descriptions
    cosine_sim = cosine_similarity(tfidf_matrix[0:1], tfidf_matrix[1:])
    description_match_score = cosine_sim[0][0] * 100  # Convert to percentage
    
    return matched_skills, description_match_score



def get_matching_jobs(user_skills):
    matching_jobs = []
    
    # Fetch jobs from SQLite database
    cursor.execute("SELECT * FROM job_posts")
    rows = cursor.fetchall()
    
    for row in rows:
        # Unpack job details
        job_id, title, company, description, application_link, date_added, features, is_applied = row
        job_features = features.split(",") if features else []
        
        # Match skills using fuzzy matching
        matched_skills, description_match_score = match_skills_and_description(user_skills, description, job_features)
        
        # Final match score is a weighted combination of skill match and description match score
        skill_match_score = len(matched_skills) / len(user_skills) if user_skills else 0
        final_match_score = (skill_match_score * 0.4) + (description_match_score * 0.6)  # 40% skill match, 60% description match
        
        job = {
            'id': job_id,
            'title': title,
            'company': company,
            'description': description,
            'application_link': application_link,
            'date_added': date_added,
            'features': job_features,
            'match_score': final_match_score * 100,  # Convert to percentage
            'matched_skills': matched_skills,
            'is_applied': is_applied
        }
        matching_jobs.append(job)
    
    return sorted(matching_jobs, key=lambda x: x['match_score'], reverse=True)
    
st.title("Lets see what you looking for ...")

# User input for skills
col1, col2 = st.columns([1, 1], vertical_alignment='center')
with col1:
    if st.button("filter and remove old Jobs"):
        Selenium.remove_duplicates_and_old_jobs()
with col2:
    if st.button("Clean database"):    
        Selenium.clean_database()

with st.expander("Scrape new jobs"):
    col1, col2, col3 = st.columns([1, 1, 0.3], vertical_alignment='center')
    with col1:
        url = st.text_input("Enter URL")
    with col2:
        pages = st.text_input("Enter number of pages")
    with col3:
        if st.button("Process"):
            Selenium.process_url(LINK = url, pages = int(pages))
    
user_skills = st.text_input("Enter your skills (comma-separated)").split(',')
user_skills = [skill.strip() for skill in user_skills if skill.strip()]
cursor.execute("SELECT COUNT(*) FROM job_posts WHERE is_applied = 1")
count = cursor.fetchone()[0]
cursor.execute("SELECT COUNT(*) FROM job_posts")
NoOfJobs = cursor.fetchone()[0]
st.write(f'**Roles Applied:** {count} / {NoOfJobs}')

def update_is_applied(job_id, applied_status):
    cursor.execute("UPDATE job_posts SET is_applied = ? WHERE id = ?", (applied_status, job_id))
    conn.commit()
def open_job_link(url):
    webbrowser.open(url, new=2)

def generate_text_function(description):
    return llm.generate_cover_letter(description)  
def print_text_function(text, title, company):
    llm.create_cover_letter_pdf(text, title, company)
with st.sidebar:
    # Create a text area inside the expander
    st.write(f"**Cover Letter Maker**")
    title = st.text_input("Title:")
    company = st.text_input("Company:")
    text_input = st.text_area("Cover Letter Generator:", height=400)
    if st.button("Save pdf"):
        print_text_function(text_input, title, company)
if user_skills:
    matching_jobs = get_matching_jobs(user_skills)
    st.write(f"**Roles found:** {len(matching_jobs)}")
    
    for job in matching_jobs:
        with st.container():
            col1, col2 = st.columns([0.3, 1], vertical_alignment='center')

            with col1:
                applied = st.checkbox("Applied", key=f"applied_{job['id']}", value=job['is_applied'] == 1)

                if applied != (job['is_applied'] == 1):
                    update_is_applied(job['id'], 1 if applied else 0)
                
                if st.button(f"Apply for {job['title']}", key=f"apply_{job['id']}"):
                    open_job_link(job['application_link'])
                
                # New button to generate text
                if st.button("Generate Cover letter", key=f"generate_{job['id']}"):
                    generated_text = generate_text_function(job['description'])  # Replace with your text generation function
                    st.session_state[f"text_{job['id']}"] = generated_text
            # Job Title and Company in the second column
            with col2:
                # Card-like container with styling
                st.html(f"""
                    <div style="background-color: #2e2e2e; border-radius: 10px; padding: 20px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.3); margin-bottom: 20px; color: white;">
                        <div style="display: flex; justify-content: flex-start; align-items: center;">
                            <div style="flex: 1; font-size: 18px; font-weight: bold; color: #f39c12;">
                                {job['title']}
                            </div>
                            <div style="margin-top: 20px;">
                            <button  style="background-color: #e74c3c; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-weight: bold;">
                                {job['company']}
                            </button>
                        </div>
                        </div>
                        
                        
                        

                        <div style="margin-top: 20px; font-size: 14px;">
                            <div style="font-weight: bold; color: #f39c12;">Matched Skills:</div>
                            <div style="color: #dcdde1;">{' - '.join([f'[{skill[0]} - {skill[1]}]' for skill in job['matched_skills']])}</div>
                        </div>

                        <div style="margin-top: 20px;">
                            <details style="background-color: #34495e; padding: 15px; border-radius: 5px; color: white;">
                                <summary style="cursor: pointer; font-weight: bold; color: #ecf0f1;">See Description</summary>
                                <p style="white-space: pre-line; color: white;">{job['description']}</p>
                            </details>
                        </div>
                    </div>
                """)
            if f"text_{job['id']}" in st.session_state:
                edited_text = st.text_area("Edit generated text:", st.session_state[f"text_{job['id']}"], key=f"edit_{job['id']}")
                st.button("Save pdf", key=f"print_{job['id']}")
                print_text_function(edited_text, job['title'], job['company'])  # Replace with your 
            
else:
    st.write("Please enter your skills to find matching jobs.")
