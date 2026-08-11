from datetime import datetime, timezone
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.db import get_db
from app.models import Booking, BookingSession, JourneyCache, Passenger
from app.models.enums import BookingSessionStatus
from app.schemas.booking import BookingCreate, BookingOut, CancelBookingRequest, TicketOut
from app.services.audit import audit
from app.services.booking import cancel_and_refund

router = APIRouter(prefix="/bookings", tags=["bookings"])


def to_out(booking: Booking) -> BookingOut:
    return BookingOut(
        id=booking.id,
        reference=booking.reference,
        status=booking.status,
        amount=booking.total_amount,
        currency=booking.currency,
        contact_email=booking.contact_email,
        contact_phone=booking.contact_phone,
        provider_booking_id=booking.provider_booking_id,
        tickets=[TicketOut(id=t.id, ticket_number=t.ticket_number, qr_text=t.qr_text, pdf_url=t.pdf_url) for t in booking.tickets],
    )


def load_booking(db: Session, booking_id: str) -> Booking | None:
    return db.scalar(
        select(Booking)
        .options(selectinload(Booking.passengers), selectinload(Booking.tickets), selectinload(Booking.payments))
        .where(Booking.id == booking_id)
    )


@router.post("", response_model=BookingOut)
def create_booking(payload: BookingCreate, db: Session = Depends(get_db)) -> BookingOut:
    session = db.get(BookingSession, payload.booking_session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Booking session not found")
    now = datetime.now(timezone.utc)
    expires_at = session.expires_at
    if expires_at.tzinfo is None:
        expires_at = expires_at.replace(tzinfo=timezone.utc)
    if session.status != BookingSessionStatus.ACTIVE.value or expires_at <= now:
        raise HTTPException(status_code=409, detail="Booking session is expired or already used")
    if session.booking:
        existing = load_booking(db, session.booking.id)
        return to_out(existing)

    journey = db.get(JourneyCache, session.journey_cache_id)
    if not journey:
        raise HTTPException(status_code=404, detail="Journey not found")

    booking_id = str(uuid4())
    reference = f"BT{booking_id.replace('-', '')[:10].upper()}"
    booking = Booking(
        id=booking_id,
        reference=reference,
        booking_session_id=session.id,
        provider=journey.provider,
        total_amount=session.quoted_amount,
        currency=session.quoted_currency,
        contact_email=str(payload.contact_email).lower(),
        contact_phone=payload.contact_phone,
    )
    db.add(booking)
    db.flush()

    for passenger in payload.passengers:
        db.add(
            Passenger(
                booking_id=booking.id,
                first_name=passenger.first_name,
                last_name=passenger.last_name,
                passenger_type=passenger.passenger_type,
                date_of_birth=passenger.date_of_birth,
                nationality=passenger.nationality,
                document_type=passenger.document_type,
                document_number=passenger.document_number,
            )
        )

    audit(db, event_type="booking.created", entity_type="booking", entity_id=booking.id)
    db.commit()
    loaded = load_booking(db, booking.id)
    return to_out(loaded)


@router.get("/{reference}", response_model=BookingOut)
def get_booking(reference: str, email: str, db: Session = Depends(get_db)) -> BookingOut:
    booking = db.scalar(
        select(Booking)
        .options(selectinload(Booking.tickets), selectinload(Booking.passengers), selectinload(Booking.payments))
        .where(Booking.reference == reference, Booking.contact_email == email.lower())
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    return to_out(booking)


@router.post("/{reference}/cancel", response_model=BookingOut)
def cancel_booking(reference: str, payload: CancelBookingRequest, db: Session = Depends(get_db)) -> BookingOut:
    booking = db.scalar(
        select(Booking)
        .options(selectinload(Booking.tickets), selectinload(Booking.passengers), selectinload(Booking.payments))
        .where(Booking.reference == reference, Booking.contact_email == str(payload.email).lower())
    )
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    try:
        booking = cancel_and_refund(db, booking)
    except ValueError as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    loaded = load_booking(db, booking.id)
    return to_out(loaded)
