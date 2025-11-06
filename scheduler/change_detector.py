import time
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from urllib.parse import urljoin
from datetime import datetime
from utils.hash_utils import fingerprint_book
from crawler.storage import (
    get_all_books,
    get_book_by_source_url,
    upsert_book_doc,
    record_change,
)
from crawler.parser import parse_book_page
from utils.logger import get_logger
import os

logger = get_logger()

def init_driver(headless=True):
    opts = Options()
    if headless:
        opts.add_argument("--headless=new")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--window-size=1920,1080")
    driver = webdriver.Chrome(options=opts)
    return driver

def detect_changes(run_headless=True, alert_threshold_pct=5):
    """
    Iterate existing books in DB, re-fetch pages and detect changes.
    Returns list of change records (inserted into DB).
    """
    driver = init_driver(headless=run_headless)
    changes_report = []

    try:
        cursor = get_all_books()
        for old_doc in cursor:
            source_url = old_doc.get("source_url")
            logger.info(f"Checking {source_url}")
            try:
                driver.get(source_url)
                time.sleep(0.6)
                html = driver.page_source
                # parse into Book model (pydantic) using your parser
                try:
                    new_book = parse_book_page(html, source_url)
                except Exception as e:
                    logger.error(f"Failed to parse {source_url}: {e}")
                    continue

                # new_book is Pydantic model; get dict
                new_doc = new_book.model_dump()
                new_doc["raw_html"] = html
                new_doc["crawl_timestamp"] = datetime.utcnow()

                # compute fingerprints
                old_fp = old_doc.get("content_hash") or ""
                new_fp = fingerprint_book(new_doc)

                if old_fp != new_fp:
                    # identify changed fields (field-level diff)
                    changed_fields = {}
                    fields_to_compare = ["price_including_tax", "price_excluding_tax", "availability", "num_reviews", "rating", "name"]
                    for f in fields_to_compare:
                        old_v = old_doc.get(f)
                        new_v = new_doc.get(f)
                        if old_v != new_v:
                            changed_fields[f] = {"old": old_v, "new": new_v}
                    change_type = "update"
                    # record change
                    rec = record_change(old_doc["_id"], source_url, change_type, changed_fields, old_doc, new_doc)
                    # update book doc (set new fields + new fingerprint)
                    new_doc["content_hash"] = new_fp
                    new_doc["meta"] = old_doc.get("meta", {})
                    new_doc["meta"]["first_seen_at"] = old_doc.get("meta", {}).get("first_seen_at")
                    new_doc["meta"]["last_seen_at"] = datetime.utcnow()
                    upsert_book_doc(new_doc)
                    changes_report.append(rec)

                    # alerting: price drop percent OR availability toggle
                    try:
                        old_price = old_doc.get("price_including_tax") or 0.0
                        new_price = new_doc.get("price_including_tax") or 0.0
                        if old_price and new_price:
                            pct = (old_price - new_price) / old_price * 100
                            if pct >= alert_threshold_pct:
                                logger.warning(f"PRICE DROP ALERT: {source_url} dropped {pct:.2f}% from {old_price} to {new_price}")
                        old_avail = old_doc.get("availability")
                        new_avail = new_doc.get("availability")
                        if old_avail != new_avail:
                            logger.warning(f"AVAILABILITY CHANGED: {source_url}: '{old_avail}' -> '{new_avail}'")
                    except Exception as e:
                        logger.error(f"Error computing alerts for {source_url}: {e}")

                else:
                    # no change — update last_seen + crawl_timestamp
                    upsert_book_doc({
                        **old_doc,
                        "crawl_timestamp": datetime.utcnow(),
                        "content_hash": new_fp,
                        "meta": {**old_doc.get("meta", {}), "last_seen_at": datetime.utcnow()}
                    })
            except Exception as e:
                logger.error(f"Error fetching {source_url}: {e}")
                continue

    finally:
        driver.quit()

    return changes_report
