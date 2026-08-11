from __future__ import annotations

from typing import Any

from app.core.config import get_settings
from app.services.providers.base import ProviderBooking, ProviderJourney, ProviderQuote, ProviderSearchRequest, TransportProvider


class DistribusionProvider(TransportProvider):
    """Distribusion adapter boundary.

    The public project intentionally does not guess private/partner endpoint paths or payload
    schemas. Once retailer credentials and partner documentation are available, implement the
    four methods below without changing the rest of the application.
    """

    name = "distribusion"

    def __init__(self) -> None:
        settings = get_settings()
        self.base_url = settings.distribusion_base_url
        self.api_key = settings.distribusion_api_key

    def _not_configured(self) -> RuntimeError:
        return RuntimeError(
            "Distribusion adapter requires retailer credentials and the partner API schema. "
            "Set DISTRIBUSION_BASE_URL/DISTRIBUSION_API_KEY and map the partner endpoints in app/services/providers/distribusion.py."
        )

    def search(self, request: ProviderSearchRequest) -> list[ProviderJourney]:
        raise self._not_configured()

    def reprice(self, journey_payload: dict[str, Any]) -> ProviderQuote:
        raise self._not_configured()

    def create_booking(self, journey_payload: dict[str, Any], passengers: list[dict[str, Any]], contact: dict[str, str]) -> ProviderBooking:
        raise self._not_configured()

    def cancel_booking(self, provider_booking_id: str) -> bool:
        raise self._not_configured()
