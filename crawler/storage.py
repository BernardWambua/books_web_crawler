import os
from dotenv import load_dotenv
from pymongo import MongoClient, ASCENDING
from datetime import datetime, timezone
from pymongo import ReturnDocument
from bson.objectid import ObjectId
from bson import json_util
from utils.logger import get_logger

logger = get_logger()
load_dotenv()

MONGO_URI = os.getenv("MONGO_URI", "mongodb://localhost:27017")
MONGO_DB = os.getenv("MONGO_DB", "books_crawler")

client = MongoClient(MONGO_URI)
db = client[MONGO_DB]
books_coll = db["books"]
changes_coll = db["changes"]
state_coll = db["crawler_state"]

# indexes
books_coll.create_index([("source_url", ASCENDING)], unique=True)
books_coll.create_index([("category", ASCENDING)])
books_coll.create_index([("price_including_tax", ASCENDING)])
changes_coll.create_index([("detected_at", ASCENDING)])
state_coll.create_index([("key", ASCENDING)], unique=True)

def upsert_book_doc(book_data):
    """Insert or update a book document safely in MongoDB."""

    # Convert any non-serializable fields to JSON-safe dicts
    try:
        safe_data = json_util.loads(json_util.dumps(book_data))
    except Exception as e:
        logger.error(f"Failed to serialize book data for {book_data.get('source_url')}: {e}")
        return None

    try:
        result = books_coll.find_one_and_update(
            {"source_url": safe_data["source_url"]},
            {"$set": safe_data},
            upsert=True,
            return_document=ReturnDocument.AFTER,
        )
        return result
    except Exception as e:
        logger.exception(f"Mongo upsert failed for {safe_data.get('source_url')}: {e}")
        return None

def get_all_books():
    """Return a cursor for all book documents (lightweight fields)."""
    return books_coll.find({})

def get_book_by_source_url(url: str):
    return books_coll.find_one({"source_url": url})

def record_change(book_id, source_url, change_type, changed_fields, old_doc, new_doc):
    payload = {
        "book_id": ObjectId(book_id) if not isinstance(book_id, ObjectId) else book_id,
        "source_url": source_url,
        "change_type": change_type,  # "new" | "update" | "removed"
        "changed_fields": changed_fields,
        "old_snapshot": old_doc,
        "new_snapshot": new_doc,
        "detected_at": datetime.now(timezone.utc)
    }
    changes_coll.insert_one(payload)
    return payload

def set_state(key, value):
    state_coll.update_one({"key": key}, {"$set": {"value": value}}, upsert=True)

def get_state(key, default=None):
    doc = state_coll.find_one({"key": key})
    return doc["value"] if doc else default
