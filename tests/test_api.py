from fastapi.testclient import TestClient
from api.main import app
import pytest

@pytest.fixture(autouse=True)
def mock_rate_limiter(monkeypatch):
    from fastapi_limiter import FastAPILimiter

    async def fake_init(redis):
        return None

    # Disable limiter dependency
    monkeypatch.setattr(FastAPILimiter, "init", fake_init)
    monkeypatch.setattr("api.main.RateLimiter", lambda *a, **k: None)

def test_list_books_unauthorized():
    client = TestClient(app)
    resp = client.get("/books")
    assert resp.status_code == 401


def test_list_books_authorized(monkeypatch):
    client = TestClient(app)

    # Mock DB functions
    mock_books = [{"_id": "1", "name": "Mock Book", "price_including_tax": 20.0}]
    monkeypatch.setattr("api.routers.books.db.books.find", lambda *a, **k: mock_books)
    monkeypatch.setattr("api.routers.books.db.books.count_documents", lambda *a, **k: 1)

    headers = {"X-API-Key": "your-secret-key-here"}
    resp = client.get("/books", headers=headers)
    assert resp.status_code == 200
    data = resp.json()
    assert "books" in data
