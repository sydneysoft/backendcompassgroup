from __future__ import annotations

from datetime import date, datetime, timezone
from decimal import Decimal
from typing import Any
from uuid import uuid4

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, Index, JSON, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base
from app.models.enums import BookingSessionStatus, BookingStatus, PaymentStatus, RefundStatus


def new_id() -> str:
    return str(uuid4())


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class Search(Base):
    __tablename__ = "searches"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    origin_query: Mapped[str] = mapped_column(String(160))
    destination_query: Mapped[str] = mapped_column(String(160))
    departure_date: Mapped[date] = mapped_column(Date)
    return_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    adults: Mapped[int] = mapped_column(default=1)
    children: Mapped[int] = mapped_column(default=0)
    currency: Mapped[str] = mapped_column(String(3), default="EUR")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    journeys: Mapped[list[JourneyCache]] = relationship(back_populates="search", cascade="all, delete-orphan")


class JourneyCache(Base):
    __tablename__ = "journey_cache"
    __table_args__ = (
        Index("ix_journey_cache_search_id", "search_id"),
        Index("ix_journey_cache_provider_journey", "provider", "provider_journey_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    search_id: Mapped[str] = mapped_column(ForeignKey("searches.id", ondelete="CASCADE"))
    provider: Mapped[str] = mapped_column(String(40))
    provider_journey_id: Mapped[str] = mapped_column(String(160))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON)
    price: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    search: Mapped[Search] = relationship(back_populates="journeys")
    booking_sessions: Mapped[list[BookingSession]] = relationship(back_populates="journey")


class BookingSession(Base):
    __tablename__ = "booking_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    journey_cache_id: Mapped[str] = mapped_column(ForeignKey("journey_cache.id"))
    status: Mapped[str] = mapped_column(String(32), default=BookingSessionStatus.ACTIVE.value)
    quoted_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    quoted_currency: Mapped[str] = mapped_column(String(3))
    provider_quote_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    journey: Mapped[JourneyCache] = relationship(back_populates="booking_sessions")
    booking: Mapped[Booking | None] = relationship(back_populates="session", uselist=False)


class Booking(Base):
    __tablename__ = "bookings"
    __table_args__ = (
        UniqueConstraint("reference", name="uq_bookings_reference"),
        Index("ix_bookings_contact_email", "contact_email"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    reference: Mapped[str] = mapped_column(String(20), unique=True)
    booking_session_id: Mapped[str] = mapped_column(ForeignKey("booking_sessions.id"), unique=True)
    provider: Mapped[str] = mapped_column(String(40))
    provider_booking_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    status: Mapped[str] = mapped_column(String(32), default=BookingStatus.PENDING_PAYMENT.value)
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    contact_email: Mapped[str] = mapped_column(String(320))
    contact_phone: Mapped[str] = mapped_column(String(40))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    session: Mapped[BookingSession] = relationship(back_populates="booking")
    passengers: Mapped[list[Passenger]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    payments: Mapped[list[Payment]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    tickets: Mapped[list[Ticket]] = relationship(back_populates="booking", cascade="all, delete-orphan")
    refunds: Mapped[list[Refund]] = relationship(back_populates="booking", cascade="all, delete-orphan")


class Passenger(Base):
    __tablename__ = "passengers"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    first_name: Mapped[str] = mapped_column(String(120))
    last_name: Mapped[str] = mapped_column(String(120))
    passenger_type: Mapped[str] = mapped_column(String(30), default="adult")
    date_of_birth: Mapped[date | None] = mapped_column(Date, nullable=True)
    nationality: Mapped[str | None] = mapped_column(String(3), nullable=True)
    document_type: Mapped[str | None] = mapped_column(String(30), nullable=True)
    document_number: Mapped[str | None] = mapped_column(String(80), nullable=True)

    booking: Mapped[Booking] = relationship(back_populates="passengers")


class Payment(Base):
    __tablename__ = "payments"
    __table_args__ = (
        UniqueConstraint("idempotency_key", name="uq_payments_idempotency_key"),
        Index("ix_payments_booking_id", "booking_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    method: Mapped[str] = mapped_column(String(30))
    gateway: Mapped[str] = mapped_column(String(40), default="sandbox")
    gateway_payment_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    idempotency_key: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(32), default=PaymentStatus.PENDING.value)
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    gateway_payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, onupdate=utcnow)

    booking: Mapped[Booking] = relationship(back_populates="payments")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    provider_ticket_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    ticket_number: Mapped[str | None] = mapped_column(String(120), nullable=True)
    qr_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    pdf_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    booking: Mapped[Booking] = relationship(back_populates="tickets")


class Refund(Base):
    __tablename__ = "refunds"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    booking_id: Mapped[str] = mapped_column(ForeignKey("bookings.id", ondelete="CASCADE"))
    payment_id: Mapped[str] = mapped_column(ForeignKey("payments.id"))
    amount: Mapped[Decimal] = mapped_column(Numeric(12, 2))
    currency: Mapped[str] = mapped_column(String(3))
    status: Mapped[str] = mapped_column(String(32), default=RefundStatus.PENDING.value)
    gateway_refund_id: Mapped[str | None] = mapped_column(String(160), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

    booking: Mapped[Booking] = relationship(back_populates="refunds")


class PromoCode(Base):
    __tablename__ = "promo_codes"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    code: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    active: Mapped[bool] = mapped_column(Boolean, default=True)
    kind: Mapped[str] = mapped_column(String(20), default="percentage")
    value: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    max_uses: Mapped[int | None] = mapped_column(nullable=True)
    uses: Mapped[int] = mapped_column(default=0)
    starts_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    ends_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class AuditLog(Base):
    __tablename__ = "audit_logs"
    __table_args__ = (Index("ix_audit_entity", "entity_type", "entity_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    event_type: Mapped[str] = mapped_column(String(80))
    entity_type: Mapped[str] = mapped_column(String(80))
    entity_id: Mapped[str] = mapped_column(String(80))
    payload: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)
