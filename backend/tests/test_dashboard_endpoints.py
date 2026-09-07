import pytest
from fastapi.testclient import TestClient
from backend.app.main import app

client = TestClient(app)

def test_dashboard_new_endpoints():
    # 1. Login as Admin
    login_res = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "Admin@LabelSure2026"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Test GET /api/reports
    reports_res = client.get("/api/reports", headers=headers)
    assert reports_res.status_code == 200
    assert isinstance(reports_res.json(), list)

    # 3. Test GET /api/images
    images_res = client.get("/api/images", headers=headers)
    assert images_res.status_code == 200
    assert isinstance(images_res.json(), list)

    # 4. Test GET /api/dashboard/analytics
    analytics_res = client.get("/api/dashboard/analytics", headers=headers)
    assert analytics_res.status_code == 200
    analytics_data = analytics_res.json()
    assert "total_inspections" in analytics_data
    assert "compliance_rate" in analytics_data
    assert "top_violations" in analytics_data
    assert "commodity_distribution" in analytics_data

    # 5. Test GET /api/auth/users
    users_res = client.get("/api/auth/users", headers=headers)
    assert users_res.status_code == 200
    users = users_res.json()
    assert len(users) >= 4
