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

## Data Models

### Book Document Structure
```json
{
    "_id": ObjectId("..."),
    "name": "Sample Book Title",
    "description": "Book description text...",
    "category": "Fiction",
    "price_including_tax": 19.99,
    "price_excluding_tax": 16.99,
    "availability": "In stock (23 available)",
    "num_reviews": 3,
    "image_url": "https://books.toscrape.com/...",
    "rating": 4,
    "source_url": "https://books.toscrape.com/catalogue/sample-book_123/",
    "crawl_timestamp": "2025-11-09T10:30:00Z",
    "content_hash": "sha256-hash-of-content",
    "meta": {
        "first_seen_at": "2025-11-08T00:00:00Z",
        "last_seen_at": "2025-11-09T10:30:00Z"
    }
}
```

### Change Log Document Structure
```json
{
    "_id": ObjectId("..."),
    "book_id": ObjectId("..."),
    "source_url": "https://books.toscrape.com/catalogue/sample-book_123/",
    "type": "price_change",
    "changes": {
        "price_including_tax": {
            "old": 19.99,
            "new": 15.99
        }
    },
    "timestamp": "2025-11-09T10:30:00Z"
}
```

## API Endpoints

### GET /books
List books with filtering and pagination.

Query Parameters:
- `category`: Filter by book category
- `min_price`, `max_price`: Price range filter
- `rating`: Filter by rating (1-5)
- `sort_by`: Sort by "rating", "price_including_tax", or "num_reviews"
- `page`: Page number (default: 1)
- `page_size`: Items per page (default: 10, max: 100)

Example:
```bash
curl -H "X-API-Key: your-key" "http://localhost:8000/books/?category=Fiction&min_price=10&max_price=20&sort_by=rating&page=1"
```

### GET /books/{book_id}
Get detailed information about a specific book.

Example:
```bash
curl -H "X-API-Key: your-key" "http://localhost:8000/books/507f1f77bcf86cd799439011"
```

### GET /changes
View recent book changes (price changes, availability updates, etc.)

Query Parameters:
- `limit`: Number of recent changes to return (default: 20)

Example:
```bash
curl -H "X-API-Key: your-key" "http://localhost:8000/changes?limit=10"
```

## Running Tests

```bash
# Install test dependencies
pip install pytest pytest-asyncio pytest-cov

# Run all tests
pytest

# Run tests with coverage report
pytest --cov=src --cov-report=html

# Run specific test file
pytest tests/test_crawler.py -v
```

## Sample Logs

### Successful Crawl
```
2025-11-09 10:30:00 INFO  [crawler] Starting crawl of https://books.toscrape.com
2025-11-09 10:30:01 INFO  [crawler] Found 1000 books across 50 pages
2025-11-09 10:35:00 INFO  [crawler] Crawl complete - 1000 books processed
```

### Change Detection
```
2025-11-09 11:00:00 INFO  [scheduler] Starting change detection cycle
2025-11-09 11:00:01 INFO  [scheduler] Found 5 price changes
2025-11-09 11:00:02 INFO  [scheduler] Found 2 availability changes
2025-11-09 11:00:03 INFO  [scheduler] Change detection complete
```

## Development Notes

- The crawler uses Selenium in headless mode by default (configurable via SELENIUM_HEADLESS)
- Rate limiting requires a Redis instance (defaults to localhost:6379)
- Email alerts use Gmail SMTP (requires App Password if 2FA is enabled)
- MongoDB indexes are created automatically on first run