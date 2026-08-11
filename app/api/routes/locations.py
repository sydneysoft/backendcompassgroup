from fastapi import APIRouter, HTTPException, Query

from app.services.providers.factory import get_transport_provider

router = APIRouter(prefix="/locations", tags=["locations"])


@router.get("")
def search_locations(q: str = Query(min_length=2, max_length=120)) -> dict:
    try:
        items = get_transport_provider().search_locations(q)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return {"items": items}
