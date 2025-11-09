# 📚 Books Crawler Project

An automated web crawling and change detection system for [Books to Scrape](https://books.toscrape.com), built with:

- **Python 3.11+**
- **Selenium** for crawling
- **BeautifulSoup4** for parsing
- **MongoDB** for storage
- **FastAPI** for RESTful APIs
- **APScheduler** for scheduled daily updates
- **Redis** + **fastapi-limiter** for API rate limiting

---

## Features

- Automated crawling of book listings (Selenium)  
- Daily scheduled crawl & change detection (APScheduler)  
- MongoDB persistence with content hash versioning  
- RESTful API with FastAPI & API-key authentication  
- Rate limiting (100 req/hour per key)  
- Swagger UI for API testing and documentation  
- Change log for price or availability updates  

---

## Setup Instructions

### Clone and enter the project
```bash
git clone git@github.com:BernardWambua/books_web_crawler.git
cd books-crawler
```
### Create a virtual environment
```bash
python -m venv env
source env/bin/activate     # Linux/macOS
env\Scripts\activate        # Windows
```
### Install dependencies
```bash
pip install -r requirements.txt
```
### Configure environment variables

MONGO_URI=mongodb://localhost:27017

MONGO_DB=books_crawler

SELENIUM_HEADLESS=True

LOG_LEVEL=INFO

### Run MongoDB & Redis (for rate limiting)
```bash
docker run -d -p 27017:27017 mongo
docker run -d -p 6379:6379 redis
```
### Run the crawler manually
```bash
python -m crawler.main
```
### Run the scheduler once (for testing)
```bash
python -m scheduler.worker --run-now
```
### Start the FastAPI server
```bash
uvicorn api.main:app --reload --port 8000
```
Then open Swagger UI at http://localhost:8000/docs

### API Authentication
X-API-Key: your-secret-key

Set this in Swagger UI by clicking the Authorize button.