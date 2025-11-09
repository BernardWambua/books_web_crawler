from fastapi import APIRouter, Depends, Query, HTTPException
from bson import ObjectId
from typing import Optional
from pymongo import ASCENDING
from api.security.auth import get_api_key
from api.deps import db

router = APIRouter(prefix="/books", tags=["Books"])

@router.get(
    "/",
    summary="List books",
    description="""
    Retrieve a paginated list of books.

    You can filter results by category, price range, or rating.
    Use `sort_by` to order results by rating, price, or number of reviews.
    """,
        dependencies=[Depends(get_api_key)],
        response_description="A paginated list of book objects."
    )
def list_books(
    category: Optional[str] = Query(None, description="Filter by book category"),
    min_price: Optional[float] = Query(None, description="Minimum book price"),
    max_price: Optional[float] = Query(None, description="Maximum book price"),
    rating: Optional[int] = Query(None, ge=1, le=5, description="Book rating (1–5)"),
    sort_by: Optional[str] = Query(None, enum=["rating", "price_including_tax", "num_reviews"]),
    page: int = Query(1, ge=1, description="Page number for pagination"),
    page_size: int = Query(10, le=100, description="Number of books per page"),
):
    """List books with filters, sorting, and pagination."""
    query = {}
    if category:
        query["category"] = category
    if rating:
        query["rating"] = rating
    if min_price is not None or max_price is not None:
        query["price_including_tax"] = {}
        if min_price is not None:
            query["price_including_tax"]["$gte"] = min_price
        if max_price is not None:
            query["price_including_tax"]["$lte"] = max_price
    # MongoDB query
    cursor = db.books.find(query)

    # Sorting (default ascending)
    if sort_by:
        cursor = cursor.sort(sort_by, ASCENDING)

    # Get total count (PyMongo 4+ compatible)
    total = db.books.count_documents(query)

    # Pagination
    cursor = cursor.skip((page - 1) * page_size).limit(page_size)
    results = list(cursor)

    # Convert ObjectId -> str
    for book in results:
        book["_id"] = str(book["_id"])

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "books": results,
    }


@router.get("/{book_id}", dependencies=[Depends(get_api_key)])
def get_book(book_id: str):
    """Return full details about a specific book."""
    try:
        oid = ObjectId(book_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid book ID format")

    book = db.books.find_one({"_id": oid})
    if not book:
        raise HTTPException(status_code=404, detail="Book not found")

    book["_id"] = str(book["_id"])
    return book
