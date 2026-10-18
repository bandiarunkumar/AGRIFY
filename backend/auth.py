"""
AGRIFY — Farm Ownership & Access Authorization
Module: backend/auth.py

Provides cryptographic token generation, secure hashing (SHA-256 with salt),
and request authorization extraction for farm-level access control.
Ensures strict multi-tenant isolation so farm profiles, historical analyses,
and action plans are accessible only to authorized owners.
"""

import hashlib
import hmac
import os
import secrets
import uuid
from typing import Optional, Tuple
from flask import request


def generate_owner_token() -> str:
    """Generate a high-entropy URL-safe ownership token (UUID4 + secure random)."""
    return f"agf_{uuid.uuid4().hex}_{secrets.token_hex(8)}"


def hash_owner_token(token: str, salt: Optional[str] = None) -> str:
    """
    Hash an owner token with a secret salt for database storage.
    Plaintext tokens are never stored in the database.
    """
    if not token or not isinstance(token, str):
        return ""
    app_secret = salt or os.getenv("SECRET_KEY", "agrify-default-secret-salt-key")
    return hmac.new(app_secret.encode("utf-8"), token.strip().encode("utf-8"), hashlib.sha256).hexdigest()


def verify_owner_token(arg1: str, arg2: str, salt: Optional[str] = None) -> bool:
    """
    Constant-time verification of a provided token against the stored hash.
    Resilient to either (provided_token, stored_hash) or (stored_hash, provided_token) call order.
    """
    if not arg1 or not arg2 or not isinstance(arg1, str) or not isinstance(arg2, str):
        return False
    token1 = arg1.strip()
    token2 = arg2.strip()
    if not token1 or not token2:
        return False

    # Check if arg1 is token and arg2 is hash
    hash1 = hash_owner_token(token1, salt)
    if hmac.compare_digest(hash1, token2):
        return True

    # Check if arg2 is token and arg1 is hash
    hash2 = hash_owner_token(token2, salt)
    return hmac.compare_digest(hash2, token1)



def extract_token_from_request(req) -> Optional[str]:
    """
    Extract an owner token from either:
    1. 'X-Farm-Token' custom header
    2. 'Authorization: Bearer <token>' standard header
    3. Query parameter 'token' (fallback for secure downloads)
    """
    # 1. Custom header
    custom_header = req.headers.get("X-Farm-Token")
    if custom_header and custom_header.strip():
        return custom_header.strip()

    # 2. Authorization header
    auth_header = req.headers.get("Authorization")
    if auth_header and auth_header.strip():
        parts = auth_header.strip().split()
        if len(parts) == 2 and parts[0].lower() == "bearer":
            return parts[1].strip()

    # 3. Query string fallback
    query_token = req.args.get("token")
    if query_token and query_token.strip():
        return query_token.strip()

    return None


extract_bearer_or_header_token = extract_token_from_request
