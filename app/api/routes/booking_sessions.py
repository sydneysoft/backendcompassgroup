from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.models import BookingSession, JourneyCache
from app.schemas.booking import BookingSessionCreate, BookingSessionOut
from app.services.providers.factory import get_transport_provider

router = APIRouter(prefix="/booking-sessions", tags=["booking-sessions"])


@router.post("", response_model=BookingSessionOut)
def create_booking_session(payload: BookingSessionCreate, db: Session = Depends(get_db)) -> BookingSessionOut:
    journey = db.get(JourneyCache, payload.journey_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    provider = get_transport_provider()
    try:
        quote = provider.reprice(journey.payload)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    if not quote.available:
        raise HTTPException(status_code=409, detail="Journey is no longer available")

    changed = quote.amount != journey.price or quote.currency != journey.currency
    session = BookingSession(
        journey_cache_id=journey.id,
        quoted_amount=quote.amount,
        quoted_currency=quote.currency,
        provider_quote_payload=quote.payload,
        expires_at=datetime.now(timezone.utc) + timedelta(minutes=15),
    )
    db.add(session)
    db.commit()
    db.refresh(session)
    return BookingSessionOut(
        id=session.id,
        status=session.status,
        amount=session.quoted_amount,
        currency=session.quoted_currency,
        expires_at=session.expires_at,
        price_changed=changed,
    )
