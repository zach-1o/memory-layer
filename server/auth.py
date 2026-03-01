"""
Auth — API key validation and rate limiting.

Auth flow per agent.md:
  1. Every MCP request arrives with X-Api-Key header
  2. auth.py validates the key → resolves to a user_id
  3. Rate limiting enforced per API key (sliding window)
"""

import os
import time
import hashlib
import sqlite3
import logging
from pathlib import Path
from dataclasses import dataclass
from collections import defaultdict

from fastapi import Request, HTTPException
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

DB_ROOT = Path(os.getenv("DB_ROOT", "./db"))
RATE_LIMIT_RPM = int(os.getenv("RATE_LIMIT_RPM", "60"))

# In-memory API key store (MVP — replace with DB in production)
# Format: { "skp_xxx": { "user_id": "...", "name": "..." } }
_api_keys: dict[str, dict] = {}

# Rate limiting: sliding window per API key
_rate_windows: dict[str, list[float]] = defaultdict(list)


@dataclass
class AuthResult:
    """Result of API key validation."""
    user_id: str
    key_name: str
    is_valid: bool = True


def _init_keys_db() -> None:
    """Initialize the API keys database if it doesn't exist."""
    DB_ROOT.mkdir(parents=True, exist_ok=True)
    db_path = DB_ROOT / "_keys.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS api_keys (
            key_hash    TEXT PRIMARY KEY,
            user_id     TEXT NOT NULL,
            key_name    TEXT NOT NULL,
            key_prefix  TEXT NOT NULL,
            created_at  TEXT NOT NULL,
            revoked_at  TEXT DEFAULT NULL
        )
    """)
    conn.commit()
    conn.close()


def register_api_key(api_key: str, user_id: str, key_name: str = "default") -> str:
    """
    Register a new API key (MVP helper).
    In production, this would be behind an admin API.
    Returns the key hash.
    """
    _init_keys_db()
    key_hash = hashlib.sha256(api_key.encode()).hexdigest()
    prefix = api_key[:8] + "..."

    db_path = DB_ROOT / "_keys.sqlite"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            """
            INSERT OR REPLACE INTO api_keys (key_hash, user_id, key_name, key_prefix, created_at)
            VALUES (?, ?, ?, ?, datetime('now'))
            """,
            (key_hash, user_id, key_name, prefix),
        )
        conn.commit()
    finally:
        conn.close()

    # Also cache in memory
    _api_keys[key_hash] = {"user_id": user_id, "name": key_name}
    logger.info(f"Registered API key {prefix} for user {user_id}")
    return key_hash


def validate_api_key(api_key: str) -> AuthResult:
    """
    Validate an API key and return the associated user_id.
    Raises HTTPException if invalid.
    """
    if not api_key:
        raise HTTPException(status_code=401, detail="Missing API key")

    key_hash = hashlib.sha256(api_key.encode()).hexdigest()

    # Check in-memory cache first
    if key_hash in _api_keys:
        info = _api_keys[key_hash]
        return AuthResult(user_id=info["user_id"], key_name=info["name"])

    # Fall back to DB lookup
    _init_keys_db()
    db_path = DB_ROOT / "_keys.sqlite"
    conn = sqlite3.connect(str(db_path))
    try:
        row = conn.execute(
            "SELECT user_id, key_name FROM api_keys WHERE key_hash = ? AND revoked_at IS NULL",
            (key_hash,),
        ).fetchone()
    finally:
        conn.close()

    if row is None:
        raise HTTPException(status_code=401, detail="Invalid API key")

    # Cache it
    _api_keys[key_hash] = {"user_id": row[0], "name": row[1]}
    return AuthResult(user_id=row[0], key_name=row[1])


def check_rate_limit(api_key: str) -> None:
    """
    Enforce rate limiting (sliding window, per API key).
    Raises HTTPException if limit exceeded.
    """
    now = time.time()
    window = _rate_windows[api_key]

    # Remove entries older than 60 seconds
    window[:] = [t for t in window if now - t < 60]

    if len(window) >= RATE_LIMIT_RPM:
        raise HTTPException(
            status_code=429,
            detail=f"Rate limit exceeded ({RATE_LIMIT_RPM} requests/minute)",
        )

    window.append(now)


async def authenticate_request(request: Request) -> AuthResult:
    """
    FastAPI dependency: extract and validate X-Api-Key header.
    Also enforces rate limiting.
    """
    api_key = request.headers.get("X-Api-Key", "")
    auth_result = validate_api_key(api_key)
    check_rate_limit(api_key)
    return auth_result
