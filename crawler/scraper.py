import os
import time
import hashlib
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from .parser import parse_book_page
from .storage import upsert_book_doc as upsert_book
from utils.logger import get_logger

logger = get_logger()

def init_driver():
    opts = Options()
    if os.getenv("SELENIUM_HEADLESS", "True").lower() == "true":
        opts.add_argument("--headless=new")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=opts)
    return driver

def crawl_books(base_url="https://books.toscrape.com"):
    driver = init_driver()
    page_num = 1

    try:
        while True:
            page_url = f"{base_url}/catalogue/page-{page_num}.html" if page_num > 1 else base_url
            logger.info(f"Scraping page {page_num}: {page_url}")
            driver.get(page_url)
            time.sleep(1)

            if "Page not found" in driver.page_source:
                logger.info("No more pages found.")
                break

            soup = BeautifulSoup(driver.page_source, "lxml")
            book_links = [
                urljoin(driver.current_url, a.get("href"))
                for a in soup.select("h3 a")
            ]
            if not book_links:
                logger.info("No books found on this page.")
                break

            for link in book_links:
                try:
                    driver.get(link)
                    driver.implicitly_wait(1)
                    html = driver.page_source
                    book = parse_book_page(html, link)
                    upsert_book(book.model_dump())
                    logger.info(f"Saved book: {book.name}")
                except Exception as e:
                    logger.error(f"Error parsing {link}: {e}")
                    continue

            page_num += 1

    finally:
        driver.quit()
