from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.core.config import get_settings
from app.core.db import get_db
from app.models import Booking, Payment
from app.models.enums import PaymentMethod, PaymentStatus
from app.schemas.payment import PaymentAction, PaymentCreate, PaymentMethodOut, PaymentOut
from app.services.audit import audit
from app.services.booking import finalize_paid_booking
from app.services.payments.factory import get_payment_gateway

router = APIRouter(prefix="/payments", tags=["payments"])


METHODS = [
    PaymentMethodOut(id=PaymentMethod.VISA, label="Visa", kind="card", supported_networks=["visa"]),
    PaymentMethodOut(id=PaymentMethod.MASTERCARD, label="Mastercard", kind="card", supported_networks=["mastercard"]),
    PaymentMethodOut(id=PaymentMethod.APPLE_PAY, label="Apple Pay", kind="wallet", supported_networks=["visa", "mastercard"]),
    PaymentMethodOut(id=PaymentMethod.GOOGLE_PAY, label="Google Pay", kind="wallet", supported_networks=["visa", "mastercard"]),
    PaymentMethodOut(id=PaymentMethod.PAYPAL, label="PayPal", kind="wallet", supported_networks=[]),
]


@router.get("/methods", response_model=list[PaymentMethodOut])
def payment_methods() -> list[PaymentMethodOut]:
    return METHODS


@router.post("", response_model=PaymentOut)
def create_payment(payload: PaymentCreate, db: Session = Depends(get_db)) -> PaymentOut:
    existing = db.scalar(select(Payment).where(Payment.idempotency_key == payload.idempotency_key))
    if existing:
        return PaymentOut(
            id=existing.id,
            booking_id=existing.booking_id,
            method=PaymentMethod(existing.method),
            status=existing.status,
            amount=existing.amount,
            currency=existing.currency,
            action=PaymentAction(**existing.gateway_payload["action"]) if existing.gateway_payload.get("action") else None,
        )

    booking = db.get(Booking, payload.booking_id)
    if not booking:
        raise HTTPException(status_code=404, detail="Booking not found")
    if booking.status not in {"pending_payment", "payment_authorized"}:
        raise HTTPException(status_code=409, detail="Booking is not payable")

    gateway = get_payment_gateway()
    try:
        intent = gateway.create_intent(
            amount=booking.total_amount,
            currency=booking.currency,
            method=payload.method,
            idempotency_key=payload.idempotency_key,
            return_url=payload.return_url,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc

    payment = Payment(
        booking_id=booking.id,
        method=payload.method.value,
        gateway=gateway.name,
        gateway_payment_id=intent.gateway_payment_id,
        idempotency_key=payload.idempotency_key,
        status=intent.status,
        amount=booking.total_amount,
        currency=booking.currency,
        gateway_payload={"raw": intent.raw, "action": intent.action},
    )
    db.add(payment)
    db.flush()
    audit(db, event_type="payment.created", entity_type="payment", entity_id=payment.id, payload={"method": payload.method.value})
    db.commit()
    db.refresh(payment)
    return PaymentOut(
        id=payment.id,
        booking_id=payment.booking_id,
        method=payload.method,
        status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        action=PaymentAction(**intent.action) if intent.action else None,
    )


@router.post("/{payment_id}/dev-succeed", response_model=PaymentOut)
def dev_succeed(payment_id: str, db: Session = Depends(get_db)) -> PaymentOut:
    if get_settings().app_env == "production":
        raise HTTPException(status_code=404, detail="Not found")
    payment = db.scalar(select(Payment).options(selectinload(Payment.booking)).where(Payment.id == payment_id))
    if not payment:
        raise HTTPException(status_code=404, detail="Payment not found")
    if payment.status == PaymentStatus.PAID.value:
        return PaymentOut(
            id=payment.id,
            booking_id=payment.booking_id,
            method=PaymentMethod(payment.method),
            status=payment.status,
            amount=payment.amount,
            currency=payment.currency,
            action=None,
        )
    try:
        finalize_paid_booking(db, payment)
    except (ValueError, RuntimeError) as exc:
        raise HTTPException(status_code=409, detail=str(exc)) from exc
    db.refresh(payment)
    return PaymentOut(
        id=payment.id,
        booking_id=payment.booking_id,
        method=PaymentMethod(payment.method),
        status=payment.status,
        amount=payment.amount,
        currency=payment.currency,
        action=None,
    )
