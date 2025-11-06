import os
import pytest
from src.crawler.selenium import BooksCrawler

def test_bookscrawler_initialization(monkeypatch):
    # Ensure headless mode for tests
    monkeypatch.setenv("HEADLESS", "1")
    crawler = None
    try:
        crawler = BooksCrawler()
        assert hasattr(crawler, "driver")
        assert crawler.driver is not None
        assert hasattr(crawler, "wait")
    finally:
        if crawler:
            crawler.close()

def test_load_homepage_title(monkeypatch):
    # Ensure headless mode for tests
    monkeypatch.setenv("HEADLESS", "1")
    crawler = None
    try:
        crawler = BooksCrawler()
        crawler.driver.get(crawler.base_url)
        title = crawler.driver.title or ""
        assert "Books to Scrape" in title
    finally:
        if crawler:
            crawler.close()