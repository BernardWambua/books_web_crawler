"""Crawl the book site with a guarded Playwright browser (see crawler/guard.py)."""
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from playwright.sync_api import sync_playwright

from utils.logger import get_logger

from .guard import Blocked, GuardedBrowser, PlaywrightError, Policy
from .parser import parse_book_page

logger = get_logger()


@dataclass
class CrawlResult:
    saved: int = 0
    failed: List[str] = field(default_factory=list)
    blocked: List[Blocked] = field(default_factory=list)


def _default_save(book: dict) -> None:
    # Imported here because importing storage opens a MongoDB connection.
    from .storage import upsert_book_doc

    upsert_book_doc(book)


def crawl_books_guarded(
    base_url: str = "https://books.toscrape.com",
    save: Optional[Callable[[dict], None]] = None,
    headless: bool = True,
) -> CrawlResult:
    """Crawl every listing page and save each book. Only base_url's host can be reached."""
    save = save or _default_save
    base_url = base_url.rstrip("/")
    result = CrawlResult()

    with sync_playwright() as playwright, GuardedBrowser(
        playwright, Policy.for_url(base_url), headless=headless
    ) as guarded:
        page = guarded.context.new_page()
        page_num = 1
        while True:
            page_url = f"{base_url}/catalogue/page-{page_num}.html" if page_num > 1 else f"{base_url}/"
            logger.info(f"Scraping page {page_num}: {page_url}")
            try:
                response = page.goto(page_url, wait_until="domcontentloaded")
            except PlaywrightError as e:
                logger.error(f"Could not open {page_url}: {e}")
                result.failed.append(page_url)
                break
            if response is None or response.status == 404:
                logger.info("No more pages found.")
                break

            links = page.eval_on_selector_all("h3 a", "links => links.map(a => a.href)")
            if not links:
                logger.info("No books found on this page.")
                break

            for link in links:
                try:
                    page.goto(link, wait_until="domcontentloaded")
                    book = parse_book_page(page.content(), link)
                    save(book.model_dump())
                    result.saved += 1
                    logger.info(f"Saved book: {book.name}")
                except Exception as e:
                    logger.error(f"Error parsing {link}: {e}")
                    result.failed.append(link)

            page_num += 1

        result.blocked = list(guarded.blocked)

    return result


if __name__ == "__main__":
    outcome = crawl_books_guarded()
    logger.info(f"Saved {outcome.saved}, failed {len(outcome.failed)}, blocked {len(outcome.blocked)}")
