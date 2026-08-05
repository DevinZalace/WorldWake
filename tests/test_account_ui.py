"""Tests for the browser-facing account interface."""

from fastapi.testclient import TestClient


def test_home_page_contains_account_controls(
    api_client: TestClient,
) -> None:
    """The landing page should expose the account workflow."""

    response = api_client.get("/")

    assert response.status_code == 200

    page = response.text

    assert 'id="open-login"' in page
    assert 'id="open-register"' in page
    assert 'id="logout-button"' in page
    assert 'id="login-form"' in page
    assert 'id="register-form"' in page
    assert 'id="change-password-form"' in page


def test_account_javascript_uses_authentication_endpoints(
    api_client: TestClient,
) -> None:
    """The browser script should connect every account action."""

    response = api_client.get(
        "/static/app.js"
    )

    assert response.status_code == 200

    script = response.text

    assert "/api/auth/register" in script
    assert "/api/auth/login" in script
    assert "/api/auth/me" in script
    assert "/api/auth/logout" in script
    assert "/api/auth/change-password" in script
    assert "X-CSRF-Token" in script