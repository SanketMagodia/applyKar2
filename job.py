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
    
st.title("Job Matcher")

# User input for skills
user_skills = st.text_input("Enter your skills (comma-separated)").split(',')
user_skills = [skill.strip() for skill in user_skills if skill.strip()]
cursor.execute("SELECT COUNT(*) FROM job_posts WHERE is_applied = 1")
count = cursor.fetchone()[0]
st.write(f'**Roles Applied:** {count}')
def update_is_applied(job_id, applied_status):
    cursor.execute("UPDATE job_posts SET is_applied = ? WHERE id = ?", (applied_status, job_id))
    conn.commit()
def open_job_link(url):
    webbrowser.open(url, new=2)

if user_skills:
    matching_jobs = get_matching_jobs(user_skills)
    st.write(f"**Roles found:** {len(matching_jobs)}")
    
    for job in matching_jobs:
        with st.container():
            # Use a single column for the checkbox
            col1, col2 = st.columns([0.3, 1], vertical_alignment='center')

            # Checkbox on the left side in a single column
            with col1:
                applied = st.checkbox("Applied", key=f"applied_{job['id']}", value=job['is_applied'] == 1)

                # Update the applied status when checkbox is clicked
                if applied != (job['is_applied'] == 1):  # If state has changed
                    update_is_applied(job['id'], 1 if applied else 0)
                if st.button(f"Apply for {job['title']}", key=f"apply_{job['id']}"):
                    open_job_link(job['application_link'])
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
            
else:
    st.write("Please enter your skills to find matching jobs.")
