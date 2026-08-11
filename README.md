# Bus Platform Backend v2

Backend for an API-driven bus/ground-transport booking website.

## What is implemented

- FastAPI REST API with OpenAPI/Swagger docs.
- PostgreSQL production database configuration.
- SQLAlchemy 2.x data model + Alembic migration.
- Transport-provider abstraction.
- Fully working mock transport API for development and end-to-end testing.
- Distribusion adapter boundary ready for partner endpoint mapping once retailer credentials/docs are supplied.
- Search persistence and short-lived journey cache.
- Repricing / availability check before checkout.
- Booking sessions with expiry.
- Passenger + contact storage.
- Booking state machine.
- Payment records + idempotency.
- Separate checkout methods: Visa, Mastercard, Apple Pay, Google Pay, PayPal.
- Sandbox payment simulator for local development only.
- Ticket record creation after successful booking.
- Cancellation + sandbox refund flow.
- Basic admin summary protected by an admin key.
- Audit log table.
- CORS configuration.
- Automated integration tests.

## Important production boundaries

### Distribusion

The project does **not** invent Distribusion partner endpoint paths or payloads. Their retailer integration requires commercial credentials/partner documentation. All provider-dependent code is isolated in:

`app/services/providers/distribusion.py`

When credentials and the retailer schema are available, implement `search`, `reprice`, `create_booking`, and `cancel_booking` there. The rest of the API does not need to change.

### Payments

The backend exposes the agreed payment choices separately:

- Visa
- Mastercard
- Apple Pay
- Google Pay
- PayPal

At present they run through a sandbox gateway so the full booking flow can be developed and tested without charging money. A production PSP/merchant account must be selected and credentials added before launch. Raw card details must never be sent to or stored by this backend.

## Local start with PostgreSQL

```bash
cp .env.example .env
docker compose up -d db
python -m venv .venv
source .venv/bin/activate
pip install -e '.[dev]'
alembic upgrade head
uvicorn app.main:app --reload
```

Open:

- API: `http://localhost:8000`
- Swagger: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Main API flow

1. `POST /api/v1/searches`
2. `POST /api/v1/booking-sessions`
3. `POST /api/v1/bookings`
4. `GET /api/v1/payments/methods`
5. `POST /api/v1/payments`
6. Development only: `POST /api/v1/payments/{payment_id}/dev-succeed`
7. `GET /api/v1/bookings/{reference}?email=...`
8. `POST /api/v1/bookings/{reference}/cancel`

## Run tests

```bash
pytest
```

Tests use an in-memory SQLite database so they do not require Docker/PostgreSQL.

## Database tables

- searches
- journey_cache
- booking_sessions
- bookings
- passengers
- payments
- tickets
- refunds
- promo_codes
- audit_logs

## Next production work

1. Map real Distribusion retailer API operations after onboarding.
2. Add a production payment gateway and its webhooks for Visa/Mastercard, Apple Pay, Google Pay, and PayPal.
3. Add provider/payment webhook processing.
4. Add email delivery for confirmations and tickets.
5. Add richer refund/change rules from carrier fare conditions.
6. Replace the simple admin key with staff accounts/RBAC before production.
