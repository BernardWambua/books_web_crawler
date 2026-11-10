"""The Playwright crawler end to end against the local range, with storage faked.

Kept apart from test_guard_e2e.py because the crawler starts its own Playwright,
and the sync API allows only one per thread at a time.
"""
from crawler.browser_scraper import crawl_books_guarded
from tests.range_site import TestRange


def test_crawl_saves_every_book_read_only():
    books = []
    with TestRange() as servers:
        result = crawl_books_guarded(servers.site.url, save=books.append)
        site_calls = servers.site.calls()
        outside_calls = servers.outside.calls()

    assert sorted(book["name"] for book in books) == ["Book 1", "Book 2", "Book 3"]
    assert books[0]["price_including_tax"] == 11.5
    assert result.saved == 3
    assert result.failed == []
    assert outside_calls == []
    assert {method for method, _ in site_calls} == {"GET"}
