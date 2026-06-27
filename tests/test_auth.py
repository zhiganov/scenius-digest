import time

import jwt
import pytest
from cryptography.hazmat.primitives.asymmetric import ec

from lib import auth


@pytest.fixture
def keypair():
    priv = ec.generate_private_key(ec.SECP256R1())
    return priv, priv.public_key()


@pytest.fixture(autouse=True)
def stub_jwks(monkeypatch, keypair):
    """Point auth's JWKS client at the test public key, no network."""
    _, pub = keypair

    class _Key:
        def __init__(self, key):
            self.key = key

    class _Client:
        def get_signing_key_from_jwt(self, token):
            return _Key(pub)

    monkeypatch.setattr(auth, "_jwks_client", _Client())
    monkeypatch.setattr(auth, "CA_JWKS_URL", "https://ca.test/.well-known/jwks.json")
    monkeypatch.setattr(auth, "CA_ISSUER", None)


def _make_token(priv, *, memberships, exp_offset=900):
    now = int(time.time())
    return jwt.encode(
        {
            "sub": "alice@example.com",
            "memberships": memberships,
            "iat": now,
            "exp": now + exp_offset,
            "iss": "community-admin",
        },
        priv,
        algorithm="ES256",
    )


def test_member_token_returns_community_ids(keypair):
    priv, _ = keypair
    token = _make_token(
        priv,
        memberships=[{"community_id": 7, "role": "member"}, {"community_id": 12, "role": "admin"}],
    )
    assert auth.member_ids_from_request({"Authorization": f"Bearer {token}"}) == {"7", "12"}


def test_non_member_token_returns_empty(keypair):
    priv, _ = keypair
    token = _make_token(priv, memberships=[])
    assert auth.member_ids_from_request({"Authorization": f"Bearer {token}"}) == set()


def test_expired_token_returns_empty(keypair):
    priv, _ = keypair
    token = _make_token(priv, memberships=[{"community_id": 7, "role": "member"}], exp_offset=-3600)
    assert auth.member_ids_from_request({"Authorization": f"Bearer {token}"}) == set()


def test_tampered_signature_returns_empty(keypair):
    priv, _ = keypair
    token = _make_token(priv, memberships=[{"community_id": 7, "role": "member"}])
    head, payload, sig = token.split(".")
    bad_sig = sig[:-1] + ("A" if sig[-1] != "A" else "B")
    tampered = f"{head}.{payload}.{bad_sig}"
    assert auth.member_ids_from_request({"Authorization": f"Bearer {tampered}"}) == set()


def test_missing_token_returns_empty():
    assert auth.member_ids_from_request({}) == set()


def test_malformed_header_returns_empty():
    assert auth.member_ids_from_request({"Authorization": "Basic abc"}) == set()
