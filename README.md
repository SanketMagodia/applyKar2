
# applyKar2


ApplyKar2 is a streamlined job application and management tool. This repository contains two main scripts to run the application and manage the database.




## Features

 - Web Application: Launch and manage the app with ease.
 - Data Management: Scrape job listings from LinkedIn and manage the database with custom options to clear, clean, or update job data.
 

# Getting Started
## Prerequisites

 - Python 3.x installed on your machine.
 - Required Python libraries (```install using pip install -r req.txt```)
## Scripts
### 1. Run the Web Application(if virtual environment named ```env``` in project folder)
#### Simply run ```app.bat``` to start the application site.
 
 if using without ```env``` simply run 
 ```streamlit run job.py```
### 2. Database Management
Use the ```selenium.py``` script to scrape job listings or modify the database as needed. 
```bash
    python selenium.py [options] "https://linkedin.com/jobSearchedUrl"

```
Options:
- ```--clear``` : Clears the entire database.
- ```--clean``` : Removes duplicates and outdated job listings.
- ```--url``` : Specify the URL to scrape job listings (e.g., LinkedIn job pages).
- ```--pages``` : Specify the number of pages to scrape.

Example:
To clear the database, clean old and repeated jobs, and scrape 5 pages of job listings from LinkedIn:
```Python
python selenium.py --clear --clean --url "https://linkedin.com" --pages 5

```

## Installation
### 1. Clone this repository
```
git clone https://github.com/yourusername/applyKar2.git
cd applyKar2
```
### 2. Install dependencies in the virtual environment named ```env``` #Important
``` 
pip install -r requirements.txt
```
### 3. For Selenium code
please open Selenium.py and enter ```USERNAME``` and ```PASSWORD``` for linkedin

## Notes
- Ensure making virtual environment in the folder named ```env``` to make use of bat files
- Ensure proper permissions to run ```app.bat``` on your machine.
