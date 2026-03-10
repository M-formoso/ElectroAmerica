import pytest
from fastapi.testclient import TestClient
from tests.conftest import auth_headers


class TestAuth:
    """Tests for authentication endpoints."""

    def test_login_success(self, client: TestClient, admin_user):
        """Test successful login."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "admin123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_wrong_password(self, client: TestClient, admin_user):
        """Test login with wrong password."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "wrongpass"}
        )
        assert response.status_code == 401

    def test_login_nonexistent_user(self, client: TestClient):
        """Test login with nonexistent user."""
        response = client.post(
            "/api/v1/auth/login",
            data={"username": "noexiste@test.com", "password": "test123"}
        )
        assert response.status_code == 401

    def test_login_inactive_user(self, client: TestClient, db, admin_user):
        """Test login with inactive user."""
        admin_user.activo = False
        db.commit()

        response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "admin123"}
        )
        assert response.status_code == 401

    def test_me_authenticated(self, client: TestClient, admin_token):
        """Test getting current user info."""
        response = client.get(
            "/api/v1/auth/me",
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200
        data = response.json()
        assert data["email"] == "admin@test.com"
        assert data["rol"] == "administrador"

    def test_me_unauthenticated(self, client: TestClient):
        """Test getting current user without token."""
        response = client.get("/api/v1/auth/me")
        assert response.status_code == 401

    def test_refresh_token(self, client: TestClient, admin_user):
        """Test refreshing access token."""
        # First login to get tokens
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "admin123"}
        )
        refresh_token = login_response.json()["refresh_token"]

        # Use refresh token to get new access token
        response = client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token}
        )
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data

    def test_change_password(self, client: TestClient, admin_token):
        """Test changing password."""
        response = client.post(
            "/api/v1/auth/cambiar-password",
            json={
                "password_actual": "admin123",
                "password_nuevo": "newpass123"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 200

        # Try login with new password
        login_response = client.post(
            "/api/v1/auth/login",
            data={"username": "admin@test.com", "password": "newpass123"}
        )
        assert login_response.status_code == 200

    def test_change_password_wrong_current(self, client: TestClient, admin_token):
        """Test changing password with wrong current password."""
        response = client.post(
            "/api/v1/auth/cambiar-password",
            json={
                "password_actual": "wrongpass",
                "password_nuevo": "newpass123"
            },
            headers=auth_headers(admin_token)
        )
        assert response.status_code == 400
