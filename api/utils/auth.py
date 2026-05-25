"""API Key authentication middleware"""
import os
from fastapi import Header, HTTPException, Request
from typing import Optional


# Load valid API keys from environment
VALID_KEYS: set[str] = set()
_keys = os.getenv("API_KEYS", "sk-test-1234")
for k in _keys.split(","):
    k = k.strip()
    if k:
        VALID_KEYS.add(k)


async def verify_api_key(request: Request):
    """Verify API key from Authorization header or query param."""
    # Skip auth for health check
    if request.url.path == "/health":
        return True

    # Allow if no keys configured (dev mode)
    if not VALID_KEYS:
        return True

    auth_header = request.headers.get("Authorization", "")
    api_key = ""

    if auth_header.startswith("Bearer "):
        api_key = auth_header[7:]
    else:
        # Also check query param
        api_key = request.query_params.get("api_key", "")

    if api_key not in VALID_KEYS:
        raise HTTPException(status_code=401, detail="Invalid or missing API key")

    return True
