"""Tests for mock-app/app.py — API key authentication and startup behavior."""
import importlib
import os
import sys
import pytest


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _load_app(api_key: str):
    """Import app module with the given API_KEY env var set."""
    os.environ["API_KEY"] = api_key
    # Force a fresh import each time so module-level code re-runs.
    if "app" in sys.modules:
        del sys.modules["app"]
    import app as mock_app  # noqa: PLC0415
    return mock_app.app


def _unload_app():
    if "app" in sys.modules:
        del sys.modules["app"]
    os.environ.pop("API_KEY", None)


# ---------------------------------------------------------------------------
# Startup tests
# ---------------------------------------------------------------------------

class TestStartup:
    def teardown_method(self):
        _unload_app()

    def test_raises_when_api_key_missing(self):
        """App must raise RuntimeError when API_KEY env var is not set."""
        os.environ.pop("API_KEY", None)
        if "app" in sys.modules:
            del sys.modules["app"]
        with pytest.raises(RuntimeError, match="API_KEY environment variable is not set"):
            import app  # noqa: F401, PLC0415

    def test_starts_when_api_key_present(self):
        """App must initialise successfully when API_KEY env var is set."""
        flask_app = _load_app("test-secret-key")
        assert flask_app is not None


# ---------------------------------------------------------------------------
# Authentication tests
# ---------------------------------------------------------------------------

class TestAuthentication:
    @pytest.fixture(autouse=True)
    def client(self):
        flask_app = _load_app("valid-test-key")
        flask_app.config["TESTING"] = True
        with flask_app.test_client() as c:
            yield c
        _unload_app()

    def test_valid_key_returns_200(self, client):
        response = client.get("/api/data", headers={"x-api-key": "valid-test-key"})
        assert response.status_code == 200
        data = response.get_json()
        assert "message" in data

    def test_wrong_key_returns_401(self, client):
        response = client.get("/api/data", headers={"x-api-key": "wrong-key"})
        assert response.status_code == 401
        data = response.get_json()
        assert data.get("error") == "Unauthorized"

    def test_missing_key_returns_401(self, client):
        response = client.get("/api/data")
        assert response.status_code == 401

    def test_empty_key_returns_401(self, client):
        response = client.get("/api/data", headers={"x-api-key": ""})
        assert response.status_code == 401
