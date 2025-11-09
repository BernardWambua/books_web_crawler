from fastapi import APIRouter, Depends
from api.security.auth import get_api_key
from api.deps import db

router = APIRouter(prefix="/changes", tags=["Changes"])

@router.get(
    "/",
    summary="View recent changes",
    description="Retrieve recent book updates such as price or availability changes.",
    tags=["Changes"],
    dependencies=[Depends(get_api_key)]
)
def get_recent_changes(limit: int = 20):
    """View recent updates (new books or price/availability changes)."""
    changes = list(db.changelog.find().sort("timestamp", -1).limit(limit))
    for c in changes:
        c["_id"] = str(c["_id"])
    return {"count": len(changes), "changes": changes}
