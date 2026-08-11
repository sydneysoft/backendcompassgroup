from datetime import date, timedelta


def test_full_search_payment_ticket_cancel_flow(client):
    travel_date = (date.today() + timedelta(days=10)).isoformat()

    search = client.post(
        "/api/v1/searches",
        json={
            "origin": "Warsaw",
            "destination": "Kyiv",
            "departure_date": travel_date,
            "passengers": {"adults": 1, "children": 0},
            "currency": "EUR",
        },
    )
    assert search.status_code == 200, search.text
    search_body = search.json()
    assert len(search_body["journeys"]) == 3
    journey_id = search_body["journeys"][0]["id"]

    session = client.post("/api/v1/booking-sessions", json={"journey_id": journey_id})
    assert session.status_code == 200, session.text
    session_id = session.json()["id"]

    booking = client.post(
        "/api/v1/bookings",
        json={
            "booking_session_id": session_id,
            "contact_email": "buyer@example.com",
            "contact_phone": "+447700900123",
            "passengers": [{"first_name": "Alex", "last_name": "Traveler", "passenger_type": "adult"}],
        },
    )
    assert booking.status_code == 200, booking.text
    booking_body = booking.json()
    assert booking_body["status"] == "pending_payment"

    payment = client.post(
        "/api/v1/payments",
        json={
            "booking_id": booking_body["id"],
            "method": "apple_pay",
            "idempotency_key": "checkout-00000001",
        },
    )
    assert payment.status_code == 200, payment.text
    assert payment.json()["status"] == "requires_action"

    succeeded = client.post(f"/api/v1/payments/{payment.json()['id']}/dev-succeed")
    assert succeeded.status_code == 200, succeeded.text
    assert succeeded.json()["status"] == "paid"

    fetched = client.get(f"/api/v1/bookings/{booking_body['reference']}", params={"email": "buyer@example.com"})
    assert fetched.status_code == 200, fetched.text
    assert fetched.json()["status"] == "ticketed"
    assert len(fetched.json()["tickets"]) == 1

    cancelled = client.post(
        f"/api/v1/bookings/{booking_body['reference']}/cancel",
        json={"email": "buyer@example.com"},
    )
    assert cancelled.status_code == 200, cancelled.text
    assert cancelled.json()["status"] == "refunded"


def test_payment_idempotency(client):
    travel_date = (date.today() + timedelta(days=12)).isoformat()
    s = client.post(
        "/api/v1/searches",
        json={"origin": "Prague", "destination": "Berlin", "departure_date": travel_date, "currency": "EUR"},
    ).json()
    session = client.post("/api/v1/booking-sessions", json={"journey_id": s["journeys"][0]["id"]}).json()
    booking = client.post(
        "/api/v1/bookings",
        json={
            "booking_session_id": session["id"],
            "contact_email": "idempotent@example.com",
            "contact_phone": "+4912345678",
            "passengers": [{"first_name": "Sam", "last_name": "Test"}],
        },
    ).json()
    payload = {"booking_id": booking["id"], "method": "visa", "idempotency_key": "same-key-123456"}
    first = client.post("/api/v1/payments", json=payload)
    second = client.post("/api/v1/payments", json=payload)
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]


def test_payment_methods_are_exact_core_set(client):
    response = client.get("/api/v1/payments/methods")
    assert response.status_code == 200
    ids = [item["id"] for item in response.json()]
    assert ids == ["visa", "mastercard", "apple_pay", "google_pay", "paypal"]
