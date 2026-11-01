"""
Guard: the repo is public, so sample data uses the dev-seed people and 555
numbers, never a real team member's phone number.
"""

import re
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCANNED_DIRS = ["src", "frontend", "DocVault", ".context", "scripts", "e2e"]
SCANNED_ROOT_FILES = ["CHANGELOG.md", "README.md", "CLAUDE.md", "AGENTS.md"]
TEXT_SUFFIXES = {".py", ".html", ".js", ".css", ".md", ".json", ".yml", ".yaml", ".txt", ".sh"}
SKIPPED_PARTS = {"node_modules", "__pycache__", "htmlcov", "venv", ".venv"}

# The team's local area code. Sample numbers belong on the fictional 555 range.
LOCAL_NUMBER = re.compile(r"(?:\+1|\b1)?\(?918\)?[\s.-]?\d{3}[\s.-]?\d{4}\b")


def _scanned_files():
    files = [REPO / name for name in SCANNED_ROOT_FILES if (REPO / name).is_file()]
    for top in SCANNED_DIRS:
        for path in (REPO / top).rglob("*"):
            if (
                path.is_file()
                and path.suffix in TEXT_SUFFIXES
                and not SKIPPED_PARTS.intersection(path.parts)
            ):
                files.append(path)
    return sorted(files)


SCANNED_FILES = _scanned_files()


def test_scan_covers_the_frontend_and_api():
    names = {p.relative_to(REPO).as_posix() for p in SCANNED_FILES}
    assert "frontend/styleguide.html" in names
    assert "src/api/routes/settings.py" in names


@pytest.mark.parametrize("path", SCANNED_FILES, ids=lambda p: p.relative_to(REPO).as_posix())
def test_file_has_no_local_phone_numbers(path):
    hits = LOCAL_NUMBER.findall(path.read_text(errors="ignore"))
    # Report only the last four digits so a failure does not print the number.
    assert not hits, f"{path.name} has {len(hits)} local number(s): " + ", ".join(
        "***" + re.sub(r"\D", "", h)[-4:] for h in hits
    )
