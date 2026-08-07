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
        policy = headers["content-security-policy"]
        assert "default-src 'self'" in policy
        assert "object-src 'none'" in policy
        assert "frame-ancestors 'none'" in policy
        assert "script-src 'self'" in policy


def test_markup_and_scripts_revalidate_so_a_deploy_cannot_serve_a_stale_mix(tmp_path) -> None:
    """A cached script running against newer markup leaves the controls silently dead."""
    client = TestClient(create_app(tmp_path))
    for path in ("/", "/runs", "/static/experience.js", "/static/experience.css"):
        cache_control = client.get(path).headers.get("cache-control", "")
        assert "no-cache" in cache_control, f"{path} may be cached without revalidation"
        assert "must-revalidate" in cache_control


def test_json_endpoints_are_not_forced_to_revalidate(tmp_path) -> None:
    assert "cache-control" not in client_headers(tmp_path, "/api/assessment")
    assert "cache-control" not in client_headers(tmp_path, "/health")


def client_headers(tmp_path, path: str):
    return TestClient(create_app(tmp_path)).get(path).headers


def test_policy_endpoint_feeds_the_browser_measurement_its_thresholds(tmp_path) -> None:
    """The in-browser widget must read policy from the server, never hardcode it."""
    payload = TestClient(create_app(tmp_path)).get("/api/policy").json()
    assert payload["minimum_k"] >= 2
    assert payload["raw_person_rows_allowed"] == 0
    for field in ("critical_minimum_k", "critical_percent_below_5", "maximum_percent_below_k5"):
        assert field in payload, f"{field} is needed to reproduce the CLI verdict in the browser"
