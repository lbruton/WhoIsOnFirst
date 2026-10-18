"""
Guards on docker-compose.yml (WOF-37 / WOF-42).

The prod volume name is derived from the compose project (Portainer stack)
name plus the volume key: stack ``whoseonfirst`` + key ``whoseonfirst-data``
= ``whoseonfirst_whoseonfirst-data``, which holds the prod database. If the
key is renamed and the existing stack redeploys, Compose mounts a NEW empty
volume and the app auto-seeds over what looks like a wiped prod. The key is
therefore pinned like ``_LEGACY_SALT``: never rename it.

Read as text on purpose so the test needs no YAML dependency.
"""

import re
from pathlib import Path

COMPOSE = (Path(__file__).resolve().parents[1] / "docker-compose.yml").read_text()


def test_data_volume_key_is_pinned_to_legacy_name():
    assert re.search(r"^\s+- whoseonfirst-data:/app/data\s*$", COMPOSE, re.M)
    assert re.search(r"^volumes:\s*\n\s+whoseonfirst-data:\s*$", COMPOSE, re.M)


def test_no_renamed_data_volume_key():
    assert "whoisonfirst-data" not in COMPOSE


def test_container_name_and_port_are_overridable_with_prod_defaults():
    assert "container_name: ${CONTAINER_NAME:-whoisonfirst}" in COMPOSE
    assert '"${HOST_PORT:-8900}:8000"' in COMPOSE


def test_dev_rails_are_passed_through():
    assert "APP_ENV=${APP_ENV:-prod}" in COMPOSE
    assert "SMS_ALLOWED_NUMBERS=${SMS_ALLOWED_NUMBERS:-}" in COMPOSE
