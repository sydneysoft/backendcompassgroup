from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from decimal import Decimal

from app.models.enums import PaymentMethod


@dataclass(slots=True)
class GatewayIntent:
    gateway_payment_id: str
    status: str
    action: dict | None
    raw: dict


class PaymentGateway(ABC):
    name: str

    @abstractmethod
    def create_intent(
        self,
        *,
        amount: Decimal,
        currency: str,
        method: PaymentMethod,
        idempotency_key: str,
        return_url: str | None,
    ) -> GatewayIntent:
        raise NotImplementedError

    @abstractmethod
    def refund(self, gateway_payment_id: str, amount: Decimal, currency: str) -> str:
        raise NotImplementedError
