def test_health(client):
    r = client.get("/api/v1/health")
    assert r.status_code == 200
    assert r.json()["status"] == "ok"


def test_admin_requires_key(client):
    assert client.get("/api/v1/admin/summary").status_code == 401
    assert client.get("/api/v1/admin/summary", headers={"X-Admin-Key": "test-admin-key"}).status_code == 200
