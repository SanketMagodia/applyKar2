import streamlit as st
import pymongo
from pymongo import MongoClient
from datetime import datetime
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
from fuzzywuzzy import fuzz
import re

# Download necessary NLTK data
nltk.download('punkt', quiet=True)
nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)

# Connect to MongoDB
client = MongoClient("mongodb+srv://MAFIA:sank4444@jobs.jr87n.mongodb.net/")
db = client["Jobs"]
collection = db["jobposts"]

def preprocess_text(text):
    # Simple preprocessing: lowercase and remove non-alphanumeric characters
    return re.sub(r'[^a-z0-9\s]', '', text.lower())

def calculate_similarity(user_skill, job_skill):
    # Calculate similarity using fuzzy string matching
    return fuzz.token_sort_ratio(preprocess_text(user_skill), preprocess_text(job_skill))

def match_skills(user_skills, job_tags, threshold=50):
    matched_skills = []
    for user_skill in user_skills:
        for job_tag in job_tags:
            if calculate_similarity(user_skill, job_tag) >= threshold:
                matched_skills.append((user_skill, job_tag))
    return matched_skills

def get_matching_jobs(user_skills):
    matching_jobs = []
    
    for job in collection.find({}):
        job_features = job.get('features', [])
        matched_skills = match_skills(user_skills, list(set(job_features)))
        match_score = len(matched_skills) / len(user_skills) if user_skills else 0
        job['match_score'] = match_score * 100  # Convert to percentage
        job['matched_skills'] = matched_skills
        matching_jobs.append(job)
        
    return sorted(matching_jobs, key=lambda x: x['match_score'], reverse=True)

st.title("Job Matcher")

# User input for skills
user_skills = st.text_input("Enter your skills (comma-separated)").split(',')
user_skills = [skill.strip() for skill in user_skills if skill.strip()]

if user_skills:
    matching_jobs = get_matching_jobs(user_skills)
    st.write(f"**roles found :** {len(matching_jobs)}")
    for job in matching_jobs:
        with st.container():
            col1, col2, col3 = st.columns([3, 1, 1])
            
            with col1:
                st.subheader(job['title'])
                st.write(f"**Company:** {job['company']}")
            
            with col2:
                st.write(f"**Match:** {job['match_score']:.2f}%")
            
            with col3:
                applied = st.checkbox("Applied", key=f"applied_{job['_id']}")

            with st.expander("See Description"):
                st.write(job['description'])
            with st.expander("See matched skills"):
                st.write(f"**Matched Skills:** {'| '.join([str(skill[0])+ '-'+ str(skill[1]) for skill in job['matched_skills']])}")            
            if st.button(f"Apply for {job['title']}", key=str(job['_id'])):
                st.write(f"Redirecting to: {job['application_link']}")
            st.markdown("---")
            

else:
    st.write("Please enter your skills to find matching jobs.")
