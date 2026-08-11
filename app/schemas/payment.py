from decimal import Decimal

from pydantic import BaseModel, Field

from app.models.enums import PaymentMethod


class PaymentMethodOut(BaseModel):
    id: PaymentMethod
    label: str
    kind: str
    supported_networks: list[str] = []


class PaymentCreate(BaseModel):
    booking_id: str
    method: PaymentMethod
    idempotency_key: str = Field(min_length=8, max_length=120)
    return_url: str | None = None


class PaymentAction(BaseModel):
    type: str
    url: str | None = None
    client_secret: str | None = None
    message: str | None = None


class PaymentOut(BaseModel):
    id: str
    booking_id: str
    method: PaymentMethod
    status: str
    amount: Decimal
    currency: str
    action: PaymentAction | None = None
