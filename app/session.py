"""
Server-issued session tokens.

Closes the unauthenticated-session-id hole: until this module landed, any client
could send any session_id and read/write that profile. Now the session_id only
counts if it arrives inside a token signed by the server's SESSION_SECRET.

Token format: "<session_id>.<hmac_hex>" where hmac_hex = HMAC-SHA256(secret, session_id).
"""
from __future__ import annotations

import hmac
import os
import uuid
from hashlib import sha256
from typing import Optional


class SessionConfigError(RuntimeError):
    """Raised at startup if SESSION_SECRET is missing or trivially weak."""


def _secret() -> bytes:
    raw = os.environ.get("SESSION_SECRET")
    if not raw or len(raw) < 32:
        raise SessionConfigError(
            "SESSION_SECRET must be set and at least 32 chars. "
            "Generate one with: python -c 'import secrets; print(secrets.token_hex(32))'"
        )
    return raw.encode("utf-8")


def _sign(session_id: str) -> str:
    mac = hmac.new(_secret(), session_id.encode("utf-8"), sha256).hexdigest()
    return f"{session_id}.{mac}"


def new_session() -> tuple[str, str]:
    """Mint a fresh session_id + signed token."""
    session_id = str(uuid.uuid4())
    return session_id, _sign(session_id)


def verify(token: Optional[str]) -> Optional[str]:
    """Return the session_id iff the token's signature is valid; else None."""
    if not token or "." not in token:
        return None
    session_id, _, mac = token.rpartition(".")
    if not session_id or not mac:
        return None
    expected = hmac.new(_secret(), session_id.encode("utf-8"), sha256).hexdigest()
    if not hmac.compare_digest(mac, expected):
        return None
    return session_id
