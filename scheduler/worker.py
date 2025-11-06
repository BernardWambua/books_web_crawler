import argparse
import os
import time
from datetime import datetime, timezone
from urllib.parse import urljoin

from apscheduler.schedulers.blocking import BlockingScheduler
from bs4 import BeautifulSoup

from crawler.scraper import init_driver  # reuse driver init for discovery
from crawler.parser import parse_book_page
from crawler.storage import (
    get_book_by_source_url,
    upsert_book_doc,
    record_change,
)
from scheduler.change_detector import detect_changes
from utils.logger import get_logger
from utils.reports import write_reports
from utils.hash_utils import fingerprint_book

logger = get_logger()

BASE_URL = os.getenv("BASE_URL", "https://books.toscrape.com")


def discover_new_books(driver):
    """Crawl index pages for new book links and insert any missing books."""
    page_num = 1
    new_count = 0

    while True:
        page_url = BASE_URL if page_num == 1 else f"{BASE_URL}/catalogue/page-{page_num}.html"
        logger.info(f"Discovering page: {page_url}")
        driver.get(page_url)
        time.sleep(0.6)

        soup = BeautifulSoup(driver.page_source, "lxml")
        anchors = soup.select("h3 a")
        if not anchors:
            break  # No more pages

        for a in anchors:
            # href = a.get("href")
            # link = urljoin(driver.current_url, href)
            href = a.get("href")
            link = urljoin(page_url, href)

            # Skip if already in DB
            if get_book_by_source_url(link):
                continue

            logger.info(f"New book found: {link}")
            try:
                driver.get(link)
                time.sleep(0.5)
                html = driver.page_source

                # Parse book details
                book = parse_book_page(html, link)
                book_data = book.model_dump()
                book_data["raw_html"] = html
                book_data["meta"] = {
                    "first_seen_at": datetime.now(timezone.utc),
                    "last_seen_at": datetime.now(timezone.utc),
                }
                book_data["content_hash"] = fingerprint_book(book_data)

                # Upsert into DB
                res = upsert_book_doc(book_data)

                # Record change log
                record_change(
                    res["_id"],
                    link,
                    "new",
                    {"created": True},
                    None,
                    book_data,
                )
                new_count += 1

            except Exception as e:
                logger.error(f"Failed to parse during discovery {link}: {e}")
                continue

        page_num += 1

    return new_count


def run_cycle():
    """Perform one full crawl + change detection cycle."""
    logger.info("Starting discovery and change-detection cycle...")

    driver = init_driver()
    try:
        new_count = discover_new_books(driver)
        logger.info(f"Discovery complete — {new_count} new books added.")
    finally:
        driver.quit()

    # Run change detection
    changes = detect_changes(run_headless=True)
    logger.info(f"Change detection complete — {len(changes)} updates found.")

    # Generate daily report
    report_path = write_reports(changes)
    logger.info(f"Report generated at: {report_path}")


def main(run_once=False):
    """Run the scheduler loop (daily at 03:00) or immediately once."""
    if run_once:
        run_cycle()
        return

    scheduler = BlockingScheduler()
    scheduler.add_job(run_cycle, "cron", hour=3, minute=0)
    logger.info("Scheduler started (daily at 03:00).")

    try:
        scheduler.start()
    except (KeyboardInterrupt, SystemExit):
        logger.info("Scheduler stopped.")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Book crawler scheduler")
    parser.add_argument(
        "--run-now",
        action="store_true",
        help="Run the discovery + detection cycle immediately and exit.",
    )
    args = parser.parse_args()
    main(run_once=args.run_now)
