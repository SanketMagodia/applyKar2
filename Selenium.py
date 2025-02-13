from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta
from ojd_daps_skills.extract_skills.extract_skills import SkillsExtractor
from contextlib import closing
import sqlite3
import argparse
from selenium.webdriver.chrome.options import Options
from dotenv import load_dotenv
import os
'''
How to run the code: python selenium.py --clear --clean --url "https://linkedin.com" --pages 10

'''
# linkedin credentials


def clean_database(table_name='job_posts'):
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    try:
        # Delete all rows from the table
        cursor.execute(f"DELETE FROM {table_name}")
        conn.commit()  # Save changes
        print(f"All data from the table '{table_name}' has been cleared.")
    except sqlite3.Error as e:
        print(f"An error occurred while clearing the table '{table_name}': {e}")
    finally:
        # Close the connection
        conn.close()

def remove_duplicates_and_old_jobs(database_path='jobs.db'):
    # Get the date one week ago
    one_week_ago = datetime.now() - timedelta(days=2)

    removed_duplicates = 0
    removed_old_jobs = 0

    try:
        with closing(sqlite3.connect(database_path)) as conn:
            with conn:  # This automatically commits or rolls back
                cursor = conn.cursor()

                # Find all unique description links
                cursor.execute("SELECT DISTINCT description FROM job_posts")
                unique_desc = cursor.fetchall()

                for (desc,) in unique_desc:
                    # Find all records with this application desc
                    cursor.execute("SELECT id, date_added FROM job_posts WHERE description = ?", (desc,))
                    documents = cursor.fetchall()

                    if len(documents) > 1:
                        # Keep the most recent document
                        documents.sort(key=lambda x: datetime.fromisoformat(x[1]), reverse=True)
                        latest_doc_id = documents[0][0]

                        # Remove duplicates
                        for doc_id, _ in documents[1:]:
                            cursor.execute("DELETE FROM job_posts WHERE id = ?", (doc_id,))
                            removed_duplicates += 1
                    else:
                        latest_doc_id = documents[0][0]

                    # Check if the most recent job is older than one week
                    cursor.execute("SELECT date_added FROM job_posts WHERE id = ?", (latest_doc_id,))
                    latest_doc_date = datetime.fromisoformat(cursor.fetchone()[0])
                    if latest_doc_date < one_week_ago:
                        cursor.execute("DELETE FROM job_posts WHERE id = ?", (latest_doc_id,))
                        removed_old_jobs += 1

        print(f"Removed {removed_duplicates} duplicate job postings.")
        print(f"Removed {removed_old_jobs} job postings older than one week.")

    except sqlite3.Error as e:
        print(f"An error occurred: {e}")



def process_url(LINK, pages = 10):
    load_dotenv()
    USERNAME = os.getenv("USER_NAME")
    PASSWORD = os.getenv("PASSWORD")
    print(USERNAME, PASSWORD)
    sm = SkillsExtractor(taxonomy_name="toy")
    #sqlite
    conn = sqlite3.connect('jobs.db')
    cursor = conn.cursor()
    # Open the Chrome browser
    chrome_options = Options()
    chrome_options.add_argument("--disable-webrtc")
    chrome_options.add_argument("--disable-gpu")
    # chrome_options.add_argument("--headless=new")
    driver = webdriver.Chrome(options=chrome_options)
    driver.get("https://www.linkedin.com/login")

    time.sleep(1)
    driver.find_element(By.CSS_SELECTOR, 'input[id="username"]').send_keys(USERNAME)
    driver.find_element(By.CSS_SELECTOR, 'input[id="password"]').send_keys(PASSWORD)
    driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
    time.sleep(1)
    driver.get(LINK)
    i = 1
    time.sleep(1)
    page = 0
    try:
        while page <= int(pages):
            scrollable_element = driver.find_element(By.CSS_SELECTOR, "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div")
            # Scroll slowly
            scroll_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_element)
            for sc in range(0, scroll_height, 100):
                driver.execute_script(f"arguments[0].scrollTop = {sc}", scrollable_element)
                time.sleep(0.2)
                
            jobsInPage = len(driver.find_elements(By.CLASS_NAME, "job-card-container"))
            print(f"jobs in page -: {jobsInPage}")
            for f in range(jobsInPage):
                driver.find_elements(By.CLASS_NAME, "job-card-container")[f].click()
                time.sleep(3)
                link = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title").find_element(By.TAG_NAME, "a").get_attribute("href")
                if not link:
                    print("No link found. Skipping.")
                    continue

                desc = driver.find_element(By.ID, "job-details").text
                # Check if the job with this description already exists in the database
                cursor.execute("SELECT * FROM job_posts WHERE description = ?", (desc,))
                existing_job = cursor.fetchone()  # Fetch the result, if any

                if existing_job:
                    print("Job already exists in the database. Skipping.")
                    continue

                job_ad_with_skills = sm([desc])  
                features = [ent.text for ent in job_ad_with_skills[0].ents if ent.label_ != 'BENEFIT']
                company = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name").text
                
                spamFlag = 0
                for spam in ['dice']:
                    if spam in company.lower():
                        print(f"skipping {spam} jobs..")
                        spamFlag = 1
                if spamFlag == 1:
                    continue
                
            
                job_post = {
                    "title": driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title").text,
                    "company": company,
                    "description": desc,
                    "application_link": link,
                    "date_added": datetime.now().isoformat(),  # Store as ISO string
                    "features": ', '.join(features),  # Convert features to a comma-separated string if it's a list
                    "is_applied":0
                }
                
                cursor.execute('''
                INSERT INTO job_posts (title, company, description, application_link, date_added, features, is_applied)
                VALUES (?, ?, ?, ?, ?, ?,?)
                ''', (job_post["title"], job_post["company"], job_post["description"],
                    job_post["application_link"], job_post["date_added"], job_post["features"], job_post["is_applied"]))
                conn.commit()

                print(f"inserted jobs -: {i}")
                i+=1
                
            page += 1
            print(f"waiting for 50 sec. Done with page {page}")
            time.sleep(50)
            selectors = driver.find_element(By.CLASS_NAME, "artdeco-pagination__pages")
            NEXT_PAGE=0
            for j in range(len(selectors.find_elements(By.TAG_NAME, "li"))):
                try:
                    selectors.find_elements(By.TAG_NAME, "li")[j].find_element(By.CSS_SELECTOR, 'button[aria-current="true"]')
                    NEXT_PAGE = j+1
                    break
                except:
                    pass
            
            selectors.find_elements(By.TAG_NAME, "li")[NEXT_PAGE].click()
    except:
        pass

if __name__ == "__main__":

    parser = argparse.ArgumentParser(description="Process database commands and a URL.")
    parser.add_argument("--clear", action="store_true", help="Clear the database.")
    parser.add_argument("--clean", action="store_true", help="Remove duplicates and old jobs from the database.")
    parser.add_argument("--url", type=str, help="URL to process.")
    parser.add_argument("--pages", type=str, help="how many pages to scrape ?")
    # Parse the arguments
    args = parser.parse_args()

    # Execute actions based on arguments
    if args.clear:
        clean_database()
    if args.clean:
        remove_duplicates_and_old_jobs()
    # Extract URL argument
    if args.url:
        process_url(LINK = args.url, pages = args.pages)

    # Print the stored LINK for confirmation
    print(f"Done")



