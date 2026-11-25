"""
Guard: every page that uses the Bootstrap JS API loads Bootstrap itself (WOF-44).

Tabler is pinned to @tabler/core@1.6.1 (WOF-45). Since Tabler 1.6.x its UMD bundle
exports to ``window.tabler`` and no longer sets a global ``bootstrap``, so a
page relying on Tabler alone throws ReferenceError at ``new bootstrap.Modal``
(the Admin "Restore from Backup" button silently did nothing).
"""

import re
from pathlib import Path

import pytest

FRONTEND = Path(__file__).resolve().parents[1] / "frontend"
BOOTSTRAP_BUNDLE = "bootstrap.bundle.min.js"

PAGES_USING_BOOTSTRAP_JS = sorted(
    p for p in FRONTEND.glob("*.html") if "bootstrap." in p.read_text()
)


def test_some_pages_use_bootstrap_js():
    assert PAGES_USING_BOOTSTRAP_JS, "expected at least one page to use bootstrap.*"


@pytest.mark.parametrize("page", PAGES_USING_BOOTSTRAP_JS, ids=lambda p: p.name)
def test_page_using_bootstrap_js_loads_bootstrap_bundle(page):
    assert BOOTSTRAP_BUNDLE in page.read_text(), (
        f"{page.name} calls bootstrap.* but does not load {BOOTSTRAP_BUNDLE}; "
        "Tabler no longer provides the global"
    )


CDN_LATEST = re.compile(r"""https?://[^\s"'<>]+@latest\b""")
ALL_PAGES = sorted(FRONTEND.glob("*.html"))


@pytest.mark.parametrize("page", ALL_PAGES, ids=lambda p: p.name)
def test_page_pins_cdn_versions(page):
    """No CDN package may float on @latest (WOF-45): upstream releases change
    JS globals and CSS without warning."""
    hits = CDN_LATEST.findall(page.read_text())
    assert not hits, f"{page.name} loads unpinned CDN assets: {hits}"
