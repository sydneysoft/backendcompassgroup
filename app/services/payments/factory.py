from app.core.config import get_settings
from app.services.payments.base import PaymentGateway
from app.services.payments.sandbox import SandboxPaymentGateway


def get_payment_gateway() -> PaymentGateway:
    settings = get_settings()
    if settings.payments_mode == "production":
        raise RuntimeError(
            "Production payment gateway is not configured. Keep PAYMENTS_MODE=sandbox until merchant credentials are added."
        )
    return SandboxPaymentGateway()
