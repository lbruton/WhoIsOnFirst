"""
Tests for version reporting across every surface.

These tests read the canonical VERSION file dynamically, so a version bump
needs no test edits — but any hardcoded literal that drifts from VERSION
(the WOF-14 bug) fails immediately.
"""

from pathlib import Path

from fastapi.testclient import TestClient

# Repo root is three levels up from tests/api/test_version.py
VERSION_FILE = Path(__file__).resolve().parents[2] / "VERSION"
CANONICAL_VERSION = VERSION_FILE.read_text().strip()


class TestVersionEndpoint:
    """Tests for GET /api/v1/version."""

    def test_get_version_returns_200(self, client: TestClient):
        """The version endpoint returns the canonical VERSION file content."""
        response = client.get("/api/v1/version")

        assert response.status_code == 200
        data = response.json()
        assert "version" in data
        assert data["version"] == CANONICAL_VERSION

    def test_get_version_missing_file(self, client: TestClient, monkeypatch):
        """Test that a missing VERSION file returns {"version": "unknown"}."""
        import src.version as version_module

        monkeypatch.setattr(
            version_module, "_VERSION_FILE", Path("/nonexistent/VERSION")
        )
        # get_app_version is lru_cached; bust the cache around the patched read
        version_module.get_app_version.cache_clear()
        try:
            response = client.get("/api/v1/version")

            assert response.status_code == 200
            data = response.json()
            assert data["version"] == "unknown"
        finally:
            version_module.get_app_version.cache_clear()


class TestVersionEnvironment:
    """WOF-42: /api/v1/version reports APP_ENV so the UI can show a DEV badge."""

    def test_environment_defaults_to_prod(self, client: TestClient, monkeypatch):
        monkeypatch.delenv("APP_ENV", raising=False)

        response = client.get("/api/v1/version")

        assert response.json()["environment"] == "prod"

    def test_environment_reports_dev(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("APP_ENV", "dev")

        response = client.get("/api/v1/version")

        assert response.json()["environment"] == "dev"

    def test_environment_is_normalized(self, client: TestClient, monkeypatch):
        monkeypatch.setenv("APP_ENV", "  DEV ")

        response = client.get("/api/v1/version")

        assert response.json()["environment"] == "dev"


class TestVersionConsistency:
    """Every version surface must report the canonical VERSION (WOF-14 drift guard)."""

    def test_health_reports_canonical_version(self, client: TestClient):
        """GET /health — what monitoring and the incident runbook check."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["version"] == CANONICAL_VERSION

    def test_api_info_reports_canonical_version(self, client: TestClient):
        """GET /api."""
        response = client.get("/api")
        assert response.status_code == 200
        assert response.json()["version"] == CANONICAL_VERSION

    def test_openapi_reports_canonical_version(self, client: TestClient):
        """The OpenAPI schema / Swagger /docs version."""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        assert response.json()["info"]["version"] == CANONICAL_VERSION
