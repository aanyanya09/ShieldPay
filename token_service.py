"""
token_service.py - Signed single-use 5-minute token for ShieldPay (§4, B2).
HMAC-SHA256 signature with constant-time verification.
Enforces a 32-byte minimum secret requirement.
"""

import os
import hmac
import hashlib
import json
import base64
import time
import uuid
from typing import Dict, Any, Tuple, Optional


class TokenError(Exception):
    pass


class TokenExpiredError(TokenError):
    pass


class TokenInvalidError(TokenError):
    pass


class TokenSecurityError(TokenError):
    pass


def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode("utf-8").rstrip("=")


def _base64url_decode(data: str) -> bytes:
    padding = 4 - (len(data) % 4)
    if padding and padding != 4:
        data += "=" * padding
    return base64.urlsafe_b64decode(data.encode("utf-8"))


def validate_secret_strength(secret: str) -> None:
    """Ensure secret is at least 32 bytes (256 bits) per B2 / B6."""
    if not secret or len(secret.encode("utf-8")) < 32:
        raise TokenSecurityError("Token secret must be at least 32 bytes (256 bits).")


def generate_capture_token(
    order_id: str,
    amount_cents: int,
    currency: str,
    seller_email: str,
    outcome: str,
    secret: str,
    ttl_seconds: int = 300
) -> Tuple[str, str, int]:
    """
    Generate a signed single-use 5-minute token (§4, B2).
    Returns (token_string, jti, expiry_timestamp).
    """
    validate_secret_strength(secret)

    now = int(time.time())
    exp = now + ttl_seconds
    jti = str(uuid.uuid4())

    header = {"alg": "HS256", "typ": "JWT"}
    payload = {
        "order_id": order_id,
        "amount_cents": amount_cents,
        "currency": currency,
        "seller_email": seller_email,
        "outcome": outcome,
        "iat": now,
        "exp": exp,
        "jti": jti
    }

    header_bytes = json.dumps(header, separators=(",", ":")).encode("utf-8")
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")

    header_b64 = _base64url_encode(header_bytes)
    payload_b64 = _base64url_encode(payload_bytes)

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    signature = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    sig_b64 = _base64url_encode(signature)

    token = f"{header_b64}.{payload_b64}.{sig_b64}"
    return token, jti, exp


def verify_capture_token(
    token: str,
    secret: str,
    current_time: Optional[int] = None
) -> Dict[str, Any]:
    """
    Verify signature, structure, and expiration of the signed token.
    Raises TokenInvalidError or TokenExpiredError on failure.
    """
    validate_secret_strength(secret)

    if not token or not isinstance(token, str):
        raise TokenInvalidError("Malformed token: empty or not a string")

    parts = token.split(".")
    if len(parts) != 3:
        raise TokenInvalidError("Malformed token: must have header, payload, and signature")

    header_b64, payload_b64, sig_b64 = parts

    signing_input = f"{header_b64}.{payload_b64}".encode("utf-8")
    expected_sig = hmac.new(secret.encode("utf-8"), signing_input, hashlib.sha256).digest()
    expected_sig_b64 = _base64url_encode(expected_sig)

    if not hmac.compare_digest(sig_b64.encode("utf-8"), expected_sig_b64.encode("utf-8")):
        raise TokenInvalidError("Invalid token signature")

    try:
        header = json.loads(_base64url_decode(header_b64).decode("utf-8"))
    except Exception:
        raise TokenInvalidError("Cannot decode token header")
    if header.get("alg") != "HS256":
        raise TokenInvalidError("Unsupported token algorithm")

    try:
        payload_bytes = _base64url_decode(payload_b64)
        payload = json.loads(payload_bytes.decode("utf-8"))
    except Exception:
        raise TokenInvalidError("Cannot decode token payload:")

    required = ["order_id", "amount_cents", "currency", "seller_email", "outcome", "iat", "exp", "jti"]
    for field in required:
        if field not in payload:
            raise TokenInvalidError(f"Missing required token field: {field}")

    now = int(time.time()) if current_time is None else current_time
    if payload["exp"] <= now:
        raise TokenExpiredError(
            f"Token expired at {payload['exp']}, current time is {now}. Check must be re-run."
        )

    return payload
