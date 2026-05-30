"""
Tests for app/session.py — the HMAC-signed session token used to close the
unauthenticated session_id hole. Verify the round-trip, reject tampering, and
reject tokens signed with a different secret.
"""
from __future__ import annotations

import pytest

from app import session as session_mod


SECRET_A = "a" * 32 + "_secret_one"
SECRET_B = "b" * 32 + "_secret_two"


def test_sign_then_verify_roundtrips(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", SECRET_A)
    session_id, token = session_mod.new_session()
    assert session_mod.verify(token) == session_id


def test_short_secret_rejected(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", "too_short")
    with pytest.raises(session_mod.SessionConfigError):
        session_mod.new_session()


def test_missing_secret_rejected(monkeypatch):
    monkeypatch.delenv("SESSION_SECRET", raising=False)
    with pytest.raises(session_mod.SessionConfigError):
        session_mod.new_session()


def test_tampered_session_id_rejected(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", SECRET_A)
    session_id, token = session_mod.new_session()
    # Flip a character in the session_id half; the mac no longer matches.
    sid, mac = token.rsplit(".", 1)
    tampered = sid[:-1] + ("A" if sid[-1] != "A" else "B") + "." + mac
    assert session_mod.verify(tampered) is None


def test_tampered_mac_rejected(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", SECRET_A)
    _, token = session_mod.new_session()
    sid, mac = token.rsplit(".", 1)
    tampered = f"{sid}.{mac[:-1]}{'0' if mac[-1] != '0' else '1'}"
    assert session_mod.verify(tampered) is None


def test_token_from_different_secret_rejected(monkeypatch):
    monkeypatch.setenv("SESSION_SECRET", SECRET_A)
    _, token = session_mod.new_session()
    # Same token presented to a server with a rotated secret must not verify.
    monkeypatch.setenv("SESSION_SECRET", SECRET_B)
    assert session_mod.verify(token) is None


@pytest.mark.parametrize("bad", ["", None, "no-dot-in-here", ".only-mac", "sid-only.", "...."])
def test_malformed_tokens_rejected(monkeypatch, bad):
    monkeypatch.setenv("SESSION_SECRET", SECRET_A)
    assert session_mod.verify(bad) is None
