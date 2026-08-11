from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, EmailStr, Field


class BookingSessionCreate(BaseModel):
    journey_id: str


class BookingSessionOut(BaseModel):
    id: str
    status: str
    amount: Decimal
    currency: str
    expires_at: datetime
    price_changed: bool = False


class PassengerCreate(BaseModel):
    first_name: str = Field(min_length=1, max_length=120)
    last_name: str = Field(min_length=1, max_length=120)
    passenger_type: str = "adult"
    date_of_birth: date | None = None
    nationality: str | None = Field(default=None, min_length=2, max_length=3)
    document_type: str | None = None
    document_number: str | None = None


class BookingCreate(BaseModel):
    booking_session_id: str
    contact_email: EmailStr
    contact_phone: str = Field(min_length=6, max_length=40)
    passengers: list[PassengerCreate] = Field(min_length=1, max_length=9)


class TicketOut(BaseModel):
    id: str
    ticket_number: str | None
    qr_text: str | None
    pdf_url: str | None


class BookingOut(BaseModel):
    id: str
    reference: str
    status: str
    amount: Decimal
    currency: str
    contact_email: EmailStr
    contact_phone: str
    provider_booking_id: str | None
    tickets: list[TicketOut] = []


class BookingLookup(BaseModel):
    reference: str
    email: EmailStr


class CancelBookingRequest(BaseModel):
    email: EmailStr
