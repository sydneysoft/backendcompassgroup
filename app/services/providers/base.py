from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import Any


@dataclass(slots=True)
class ProviderSearchRequest:
    origin: str
    destination: str
    departure_date: date
    adults: int
    children: int
    currency: str


@dataclass(slots=True)
class ProviderJourney:
    provider_journey_id: str
    operator_name: str
    operator_logo_url: str | None
    origin_name: str
    origin_station: str
    destination_name: str
    destination_station: str
    departure_at: datetime
    arrival_at: datetime
    duration_minutes: int
    transfers: int
    amenities: list[str]
    available_seats: int | None
    price: Decimal
    currency: str
    refundable: bool
    raw: dict[str, Any]


@dataclass(slots=True)
class ProviderQuote:
    amount: Decimal
    currency: str
    available: bool
    payload: dict[str, Any]


@dataclass(slots=True)
class ProviderTicket:
    provider_ticket_id: str
    ticket_number: str
    qr_text: str | None
    pdf_url: str | None


@dataclass(slots=True)
class ProviderBooking:
    provider_booking_id: str
    status: str
    ticket: ProviderTicket | None


class TransportProvider(ABC):
    name: str

    @abstractmethod
    def search(self, request: ProviderSearchRequest) -> list[ProviderJourney]:
        raise NotImplementedError

    @abstractmethod
    def reprice(self, journey_payload: dict[str, Any]) -> ProviderQuote:
        raise NotImplementedError

    @abstractmethod
    def create_booking(self, journey_payload: dict[str, Any], passengers: list[dict[str, Any]], contact: dict[str, str]) -> ProviderBooking:
        raise NotImplementedError

    @abstractmethod
    def cancel_booking(self, provider_booking_id: str) -> bool:
        raise NotImplementedError

    def search_locations(self, query: str) -> list[dict[str, str]]:
        return []
