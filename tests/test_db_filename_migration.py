"""
Tests for scripts/migrate-db-filename.sh (WOF-37).

The rename moves the SQLite file from whoseonfirst.db to whoisonfirst.db.
The container entrypoint runs this script before migrations and before the
app's first-boot auto-seed, so an existing database is renamed in place and
never seeded over.
"""

import subprocess
from pathlib import Path

import pytest

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "migrate-db-filename.sh"


def run(data_dir: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        ["bash", str(SCRIPT), str(data_dir)],
        capture_output=True, text=True, check=False,
    )


@pytest.fixture
def data_dir(tmp_path):
    d = tmp_path / "data"
    d.mkdir()
    return d


def test_old_db_only_is_moved_with_sidecars(data_dir):
    (data_dir / "whoseonfirst.db").write_bytes(b"main")
    (data_dir / "whoseonfirst.db-wal").write_bytes(b"wal")
    (data_dir / "whoseonfirst.db-shm").write_bytes(b"shm")

    result = run(data_dir)

    assert result.returncode == 0, result.stderr
    assert (data_dir / "whoisonfirst.db").read_bytes() == b"main"
    assert (data_dir / "whoisonfirst.db-wal").read_bytes() == b"wal"
    assert (data_dir / "whoisonfirst.db-shm").read_bytes() == b"shm"
    assert not (data_dir / "whoseonfirst.db").exists()
    assert not (data_dir / "whoseonfirst.db-wal").exists()
    assert not (data_dir / "whoseonfirst.db-shm").exists()


def test_both_present_leaves_both_untouched_and_warns(data_dir):
    (data_dir / "whoseonfirst.db").write_bytes(b"old")
    (data_dir / "whoisonfirst.db").write_bytes(b"new")

    result = run(data_dir)

    assert result.returncode == 0, result.stderr
    assert (data_dir / "whoseonfirst.db").read_bytes() == b"old"
    assert (data_dir / "whoisonfirst.db").read_bytes() == b"new"
    assert "WARNING" in result.stdout


def test_new_only_is_untouched(data_dir):
    (data_dir / "whoisonfirst.db").write_bytes(b"new")

    result = run(data_dir)

    assert result.returncode == 0, result.stderr
    assert (data_dir / "whoisonfirst.db").read_bytes() == b"new"


def test_neither_present_creates_nothing(data_dir):
    result = run(data_dir)

    assert result.returncode == 0, result.stderr
    assert list(data_dir.iterdir()) == []


def test_empty_old_db_is_still_moved(data_dir):
    """A zero-byte old file is moved too; the app decides whether to seed it."""
    (data_dir / "whoseonfirst.db").write_bytes(b"")

    result = run(data_dir)

    assert result.returncode == 0, result.stderr
    assert (data_dir / "whoisonfirst.db").exists()
    assert not (data_dir / "whoseonfirst.db").exists()
