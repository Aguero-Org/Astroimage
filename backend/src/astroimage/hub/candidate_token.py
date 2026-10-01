from __future__ import annotations

import base64
import hashlib
import hmac
import json
from typing import Any


class InvalidCandidateTokenError(ValueError):
    """Raised when a candidate token signature does not match."""


def sign_candidate_token(payload: dict[str, Any], secret: str) -> str:
    encoded = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode("utf-8")
    body = base64.urlsafe_b64encode(encoded).decode("ascii").rstrip("=")
    signature = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    return f"{body}.{signature}"


def read_candidate_token(token: str, secret: str) -> dict[str, Any]:
    body, separator, signature = token.partition(".")
    if separator == "" or body == "" or signature == "":
        raise InvalidCandidateTokenError("candidate token is malformed")
    expected = hmac.new(secret.encode("utf-8"), body.encode("ascii"), hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected, signature):
        raise InvalidCandidateTokenError("candidate token signature is invalid")
    padding = "=" * (-len(body) % 4)
    try:
        decoded = base64.urlsafe_b64decode(body + padding).decode("utf-8")
        payload = json.loads(decoded)
    except (ValueError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise InvalidCandidateTokenError("candidate token payload is invalid") from exc
    if not isinstance(payload, dict) or "data_uri" not in payload:
        raise InvalidCandidateTokenError("candidate token payload is invalid")
    return payload
