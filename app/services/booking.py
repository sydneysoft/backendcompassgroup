from __future__ import annotations

from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Booking, BookingSession, JourneyCache, Passenger, Payment, Refund, Ticket
from app.models.enums import BookingSessionStatus, BookingStatus, PaymentStatus, RefundStatus
from app.services.audit import audit
from app.services.payments.factory import get_payment_gateway
from app.services.providers.factory import get_transport_provider


def booking_reference(booking_id: str) -> str:
    return f"BT{booking_id.replace('-', '')[:10].upper()}"


def finalize_paid_booking(db: Session, payment: Payment) -> Booking:
    booking = db.get(Booking, payment.booking_id)
    if not booking:
        raise ValueError("Booking not found")
    if booking.status == BookingStatus.TICKETED.value:
        return booking

    session = db.get(BookingSession, booking.booking_session_id)
    journey = db.get(JourneyCache, session.journey_cache_id) if session else None
    if not session or not journey:
        raise ValueError("Booking session or journey not found")

    provider = get_transport_provider()
    passenger_payloads = [
        {
            "first_name": p.first_name,
            "last_name": p.last_name,
            "passenger_type": p.passenger_type,
            "date_of_birth": p.date_of_birth.isoformat() if p.date_of_birth else None,
            "nationality": p.nationality,
            "document_type": p.document_type,
            "document_number": p.document_number,
        }
        for p in booking.passengers
    ]
    result = provider.create_booking(
        journey.payload,
        passenger_payloads,
        {"email": booking.contact_email, "phone": booking.contact_phone},
    )

    payment.status = PaymentStatus.PAID.value
    booking.provider_booking_id = result.provider_booking_id
    booking.status = BookingStatus.TICKETED.value if result.ticket else BookingStatus.CONFIRMED.value
    session.status = BookingSessionStatus.CONSUMED.value

    if result.ticket:
        db.add(
            Ticket(
                booking_id=booking.id,
                provider_ticket_id=result.ticket.provider_ticket_id,
                ticket_number=result.ticket.ticket_number,
                qr_text=result.ticket.qr_text,
                pdf_url=result.ticket.pdf_url,
            )
        )

    audit(db, event_type="booking.ticketed", entity_type="booking", entity_id=booking.id, payload={"provider_booking_id": result.provider_booking_id})
    db.commit()
    db.refresh(booking)
    return booking


def cancel_and_refund(db: Session, booking: Booking) -> Booking:
    if booking.status in {BookingStatus.CANCELLED.value, BookingStatus.REFUNDED.value}:
        return booking
    if not booking.provider_booking_id:
        raise ValueError("Booking has not been confirmed with the transport provider")

    provider = get_transport_provider()
    if not provider.cancel_booking(booking.provider_booking_id):
        raise ValueError("Transport provider rejected cancellation")

    payment = db.scalar(
        select(Payment).where(Payment.booking_id == booking.id, Payment.status == PaymentStatus.PAID.value).order_by(Payment.created_at.desc())
    )
    booking.status = BookingStatus.CANCELLED.value

    if payment:
        gateway = get_payment_gateway()
        refund_id = gateway.refund(payment.gateway_payment_id or payment.id, Decimal(payment.amount), payment.currency)
        db.add(
            Refund(
                booking_id=booking.id,
                payment_id=payment.id,
                amount=payment.amount,
                currency=payment.currency,
                status=RefundStatus.SUCCEEDED.value,
                gateway_refund_id=refund_id,
            )
        )
        payment.status = PaymentStatus.REFUNDED.value
        booking.status = BookingStatus.REFUNDED.value

    audit(db, event_type="booking.cancelled", entity_type="booking", entity_id=booking.id)
    db.commit()
    db.refresh(booking)
    return booking
