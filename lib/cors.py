import os


DEFAULT_ALLOWED_ORIGINS = frozenset({
    "https://my.citizeninfra.org",
    "http://localhost:5173",
    "http://127.0.0.1:5173",
})


def _allowed_origins():
    configured = {
        origin.strip()
        for origin in os.environ.get("CORS_ALLOWED_ORIGINS", "").split(",")
        if origin.strip()
    }
    return DEFAULT_ALLOWED_ORIGINS | configured


def send_cors_headers(response):
    origin = response.headers.get("Origin")
    if not origin:
        return
    requested_headers = response.headers.get("Access-Control-Request-Headers", "")
    carries_authorization = bool(response.headers.get("Authorization")) or any(
        header.strip().lower() == "authorization"
        for header in requested_headers.split(",")
    )
    if origin in _allowed_origins():
        response.send_header("Access-Control-Allow-Origin", origin)
        response.send_header("Vary", "Origin")
    elif not carries_authorization:
        response.send_header("Access-Control-Allow-Origin", "*")


def handle_options(response):
    response.send_response(204)
    send_cors_headers(response)
    response.send_header("Access-Control-Allow-Methods", "GET, OPTIONS")
    response.send_header("Access-Control-Allow-Headers", "Authorization, Content-Type")
    response.send_header("Access-Control-Max-Age", "86400")
    response.end_headers()
