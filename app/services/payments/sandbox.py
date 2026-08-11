from __future__ import annotations

from decimal import Decimal
from uuid import uuid4

from app.models.enums import PaymentMethod
from app.services.payments.base import GatewayIntent, PaymentGateway


class SandboxPaymentGateway(PaymentGateway):
    name = "sandbox"

    def create_intent(
        self,
        *,
        amount: Decimal,
        currency: str,
        method: PaymentMethod,
        idempotency_key: str,
        return_url: str | None,
    ) -> GatewayIntent:
        pid = f"sandbox_{uuid4().hex}"
        action = {
            "type": "sandbox_confirmation",
            "message": "Development only: call the dev success endpoint to simulate the selected payment method.",
        }
        return GatewayIntent(
            gateway_payment_id=pid,
            status="requires_action",
            action=action,
            raw={"method": method.value, "amount": str(amount), "currency": currency, "return_url": return_url},
        )

    def refund(self, gateway_payment_id: str, amount: Decimal, currency: str) -> str:
        return f"refund_{uuid4().hex}"
