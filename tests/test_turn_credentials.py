"""
Test TURN Credentials Endpoint
Tests the TURN server credential generation functionality
"""

import pytest
import hmac
import hashlib
import base64
import time

from src.utils.config import get_settings


def test_turn_credentials_without_auth(client):
    """Test that TURN credentials endpoint requires authentication"""
    response = client.get("/auth/turn-credentials")
    # FastAPI returns 403 when no credentials are provided at all
    assert response.status_code in [401, 403]


def test_turn_credentials_with_invalid_token(client):
    """Test TURN credentials with invalid token"""
    response = client.get(
        "/auth/turn-credentials",
        headers={"Authorization": "Bearer invalid_token"}
    )
    assert response.status_code == 401


def test_turn_credentials_success(client):
    """Test successful TURN credentials generation"""
    # First login to get valid token
    login_response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Get settings to set TURN server config for test
    settings = get_settings()
    original_secret = settings.turnserver_secret
    original_urls = settings.turnserver_urls

    # Set test values
    settings.turnserver_secret = "test_secret_key"
    settings.turnserver_urls = ["turn:test.example.com:3478", "turns:test.example.com:5349"]
    settings.turnserver_ttl = 86400

    try:
        # Get TURN credentials
        response = client.get(
            "/auth/turn-credentials",
            headers={"Authorization": f"Bearer {token}"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response structure
        assert "username" in data
        assert "credential" in data
        assert "urls" in data
        assert "ttl" in data

        # Verify username format (timestamp:username)
        username_parts = data["username"].split(":")
        assert len(username_parts) == 2
        timestamp = int(username_parts[0])
        assert username_parts[1] == "admin"

        # Verify timestamp is in the future
        current_time = int(time.time())
        assert timestamp > current_time
        assert timestamp <= current_time + settings.turnserver_ttl + 10  # Allow 10s tolerance

        # Verify credential is valid HMAC-SHA1
        secret_bytes = settings.turnserver_secret.encode('utf-8')
        username_bytes = data["username"].encode('utf-8')
        expected_hmac = hmac.new(secret_bytes, username_bytes, hashlib.sha1)
        expected_credential = base64.b64encode(expected_hmac.digest()).decode('utf-8')

        assert data["credential"] == expected_credential

        # Verify URLs
        assert data["urls"] == settings.turnserver_urls

        # Verify TTL
        assert data["ttl"] == settings.turnserver_ttl

    finally:
        # Restore original settings
        settings.turnserver_secret = original_secret
        settings.turnserver_urls = original_urls


def test_turn_credentials_without_config(client):
    """Test TURN credentials when server is not configured"""
    # Login
    login_response = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login_response.status_code == 200
    token = login_response.json()["access_token"]

    # Get settings and clear TURN config
    settings = get_settings()
    original_secret = settings.turnserver_secret
    original_urls = settings.turnserver_urls

    settings.turnserver_secret = ""
    settings.turnserver_urls = []

    try:
        # Try to get TURN credentials
        response = client.get(
            "/auth/turn-credentials",
            headers={"Authorization": f"Bearer {token}"}
        )

        # Should fail with 503 Service Unavailable
        assert response.status_code == 503
        assert "not configured" in response.json()["detail"].lower()

    finally:
        # Restore original settings
        settings.turnserver_secret = original_secret
        settings.turnserver_urls = original_urls


def test_turn_credentials_hmac_algorithm():
    """Test that HMAC-SHA1 algorithm is correctly implemented"""
    # Test with known values
    secret = "test_secret"
    username = "1704067200:testuser"

    # Generate HMAC-SHA1
    secret_bytes = secret.encode('utf-8')
    username_bytes = username.encode('utf-8')
    hmac_hash = hmac.new(secret_bytes, username_bytes, hashlib.sha1)
    credential = base64.b64encode(hmac_hash.digest()).decode('utf-8')

    # Verify it's a valid base64 string
    assert len(credential) > 0
    try:
        base64.b64decode(credential)
    except Exception:
        pytest.fail("Credential is not valid base64")

    # Verify HMAC-SHA1 produces consistent results
    hmac_hash2 = hmac.new(secret_bytes, username_bytes, hashlib.sha1)
    credential2 = base64.b64encode(hmac_hash2.digest()).decode('utf-8')
    assert credential == credential2


def test_turn_credentials_different_users(client):
    """Test that different users get different credentials"""
    # Login as admin
    login1 = client.post(
        "/auth/login",
        json={"username": "admin", "password": "admin123"}
    )
    assert login1.status_code == 200
    token1 = login1.json()["access_token"]

    # Login as user1
    login2 = client.post(
        "/auth/login",
        json={"username": "user1", "password": "password123"}
    )
    assert login2.status_code == 200
    token2 = login2.json()["access_token"]

    # Configure TURN server
    settings = get_settings()
    original_secret = settings.turnserver_secret
    original_urls = settings.turnserver_urls

    settings.turnserver_secret = "test_secret_key"
    settings.turnserver_urls = ["turn:test.example.com:3478"]

    try:
        # Get credentials for both users
        response1 = client.get(
            "/auth/turn-credentials",
            headers={"Authorization": f"Bearer {token1}"}
        )
        response2 = client.get(
            "/auth/turn-credentials",
            headers={"Authorization": f"Bearer {token2}"}
        )

        assert response1.status_code == 200
        assert response2.status_code == 200

        creds1 = response1.json()
        creds2 = response2.json()

        # Usernames should contain different usernames
        assert "admin" in creds1["username"]
        assert "user1" in creds2["username"]

        # Credentials should be different
        assert creds1["credential"] != creds2["credential"]

    finally:
        settings.turnserver_secret = original_secret
        settings.turnserver_urls = original_urls


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

