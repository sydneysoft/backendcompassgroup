from datetime import datetime, timedelta, timezone
from decimal import Decimal

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import JourneyCache, Search
from app.schemas.search import JourneyOut, SearchCreate, SearchOut
from app.services.providers.base import ProviderSearchRequest
from app.services.providers.factory import get_transport_provider

router = APIRouter(prefix="/searches", tags=["searches"])


def cache_to_out(item: JourneyCache) -> JourneyOut:
    p = item.payload
    return JourneyOut(
        id=item.id,
        provider=item.provider,
        provider_journey_id=item.provider_journey_id,
        operator_name=p["operator_name"],
        operator_logo_url=p.get("operator_logo_url"),
        origin_name=p["origin_name"],
        origin_station=p["origin_station"],
        destination_name=p["destination_name"],
        destination_station=p["destination_station"],
        departure_at=datetime.fromisoformat(p["departure_at"]),
        arrival_at=datetime.fromisoformat(p["arrival_at"]),
        duration_minutes=p["duration_minutes"],
        transfers=p["transfers"],
        amenities=p.get("amenities", []),
        available_seats=p.get("available_seats"),
        price=item.price,
        currency=item.currency,
        refundable=p.get("refundable", False),
    )


@router.post("", response_model=SearchOut)
def create_search(payload: SearchCreate, db: Session = Depends(get_db)) -> SearchOut:
    if payload.return_date and payload.return_date < payload.departure_date:
        raise HTTPException(status_code=422, detail="Return date cannot be before departure date")

    record = Search(
        origin_query=payload.origin,
        destination_query=payload.destination,
        departure_date=payload.departure_date,
        return_date=payload.return_date,
        adults=payload.passengers.adults,
        children=payload.passengers.children,
        currency=payload.currency.upper(),
    )
    db.add(record)
    db.flush()

    provider = get_transport_provider()
    try:
        journeys = provider.search(
            ProviderSearchRequest(
                origin=payload.origin,
                destination=payload.destination,
                departure_date=payload.departure_date,
                adults=payload.passengers.adults,
                children=payload.passengers.children,
                currency=payload.currency.upper(),
            )
        )
    except RuntimeError as exc:
        db.rollback()
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    outputs: list[JourneyOut] = []
    for j in journeys:
        snapshot = {
            **j.raw,
            "operator_name": j.operator_name,
            "operator_logo_url": j.operator_logo_url,
            "origin_name": j.origin_name,
            "origin_station": j.origin_station,
            "destination_name": j.destination_name,
            "destination_station": j.destination_station,
            "departure_at": j.departure_at.isoformat(),
            "arrival_at": j.arrival_at.isoformat(),
            "duration_minutes": j.duration_minutes,
            "transfers": j.transfers,
            "amenities": j.amenities,
            "available_seats": j.available_seats,
            "refundable": j.refundable,
            "price": str(j.price),
            "currency": j.currency,
        }
        cache = JourneyCache(
            search_id=record.id,
            provider=provider.name,
            provider_journey_id=j.provider_journey_id,
            payload=snapshot,
            price=j.price,
            currency=j.currency,
            expires_at=datetime.now(timezone.utc) + timedelta(minutes=5),
        )
        db.add(cache)
        db.flush()
        outputs.append(cache_to_out(cache))

    db.commit()
    return SearchOut(search_id=record.id, journeys=outputs)


@router.get("/{search_id}", response_model=SearchOut)
def get_search(search_id: str, db: Session = Depends(get_db)) -> SearchOut:
    record = db.get(Search, search_id)
    if not record:
        raise HTTPException(status_code=404, detail="Search not found")
    journeys = db.scalars(select(JourneyCache).where(JourneyCache.search_id == search_id)).all()
    return SearchOut(search_id=record.id, journeys=[cache_to_out(item) for item in journeys])
