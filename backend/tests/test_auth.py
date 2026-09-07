import pytest
from datetime import timedelta
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.core.security import create_access_token
from backend.app.models import UserRole

client = TestClient(app)

# ---------------------------------------------------------
# Test Users Fixtures & Helper
# ---------------------------------------------------------
TEST_CREDENTIALS = {
    "ADMIN": ("admin", "Admin@LabelSure2026"),
    "INSPECTOR": ("inspector1", "Inspector@2026"),
    "SUPERVISOR": ("supervisor1", "Supervisor@2026"),
    "VIEWER": ("viewer1", "Viewer@2026"),
}

def get_auth_token(role: str) -> str:
    username, password = TEST_CREDENTIALS[role]
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200, f"Login failed for role {role}: {res.text}"
    return res.json()["access_token"]

# ---------------------------------------------------------
# 1. Valid Login Tests
# ---------------------------------------------------------
@pytest.mark.parametrize("role,username,expected_title", [
    ("ADMIN", "admin", "Chief Legal Metrology Officer"),
    ("INSPECTOR", "inspector1", "Rajesh Sharma (Inspector)"),
    ("SUPERVISOR", "supervisor1", "Priya Varma (Assistant Controller)"),
    ("VIEWER", "viewer1", "Compliance Audit Observer"),
])
def test_valid_login_all_roles(role, username, expected_title):
    _, password = TEST_CREDENTIALS[role]
    res = client.post("/api/auth/login", json={"username": username, "password": password})
    assert res.status_code == 200
    data = res.json()
    assert "access_token" in data
    assert data["token_type"] == "bearer"
    assert data["role"] == role
    assert data["username"] == username
    assert data["full_name"] == expected_title
    assert "user_id" in data

# ---------------------------------------------------------
# 2. Invalid Password & Credentials Tests
# ---------------------------------------------------------
def test_login_invalid_password():
    res = client.post("/api/auth/login", json={"username": "admin", "password": "WrongPassword!2026"})
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"

def test_login_nonexistent_user():
    res = client.post("/api/auth/login", json={"username": "non_existent_inspector", "password": "AnyPassword123"})
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS"

# ---------------------------------------------------------
# 3. Current-User (/api/auth/me) Endpoint Tests
# ---------------------------------------------------------
def test_current_user_profile():
    token = get_auth_token("INSPECTOR")
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["username"] == "inspector1"
    assert data["role"] == "INSPECTOR"
    assert data["badge_number"] == "INS-DL-412"
    assert data["is_active"] is True

