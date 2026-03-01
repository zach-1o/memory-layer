"""
Episodic Log — SQLite + FTS5 append-only event diary.

Schema per agent.md:
  id, project_id, session_id, timestamp, action_type,
  raw_content, compressed_summary, token_count,
  entities_mentioned, invalidated_at

Rules:
  - NEVER delete rows. Use invalidated_at for soft-deprecation.
  - FTS5 index on raw_content + compressed_summary.
  - Every read/write MUST be scoped to a tenant.
"""

import sqlite3
import uuid
import json
from datetime import datetime, timezone
from typing import Optional

from namespacing.tenant import Tenant


def _get_connection(tenant: Tenant) -> sqlite3.Connection:
    """Get a SQLite connection for the tenant's episodic database."""
    db_path = tenant.episodic_db_path
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    return conn


def initialize(tenant: Tenant) -> None:
    """Create the episodic log tables and FTS5 index for a tenant."""
    conn = _get_connection(tenant)
    try:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS observations (
                id              TEXT PRIMARY KEY,
                project_id      TEXT NOT NULL,
                session_id      TEXT NOT NULL,
                timestamp       TEXT NOT NULL,
                action_type     TEXT NOT NULL,
                raw_content     TEXT NOT NULL,
                compressed_summary TEXT DEFAULT '',
                token_count     INTEGER DEFAULT 0,
                entities_mentioned TEXT DEFAULT '[]',
                invalidated_at  TEXT DEFAULT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_obs_timestamp
                ON observations(timestamp);

            CREATE INDEX IF NOT EXISTS idx_obs_session
                ON observations(session_id);

            CREATE INDEX IF NOT EXISTS idx_obs_action_type
                ON observations(action_type);

            CREATE VIRTUAL TABLE IF NOT EXISTS observations_fts USING fts5(
                raw_content,
                compressed_summary,
                content='observations',
                content_rowid='rowid'
            );

            -- Triggers to keep FTS index in sync
            CREATE TRIGGER IF NOT EXISTS obs_ai AFTER INSERT ON observations BEGIN
                INSERT INTO observations_fts(rowid, raw_content, compressed_summary)
                VALUES (new.rowid, new.raw_content, new.compressed_summary);
            END;

            CREATE TRIGGER IF NOT EXISTS obs_au AFTER UPDATE ON observations BEGIN
                INSERT INTO observations_fts(observations_fts, rowid, raw_content, compressed_summary)
                VALUES ('delete', old.rowid, old.raw_content, old.compressed_summary);
                INSERT INTO observations_fts(rowid, raw_content, compressed_summary)
                VALUES (new.rowid, new.raw_content, new.compressed_summary);
            END;
        """)
        conn.commit()
    finally:
        conn.close()


def write_observation(
    tenant: Tenant,
    session_id: str,
    action_type: str,
    raw_content: str,
    entities: list[str] | None = None,
    compressed_summary: str = "",
    token_count: int = 0,
) -> str:
    """
    Append a new observation to the episodic log.
    Returns the generated observation ID.
    """
    obs_id = str(uuid.uuid4())
    now = datetime.now(timezone.utc).isoformat()
    entities_json = json.dumps(entities or [])

    conn = _get_connection(tenant)
    try:
        conn.execute(
            """
            INSERT INTO observations
                (id, project_id, session_id, timestamp, action_type,
                 raw_content, compressed_summary, token_count, entities_mentioned)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                obs_id,
                tenant.project_id,
                session_id,
                now,
                action_type,
                raw_content,
                compressed_summary,
                token_count,
                entities_json,
            ),
        )
        conn.commit()
    finally:
        conn.close()

    return obs_id


def get_observation(tenant: Tenant, obs_id: str) -> Optional[dict]:
    """Retrieve a single observation by ID."""
    conn = _get_connection(tenant)
    try:
        row = conn.execute(
            "SELECT * FROM observations WHERE id = ?", (obs_id,)
        ).fetchone()
        if row is None:
            return None
        return dict(row)
    finally:
        conn.close()


def search_fts(tenant: Tenant, query: str, limit: int = 20) -> list[dict]:
    """
    Full-text search across raw_content and compressed_summary.
    Returns lightweight results: id, action_type, timestamp, snippet.
    """
    conn = _get_connection(tenant)
    try:
        rows = conn.execute(
            """
            SELECT o.id, o.action_type, o.timestamp,
                   snippet(observations_fts, 0, '>>>', '<<<', '...', 32) as snippet,
                   o.token_count
            FROM observations_fts fts
            JOIN observations o ON o.rowid = fts.rowid
            WHERE observations_fts MATCH ?
              AND o.invalidated_at IS NULL
            ORDER BY rank
            LIMIT ?
            """,
            (query, limit),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_timeline(
    tenant: Tenant, obs_id: str, window: int = 5
) -> list[dict]:
    """
    Get observations before and after a specific observation (by timestamp).
    Returns `window` items on each side, ordered chronologically.
    """
    conn = _get_connection(tenant)
    try:
        # Get the target observation's timestamp
        target = conn.execute(
            "SELECT timestamp FROM observations WHERE id = ?", (obs_id,)
        ).fetchone()
        if target is None:
            return []

        ts = target["timestamp"]

        # Get window items before and after
        rows = conn.execute(
            """
            SELECT id, session_id, timestamp, action_type,
                   compressed_summary, token_count, entities_mentioned
            FROM observations
            WHERE invalidated_at IS NULL
            ORDER BY ABS(julianday(timestamp) - julianday(?))
            LIMIT ?
            """,
            (ts, window * 2 + 1),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def get_recent(tenant: Tenant, limit: int = 20) -> list[dict]:
    """Get the most recent observations."""
    conn = _get_connection(tenant)
    try:
        rows = conn.execute(
            """
            SELECT id, session_id, timestamp, action_type,
                   compressed_summary, token_count, entities_mentioned
            FROM observations
            WHERE invalidated_at IS NULL
            ORDER BY timestamp DESC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def invalidate(tenant: Tenant, obs_id: str) -> bool:
    """Soft-invalidate an observation. Never hard-delete."""
    now = datetime.now(timezone.utc).isoformat()
    conn = _get_connection(tenant)
    try:
        cursor = conn.execute(
            "UPDATE observations SET invalidated_at = ? WHERE id = ? AND invalidated_at IS NULL",
            (now, obs_id),
        )
        conn.commit()
        return cursor.rowcount > 0
    finally:
        conn.close()


def get_uncompressed(tenant: Tenant, limit: int = 5) -> list[dict]:
    """Get observations that haven't been compressed yet (for batch compression)."""
    conn = _get_connection(tenant)
    try:
        rows = conn.execute(
            """
            SELECT id, raw_content, entities_mentioned
            FROM observations
            WHERE compressed_summary = '' AND invalidated_at IS NULL
            ORDER BY timestamp ASC
            LIMIT ?
            """,
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


def update_summary(tenant: Tenant, obs_id: str, summary: str, token_count: int) -> None:
    """Update the compressed summary for an observation (called by compression worker)."""
    conn = _get_connection(tenant)
    try:
        conn.execute(
            "UPDATE observations SET compressed_summary = ?, token_count = ? WHERE id = ?",
            (summary, token_count, obs_id),
        )
        conn.commit()
    finally:
        conn.close()
