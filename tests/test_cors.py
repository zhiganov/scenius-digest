import io

import pytest

from api import events, groups, links
from lib import config, cors


ALLOWED_ORIGIN = "https://my.citizeninfra.org"


def _handler(handler_class, origin=ALLOWED_ORIGIN, request_headers=None):
    instance = handler_class.__new__(handler_class)
    instance.headers = {"Origin": origin, **(request_headers or {})}
    instance.client_address = ("127.0.0.1", 12345)
    instance.request_version = "HTTP/1.1"
    instance.requestline = "OPTIONS /api/test HTTP/1.1"
    instance.rfile = io.BytesIO()
    instance.wfile = io.BytesIO()
    return instance


@pytest.mark.parametrize("handler_class", [groups.handler, links.handler, events.handler])
def test_browser_read_endpoints_accept_authorization_preflight(handler_class):
    instance = _handler(handler_class)

    instance.do_OPTIONS()

    response = instance.wfile.getvalue().decode()
    assert response.splitlines()[0].endswith("204 No Content")
    assert f"Access-Control-Allow-Origin: {ALLOWED_ORIGIN}" in response
    assert "Access-Control-Allow-Methods: GET, OPTIONS" in response
    assert "Access-Control-Allow-Headers: Authorization, Content-Type" in response


def test_unknown_origin_cannot_read_authenticated_responses():
    instance = _handler(
        groups.handler,
        "https://example.com",
        {"Access-Control-Request-Headers": "authorization"},
    )

    instance.do_OPTIONS()

    response = instance.wfile.getvalue().decode()
    assert "Access-Control-Allow-Origin" not in response


def test_unknown_origin_can_read_anonymous_public_responses():
    instance = _handler(groups.handler, "https://example.com")
    instance.requestline = "GET /api/groups HTTP/1.1"

    cors.send_cors_headers(instance)

    headers = b"".join(instance._headers_buffer).decode()
    assert "Access-Control-Allow-Origin: *" in headers


def test_groups_get_allows_production_web_origin(monkeypatch):
    monkeypatch.setattr(config, "MONITORED_GROUPS", {
        "cibc": {"name": "Citizen Infra Builders", "visibility": "public"},
    })
    instance = _handler(groups.handler)
    instance.requestline = "GET /api/groups HTTP/1.1"

    instance.do_GET()

    response = instance.wfile.getvalue().decode()
    assert response.splitlines()[0].endswith("200 OK")
    assert f"Access-Control-Allow-Origin: {ALLOWED_ORIGIN}" in response


@pytest.mark.parametrize(
    "origin",
    ["http://localhost:5173", "http://127.0.0.1:5173"],
)
def test_local_web_development_origins_are_allowed(origin):
    instance = _handler(groups.handler, origin)

    instance.do_OPTIONS()

    response = instance.wfile.getvalue().decode()
    assert f"Access-Control-Allow-Origin: {origin}" in response


def test_configured_origin_is_allowed(monkeypatch):
    monkeypatch.setenv("CORS_ALLOWED_ORIGINS", "https://preview.example.com")
    instance = _handler(groups.handler, "https://preview.example.com")

    instance.do_OPTIONS()

    response = instance.wfile.getvalue().decode()
    assert "Access-Control-Allow-Origin: https://preview.example.com" in response
