from app.core.config import get_settings
from app.services.providers.base import TransportProvider
from app.services.providers.distribusion import DistribusionProvider
from app.services.providers.mock import MockTransportProvider


def get_transport_provider() -> TransportProvider:
    settings = get_settings()
    if settings.transport_provider == "distribusion":
        return DistribusionProvider()
    return MockTransportProvider()
