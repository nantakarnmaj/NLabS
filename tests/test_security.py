"""Tests for security headers, XSS escaping, safe error handling, and local asset enforcement."""

from __future__ import annotations

import re
from pathlib import Path
from app.models.mission import Mission
from app.extensions import db


def test_security_headers_present(client):
    """Verify security headers (CSP, nosniff, X-Frame-Options, Referrer-Policy)."""
    res = client.get("/")
    assert res.status_code == 200

    # Content-Security-Policy
    csp = res.headers.get("Content-Security-Policy", "")
    assert "default-src 'self'" in csp
    assert "script-src 'self'" in csp
    assert "style-src 'self'" in csp

    # nosniff
    assert res.headers.get("X-Content-Type-Options") == "nosniff"

    # Frame-Options
    assert res.headers.get("X-Frame-Options") == "DENY"

    # Referrer-Policy
    assert res.headers.get("Referrer-Policy") == "strict-origin-when-cross-origin"


def test_html_escaping_untrusted_input(app, client):
    """Verify untrusted strings in database are escaped by Jinja and not rendered as raw HTML."""
    with app.app_context():
        malicious = Mission(
            slug="xss-test-room",
            room_number="998",
            title='<script>alert("XSS")</script>',
            subtitle='<img src=x onerror=alert(1)>',
            description='<b>Bold text</b> & <script>document.cookie</script>',
            availability="coming_soon",
            display_order=99,
        )
        db.session.add(malicious)
        db.session.commit()

    res = client.get("/ward")
    assert res.status_code == 200
    html = res.get_data(as_text=True)

    # Must be escaped
    assert '<script>alert("XSS")</script>' not in html
    assert '&lt;script&gt;alert(&#34;XSS&#34;)&lt;/script&gt;' in html or '&lt;script&gt;' in html
    assert '<img src=x onerror=alert(1)>' not in html


def test_compiled_css_exists_and_no_external_cdns(client):
    """Verify compiled CSS file exists locally and rendered pages do not call external CDNs."""
    # 1. Local compiled CSS file exists
    css_file = Path("app/static/css/app.css")
    assert css_file.exists()
    assert css_file.stat().st_size > 5000  # verified substantial Tailwind build

    # 2. Rendered pages have no external cdn/http references for scripts/styles
    for path in ["/", "/ward"]:
        res = client.get(path)
        html = res.get_data(as_text=True)

        # Check for external stylesheets or script tags
        external_links = re.findall(r'<link[^>]+href=["\'](http[s]?://[^"\']+)["\']', html)
        assert len(external_links) == 0, f"Found external links on {path}: {external_links}"

        external_scripts = re.findall(r'<script[^>]+src=["\'](http[s]?://[^"\']+)["\']', html)
        assert len(external_scripts) == 0, f"Found external scripts on {path}: {external_scripts}"


def test_cache_control_on_ward(client):
    """Personalized ward view must include no-store Cache-Control header."""
    res = client.get("/ward")
    assert res.status_code == 200
    cache_control = res.headers.get("Cache-Control", "")
    assert "no-store" in cache_control
