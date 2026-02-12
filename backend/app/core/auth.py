import json
import os
import logging
import time
from typing import Optional

import requests
import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer



logger = logging.getLogger(__name__)

_bearer = HTTPBearer(auto_error=False)
_jwks_cache = {
    "keys": None,
    "fetched_at": 0,
}


def _get_supabase_url() -> str:
    supabase_url = os.getenv("SUPABASE_URL")
    if not supabase_url:
        raise HTTPException(status_code=500, detail="SUPABASE_URL is not configured")
    return supabase_url.rstrip("/")


def _get_supabase_api_key() -> str:
    api_key = os.getenv("SUPABASE_ANON_KEY") or os.getenv("SUPABASE_SERVICE_ROLE_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="Supabase API key is not configured")
    return api_key


def _get_jwks() -> list:
    now = time.time()
    if _jwks_cache["keys"] and (now - _jwks_cache["fetched_at"]) < 3600:
        return _jwks_cache["keys"]

    jwks_url = f"{_get_supabase_url()}/auth/v1/.well-known/jwks.json"
    api_key = _get_supabase_api_key()
    response = requests.get(
        jwks_url,
        headers={
            "apikey": api_key,
            "Authorization": f"Bearer {api_key}",
        },
        timeout=5,
    )
    if response.status_code != 200:
        raise HTTPException(status_code=500, detail="Failed to fetch Supabase JWKS")

    jwks = response.json().get("keys", [])
    _jwks_cache["keys"] = jwks
    _jwks_cache["fetched_at"] = now
    return jwks


def _get_public_key(token: str):
    try:
        header = jwt.get_unverified_header(token)
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token header")

    kid = header.get("kid")
    if not kid:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing kid")

    jwks = _get_jwks()
    jwk_set = jwt.PyJWKSet(jwks)
    
    for jwk in jwk_set.keys:
        if jwk.key_id == kid:
            return jwk.key

    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Signing key not found")


def require_auth(credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer)):
    # logger.debug(f"[AUTH] require_auth called")
    # logger.debug(f"[AUTH] Credentials present: {credentials is not None}")
    
    if not credentials or credentials.scheme.lower() != "bearer":
        logger.warning(f"[AUTH] Missing or invalid bearer token")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    token = credentials.credentials
    # logger.debug(f"[AUTH] Token received")
    
    public_key = _get_public_key(token)
    issuer = f"{_get_supabase_url()}/auth/v1"
    audience = os.getenv("SUPABASE_JWT_AUD")

    try:
        # Support both RS256 and ES256
        # Added leeway and disabled iat check because of clock drift on local server
        decode_opts = {
            "algorithms": ["RS256", "ES256"],
            "issuer": issuer,
            "leeway": 300,
            "options": {"verify_iat": False}
        }
        if audience:
            decode_opts["audience"] = audience
            
        payload = jwt.decode(token, public_key, **decode_opts)
        # logger.debug(f"[AUTH] Token validated successfully for user: {payload.get('sub', 'unknown')}")
    except jwt.ExpiredSignatureError:
        logger.info(f"[AUTH] Token expired")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token expired")
    except jwt.InvalidTokenError as e:
        logger.error(f"[AUTH] JWT Validation Error: {e}")
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=f"Invalid token: {str(e)}")

    return payload
