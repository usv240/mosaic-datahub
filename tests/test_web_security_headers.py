from fastapi.testclient import TestClient

from mosaic.web.complete_app import create_app


def test_browser_security_headers_apply_to_html_and_api(tmp_path) -> None:
    client = TestClient(create_app(tmp_path))
    for path in ("/", "/runs", "/api/assessment", "/health"):
        headers = client.get(path).headers
        assert headers["x-content-type-options"] == "nosniff"
        assert headers["x-frame-options"] == "DENY"
        assert headers["referrer-policy"] == "strict-origin-when-cross-origin"
        assert headers["permissions-policy"] == "camera=(), microphone=(), geolocation=()"
