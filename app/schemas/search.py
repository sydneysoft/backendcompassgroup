from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field


class PassengerCounts(BaseModel):
    adults: int = Field(default=1, ge=1, le=9)
    children: int = Field(default=0, ge=0, le=9)


class SearchCreate(BaseModel):
    origin: str = Field(min_length=2, max_length=160)
    destination: str = Field(min_length=2, max_length=160)
    departure_date: date
    return_date: date | None = None
    passengers: PassengerCounts = PassengerCounts()
    currency: str = Field(default="EUR", min_length=3, max_length=3)


class JourneyOut(BaseModel):
    id: str
    provider: str
    provider_journey_id: str
    operator_name: str
    operator_logo_url: str | None = None
    origin_name: str
    origin_station: str
    destination_name: str
    destination_station: str
    departure_at: datetime
    arrival_at: datetime
    duration_minutes: int
    transfers: int
    amenities: list[str]
    available_seats: int | None = None
    price: Decimal
    currency: str
    refundable: bool


class SearchOut(BaseModel):
    search_id: str
    journeys: list[JourneyOut]
