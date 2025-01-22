from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import time
from datetime import datetime, timedelta
import pymongo
from ojd_daps_skills.extract_skills.extract_skills import SkillsExtractor
sm = SkillsExtractor(taxonomy_name="toy")

# Connect to MongoDB
CLIENT = pymongo.MongoClient("mongodb+srv://MAFIA:sank4444@jobs.jr87n.mongodb.net/")
LINK = "https://www.linkedin.com/jobs/search/?currentJobId=4131209300&f_E=2&f_TPR=r86400&geoId=103644278&keywords=software%20engineer&origin=JOB_SEARCH_PAGE_JOB_FILTER&refresh=true"
# Access the 'jobs' database
db = CLIENT["Jobs"]
# Access the 'jobposts' collection
collection = db["jobposts"]

# Open the Chrome browser
driver = webdriver.Chrome() 
driver.get("https://www.linkedin.com/login")

time.sleep(1)
driver.find_element(By.CSS_SELECTOR, 'input[id="username"]').send_keys("sanket4461@gmail.com")
driver.find_element(By.CSS_SELECTOR, 'input[id="password"]').send_keys("sank4444")
driver.find_element(By.CSS_SELECTOR, 'button[type="submit"]').click()
time.sleep(1)
driver.get(LINK)
i = 1
time.sleep(1)
try:
    while True:
        scrollable_element = driver.find_element(By.CSS_SELECTOR, "#main > div > div.scaffold-layout__list-detail-inner.scaffold-layout__list-detail-inner--grow > div.scaffold-layout__list > div")
        # Scroll slowly
        scroll_height = driver.execute_script("return arguments[0].scrollHeight", scrollable_element)
        for sc in range(0, scroll_height, 100):
            driver.execute_script(f"arguments[0].scrollTop = {sc}", scrollable_element)
            time.sleep(0.5)
            
        jobsInPage = len(driver.find_elements(By.CLASS_NAME, "job-card-container"))
        print(f"jobs in page -: {jobsInPage}")
        for f in range(jobsInPage):
            driver.find_elements(By.CLASS_NAME, "job-card-container")[f].click()
            time.sleep(3)
            link = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title").find_element(By.TAG_NAME, "a").get_attribute("href")
            if not link:
                continue
            # Check if the job with this link already exists in the database
            existing_job = collection.find_one({"application_link": link})

            if existing_job:
                print(f"Job with link already exists in the database. Skipping.")
                continue

            desc = driver.find_element(By.ID, "job-details").text
            job_ad_with_skills = sm([desc])  
            features = [ent.text for ent in job_ad_with_skills[0].ents if ent.label_ != 'BENEFIT']
            company = driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__company-name").text
            
            spamFlag = 0
            for spam in ['dice']:
                if spam in company.lower():
                    print("skipping {spam} jobs..")
                    spamFlag = 1
            if spamFlag == 1:
                continue
            
            job_post = {
            "title": driver.find_element(By.CLASS_NAME, "job-details-jobs-unified-top-card__job-title").text,
            "company": company,
            "description": desc,
            "application_link": link,
            "date_added": datetime.now(),
            "features": features
            }
            result = collection.insert_one(job_post)

            print(f"inserted jobs -: {i}")
            i+=1
            
        print("waiting for 50 sec")
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

def remove_duplicates_and_old_jobs():
    # Get the date one week ago
    one_week_ago = datetime.now() - timedelta(days=7)

    # Find all unique application links
    unique_links = collection.distinct("application_link")

    # Counter for removed duplicates and old jobs
    removed_duplicates = 0
    removed_old_jobs = 0

    for link in unique_links:
        # Find all documents with this application link
        documents = list(collection.find({"application_link": link}))
        
        if len(documents) > 1:
            # Keep the most recent document
            documents.sort(key=lambda x: x.get("date_added", datetime.min), reverse=True)
            latest_doc = documents[0]
            
            # Remove duplicates
            for doc in documents[1:]:
                collection.delete_one({"_id": doc["_id"]})
                removed_duplicates += 1
        else:
            latest_doc = documents[0]

        # Check if the job is older than one week
        if latest_doc.get("date_added", datetime.min) < one_week_ago:
            collection.delete_one({"_id": latest_doc["_id"]})
            removed_old_jobs += 1

    print(f"Removed {removed_duplicates} duplicate job postings.")
    print(f"Removed {removed_old_jobs} job postings older than one week.")