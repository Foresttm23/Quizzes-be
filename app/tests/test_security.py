from datetime import timedelta

import pytest

from app.core.exceptions import InvalidJWTToken
from app.core.security import (
    verify_token_local,
    verify_token_auth0,
)
from app.utils.jwt_utils import create_access_token


# Can be modified later, if more fields added
def get_test_access_token(sub="test@example.com", exp_delta=60):
    expire = timedelta(seconds=exp_delta)
    data = {"sub": sub}
    token = create_access_token(data=data, expires_delta=expire)
    return token


def test_verify_token_local_success():
    token = get_test_access_token()
    result = verify_token_local(token)
    assert result["email"] == "test@example.com"


def test_verify_token_local_expired():
    token = get_test_access_token(exp_delta=-10)  # already expired
    with pytest.raises(InvalidJWTToken):
        verify_token_local(token)


def test_verify_token_local_invalid():
    token = "not_a_real_token"
    with pytest.raises(InvalidJWTToken):
        verify_token_local(token)


def test_verify_token_auth0_success(monkeypatch):
    fake_token = "fake_auth0_token"

    monkeypatch.setattr(
        "app.core.security.jws.get_unverified_header",
        lambda token: {"kid": "abc123"}
    )

    monkeypatch.setattr(
        "app.core.security.find_public_key",
        lambda kid: {"kty": "RSA", "kid": kid, "alg": "RS256"}
    )

    monkeypatch.setattr(
        "app.core.security.jwt.decode",
        lambda token, key, audience, algorithms: {"email": "auth0@example.com"}
    )

    result = verify_token_auth0(fake_token)
    assert result["email"] == "auth0@example.com"


def test_verify_token_auth0_invalid(monkeypatch):
    fake_token = "fake_auth0_token"

    monkeypatch.setattr(
        "app.core.security.jws.get_unverified_header",
        lambda token: {"kid": "abc123"}
    )

    monkeypatch.setattr(
        "app.core.security.find_public_key",
        lambda kid: None
    )

    with pytest.raises(InvalidJWTToken):
        verify_token_auth0(fake_token)
