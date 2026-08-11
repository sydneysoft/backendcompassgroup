from enum import StrEnum


class BookingStatus(StrEnum):
    PENDING_PAYMENT = "pending_payment"
    PAYMENT_AUTHORIZED = "payment_authorized"
    CONFIRMED = "confirmed"
    TICKETED = "ticketed"
    CANCELLED = "cancelled"
    FAILED = "failed"
    REFUND_PENDING = "refund_pending"
    REFUNDED = "refunded"


class BookingSessionStatus(StrEnum):
    ACTIVE = "active"
    CONSUMED = "consumed"
    EXPIRED = "expired"


class PaymentMethod(StrEnum):
    VISA = "visa"
    MASTERCARD = "mastercard"
    APPLE_PAY = "apple_pay"
    GOOGLE_PAY = "google_pay"
    PAYPAL = "paypal"


class PaymentStatus(StrEnum):
    PENDING = "pending"
    REQUIRES_ACTION = "requires_action"
    AUTHORIZED = "authorized"
    PAID = "paid"
    FAILED = "failed"
    CANCELLED = "cancelled"
    REFUNDED = "refunded"
    PARTIALLY_REFUNDED = "partially_refunded"


class RefundStatus(StrEnum):
    PENDING = "pending"
    SUCCEEDED = "succeeded"
    FAILED = "failed"
