import mongomock
from crawler.storage import upsert_book_doc

def test_upsert_book_doc(monkeypatch):
    mock_client = mongomock.MongoClient()
    db = mock_client["test_db"]
    monkeypatch.setattr("crawler.storage.books_coll", db["books"])

    book_data = {
        "title": "Test Book",
        "price_incl_tax": 10.5,
        "category": "Fiction",
        "source_url": "https://example.com/book1",
        "rating": 4,
        "availability": "In stock",
        "raw_html": "<html></html>",
    }

    result = upsert_book_doc(book_data)
    assert result["title"] == "Test Book"
    assert db["books"].count_documents({}) == 1
