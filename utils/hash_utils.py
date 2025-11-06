# utils/hash_utils.py
import hashlib
import json
from typing import Dict, Any

def canonicalize_for_hash(d: Dict[str, Any], keys: list):
    """
    Build a canonical dict containing only selected keys (in fixed order).
    """
    out = {}
    for k in keys:
        out[k] = d.get(k)
    return out

def sha256_of_dict(d: Dict[str, Any]) -> str:
    s = json.dumps(d, sort_keys=True, separators=(",", ":"), default=str)
    return hashlib.sha256(s.encode("utf-8")).hexdigest()

def fingerprint_book(doc: Dict[str, Any]) -> str:
    """
    Compute fingerprint based on the most relevant fields.
    Fallback: use raw_html if main fields absent.
    """
    keys = ["name", "price_including_tax", "price_excluding_tax", "availability", "num_reviews", "rating"]
    canonical = canonicalize_for_hash(doc, keys)
    # if all key values are None/empty, fall back to raw_html
    if all(v is None for v in canonical.values()):
        raw = doc.get("raw_html") or ""
        return hashlib.sha256(raw.encode("utf-8")).hexdigest()
    return sha256_of_dict(canonical)
