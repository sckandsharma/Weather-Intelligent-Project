import uuid
from datetime import timedelta
import pytest
from fastapi.testclient import TestClient

from app.auth.jwt_handler import create_token
from app.core.security import limiter


def test_register_and_login_success(client: TestClient):
    email = f"test_{uuid.uuid4().hex[:8]}@example.com"
    reg_payload = {
        "full_name": "Aarav Patel",
        "email": email,
        "password": "SecurePassword123!",
    }
    res = client.post("/api/v1/auth/register", json=reg_payload)
    assert res.status_code == 201
    data = res.json()
    assert data["email"] == email
    assert data["role"] == "user"

    # Test login
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": "SecurePassword123!"},
    )
    assert login_res.status_code == 200
    tokens = login_res.json()
    assert "access_token" in tokens
    assert "refresh_token" in tokens
    assert tokens["token_type"] == "bearer"


def test_register_duplicate_email(client: TestClient):
    email = f"dup_{uuid.uuid4().hex[:8]}@example.com"
    payload = {
        "full_name": "Duplicate User",
        "email": email,
        "password": "Password123!",
    }
    res1 = client.post("/api/v1/auth/register", json=payload)
    assert res1.status_code == 201

    res2 = client.post("/api/v1/auth/register", json=payload)
    assert res2.status_code == 409
    assert "already registered" in res2.json()["detail"].lower()


def test_login_wrong_password(client: TestClient):
    payload = {
        "full_name": "Auth Test User",
        "email": "authtest@example.com",
        "password": "CorrectPassword123!",
    }
    client.post("/api/v1/auth/register", json=payload)

    res = client.post(
        "/api/v1/auth/login",
        json={"email": "authtest@example.com", "password": "WrongPassword!"},
    )
    assert res.status_code == 401
    assert "invalid email or password" in res.json()["detail"].lower()


def test_me_endpoint_and_token_invalidation(client: TestClient):
    payload = {"full_name": "Me User", "email": "me@example.com", "password": "Pass12345678!"}
    client.post("/api/v1/auth/register", json=payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "me@example.com", "password": "Pass12345678!"})
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Access /users/me
    me_res = client.get("/api/v1/users/me", headers=headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "me@example.com"

    # Logout to revoke token
    logout_res = client.post("/api/v1/auth/logout", headers=headers)
    assert logout_res.status_code == 200

    # Revoked token should return 401
    revoked_res = client.get("/api/v1/users/me", headers=headers)
    assert revoked_res.status_code == 401
    assert "revoked" in revoked_res.json()["detail"].lower()


def test_expired_jwt(client: TestClient, regular_user):
    expired_token = create_token(
        user_id=regular_user.id,
        token_type="access",
        expires_delta=timedelta(seconds=-10),
        role=regular_user.role.value,
    )
    res = client.get("/api/v1/users/me", headers={"Authorization": f"Bearer {expired_token}"})
    assert res.status_code == 401
    assert "expired" in res.json()["detail"].lower()


def test_invalid_jwt(client: TestClient):
    res = client.get("/api/v1/users/me", headers={"Authorization": "Bearer this.is.invalid.jwt"})
    assert res.status_code == 401


def test_refresh_token_flow(client: TestClient):
    payload = {"full_name": "Refresh User", "email": "refresh@example.com", "password": "Pass12345678!"}
    client.post("/api/v1/auth/register", json=payload)

    login_res = client.post("/api/v1/auth/login", json={"email": "refresh@example.com", "password": "Pass12345678!"})
    refresh_token = login_res.json()["refresh_token"]

    ref_res = client.post("/api/v1/auth/refresh", json={"refresh_token": refresh_token})
    assert ref_res.status_code == 200
    new_data = ref_res.json()
    assert "access_token" in new_data
    assert new_data["token_type"] == "bearer"


def test_rbac_role_restrictions(client: TestClient, user_headers, admin_headers, evaluator_headers):
    # User cannot run evaluation (Evaluator/Admin only) -> 403
    res_user_eval = client.post("/api/v1/evaluation/run", headers=user_headers)
    assert res_user_eval.status_code == 403

    # User cannot access admin users list -> 403
    res_user_admin = client.get("/api/v1/users/", headers=user_headers)
    assert res_user_admin.status_code == 403

    # Admin can access admin users list -> 200
    res_admin = client.get("/api/v1/users/", headers=admin_headers)
    assert res_admin.status_code == 200


def test_rate_limiting_status_code(client: TestClient):
    # Temporarily enable rate limiter to test 429
    limiter.enabled = True
    try:
        url = "/api/v1/auth/login"
        payload = {"email": "ratelimit@example.com", "password": "wrongpassword123!"}
        for _ in range(6):
            res = client.post(url, json=payload)
        assert res.status_code == 429
        assert "rate limit exceeded" in res.json()["error"].lower()
    finally:
        limiter.enabled = False
