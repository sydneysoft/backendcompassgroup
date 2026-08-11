from __future__ import annotations

from datetime import datetime, time, timedelta, timezone
from decimal import Decimal
from hashlib import sha1
from typing import Any

from app.services.providers.base import (
    ProviderBooking,
    ProviderJourney,
    ProviderQuote,
    ProviderSearchRequest,
    ProviderTicket,
    TransportProvider,
)


class MockTransportProvider(TransportProvider):
    name = "mock"

    locations = [
        {"id": "warsaw", "name": "Warsaw", "country": "Poland", "type": "city"},
        {"id": "kyiv", "name": "Kyiv", "country": "Ukraine", "type": "city"},
        {"id": "lviv", "name": "Lviv", "country": "Ukraine", "type": "city"},
        {"id": "krakow", "name": "Kraków", "country": "Poland", "type": "city"},
        {"id": "prague", "name": "Prague", "country": "Czechia", "type": "city"},
        {"id": "berlin", "name": "Berlin", "country": "Germany", "type": "city"},
        {"id": "munich", "name": "Munich", "country": "Germany", "type": "city"},
        {"id": "london", "name": "London", "country": "United Kingdom", "type": "city"},
    ]

    def search_locations(self, query: str) -> list[dict[str, str]]:
        q = query.casefold().strip()
        return [item for item in self.locations if q in item["name"].casefold() or q in item["country"].casefold()][:8]

    def search(self, request: ProviderSearchRequest) -> list[ProviderJourney]:
        base = datetime.combine(request.departure_date, time(3, 10), tzinfo=timezone.utc)
        seed = int(sha1(f"{request.origin}|{request.destination}|{request.departure_date}".encode()).hexdigest()[:6], 16)
        operators = ["Golden Plus Trans", "EuroBus", "Intercity Coach"]
        journeys: list[ProviderJourney] = []
        for index, operator in enumerate(operators):
            depart = base + timedelta(hours=index * 4 + (seed % 2))
            duration = 1010 - index * 65 + (seed % 30)
            arrive = depart + timedelta(minutes=duration)
            price = Decimal("27.50") + Decimal(index * 4) + Decimal(seed % 7) / Decimal("10")
            jid = f"mock_{request.departure_date}_{index}_{seed}"
            raw = {
                "id": jid,
                "operator": operator,
                "origin": request.origin,
                "destination": request.destination,
                "departure_at": depart.isoformat(),
                "arrival_at": arrive.isoformat(),
                "duration_minutes": duration,
                "price": str(price),
                "currency": request.currency,
                "available_seats": max(1, 12 - index * 3),
                "amenities": ["wifi", "power", "air_conditioning"] if index != 2 else ["power"],
                "refundable": index == 1,
            }
            journeys.append(
                ProviderJourney(
                    provider_journey_id=jid,
                    operator_name=operator,
                    operator_logo_url=None,
                    origin_name=request.origin,
                    origin_station=f"{request.origin} Central Bus Station",
                    destination_name=request.destination,
                    destination_station=f"{request.destination} Central Bus Station",
                    departure_at=depart,
                    arrival_at=arrive,
                    duration_minutes=duration,
                    transfers=0 if index < 2 else 1,
                    amenities=raw["amenities"],
                    available_seats=raw["available_seats"],
                    price=price,
                    currency=request.currency,
                    refundable=raw["refundable"],
                    raw=raw,
                )
            )
        return journeys

    def reprice(self, journey_payload: dict[str, Any]) -> ProviderQuote:
        return ProviderQuote(
            amount=Decimal(str(journey_payload["price"])),
            currency=journey_payload["currency"],
            available=int(journey_payload.get("available_seats", 1)) > 0,
            payload={"checked": True, "available_seats": journey_payload.get("available_seats")},
        )

    def create_booking(self, journey_payload: dict[str, Any], passengers: list[dict[str, Any]], contact: dict[str, str]) -> ProviderBooking:
        token = sha1(f"{journey_payload['id']}|{contact['email']}|{len(passengers)}".encode()).hexdigest()[:12].upper()
        ticket = ProviderTicket(
            provider_ticket_id=f"T-{token}",
            ticket_number=f"MOCK-{token}",
            qr_text=f"BUSBOOKING:{token}",
            pdf_url=None,
        )
        return ProviderBooking(provider_booking_id=f"B-{token}", status="ticketed", ticket=ticket)

    def cancel_booking(self, provider_booking_id: str) -> bool:
        return True