# ---------------------------------------------------------
# 4. Expired & Invalid Token Tests
# ---------------------------------------------------------
def test_expired_token_rejection():
    # Login first to obtain valid user id
    token = get_auth_token("ADMIN")
    me_res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    admin_id = me_res.json()["id"]

    # Generate token already expired by 10 minutes
    expired_token = create_access_token(
        data={"sub": admin_id, "role": "ADMIN"},
        expires_delta=timedelta(minutes=-10)
    )
    res = client.get("/api/auth/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"

def test_invalid_malformed_token_rejection():
    res = client.get("/api/auth/me", headers={"Authorization": "Bearer not-a-valid-jwt-token-string"})
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_TOKEN"

def test_missing_auth_header_unauthorized():
    res = client.get("/api/auth/me")
    assert res.status_code == 401
    data = res.json()
    assert data["success"] is False
    assert data["error"]["code"] == "INVALID_CREDENTIALS" or data["error"]["code"] == "UNAUTHORIZED" or res.status_code == 401

# ---------------------------------------------------------
# 5. Role-Based Access Control (RBAC) & Hierarchy Tests
# ---------------------------------------------------------
def test_admin_role_access():
    admin_token = get_auth_token("ADMIN")
    headers = {"Authorization": f"Bearer {admin_token}"}

    # ADMIN should have access to ALL tiers
    assert client.get("/api/auth/admin-area", headers=headers).status_code == 200
    assert client.get("/api/auth/supervisor-area", headers=headers).status_code == 200
    assert client.get("/api/auth/inspector-area", headers=headers).status_code == 200
    assert client.get("/api/auth/viewer-area", headers=headers).status_code == 200
    assert client.get("/api/auth/users", headers=headers).status_code == 200

def test_supervisor_role_access():
    sup_token = get_auth_token("SUPERVISOR")
    headers = {"Authorization": f"Bearer {sup_token}"}

    # SUPERVISOR can access supervisor, inspector, viewer, and users
    assert client.get("/api/auth/supervisor-area", headers=headers).status_code == 200
    assert client.get("/api/auth/inspector-area", headers=headers).status_code == 200
    assert client.get("/api/auth/viewer-area", headers=headers).status_code == 200
    assert client.get("/api/auth/users", headers=headers).status_code == 200

    # SUPERVISOR CANNOT access admin area
    admin_res = client.get("/api/auth/admin-area", headers=headers)
    assert admin_res.status_code == 403
    assert admin_res.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

def test_inspector_role_access():
    ins_token = get_auth_token("INSPECTOR")
    headers = {"Authorization": f"Bearer {ins_token}"}

    # INSPECTOR can access inspector and viewer areas
    assert client.get("/api/auth/inspector-area", headers=headers).status_code == 200
    assert client.get("/api/auth/viewer-area", headers=headers).status_code == 200

    # INSPECTOR CANNOT access supervisor or admin areas
    sup_res = client.get("/api/auth/supervisor-area", headers=headers)
    assert sup_res.status_code == 403
    assert sup_res.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    admin_res = client.get("/api/auth/admin-area", headers=headers)
    assert admin_res.status_code == 403
    assert admin_res.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"

    users_res = client.get("/api/auth/users", headers=headers)
    assert users_res.status_code == 403

def test_viewer_role_access():
    view_token = get_auth_token("VIEWER")
    headers = {"Authorization": f"Bearer {view_token}"}

    # VIEWER can only access viewer-area and me
    assert client.get("/api/auth/viewer-area", headers=headers).status_code == 200
    assert client.get("/api/auth/me", headers=headers).status_code == 200

    # VIEWER CANNOT access inspector, supervisor, admin, or user list
    assert client.get("/api/auth/inspector-area", headers=headers).status_code == 403
    assert client.get("/api/auth/supervisor-area", headers=headers).status_code == 403
    assert client.get("/api/auth/admin-area", headers=headers).status_code == 403
    assert client.get("/api/auth/users", headers=headers).status_code == 403

# ---------------------------------------------------------
# 6. User Creation Authorization Tests
# ---------------------------------------------------------
def test_admin_can_register_new_user():
    admin_token = get_auth_token("ADMIN")
    import uuid
    rand_suffix = uuid.uuid4().hex[:6]
    payload = {
        "username": f"inspector_test_{rand_suffix}",
        "email": f"inspector_{rand_suffix}@labelsure.gov.in",
        "password": "SecurePassword@123",
        "full_name": f"Test Inspector {rand_suffix}",
        "role": "INSPECTOR",
        "badge_number": f"TEST-{rand_suffix}"
    }
    res = client.post("/api/auth/register", json=payload, headers={"Authorization": f"Bearer {admin_token}"})
    assert res.status_code == 200
    created = res.json()
    assert created["username"] == payload["username"]
    assert created["role"] == "INSPECTOR"

def test_non_admin_cannot_register_user():
    ins_token = get_auth_token("INSPECTOR")
    payload = {
        "username": "unauthorized_user",
        "email": "unauth@labelsure.gov.in",
        "password": "Password123!",
        "full_name": "Unauthorized User",
        "role": "INSPECTOR"
    }
    res = client.post("/api/auth/register", json=payload, headers={"Authorization": f"Bearer {ins_token}"})
    assert res.status_code == 403
    assert res.json()["error"]["code"] == "INSUFFICIENT_PERMISSIONS"
