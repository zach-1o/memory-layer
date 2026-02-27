"""
Tenant model: maps (api_key, project_id) → isolated database directory.

Every tenant gets a unique hash-based directory under DB_ROOT containing:
  - episodic.sqlite   (append-only event log)
  - chroma/           (vector embeddings)
  - graph.json        (knowledge graph)
"""

import hashlib
import os
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime, timezone

from dotenv import load_dotenv

load_dotenv()

DB_ROOT = Path(os.getenv("DB_ROOT", "./db"))


@dataclass
class Tenant:
    """Represents an isolated project namespace."""

    user_id: str
    project_id: str
    tenant_hash: str = field(init=False)
    db_path: Path = field(init=False)
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def __post_init__(self):
        # Deterministic hash from (user_id, project_id) — same inputs always
        # produce the same directory, ensuring idempotent namespace resolution.
        raw = f"{self.user_id}::{self.project_id}"
        self.tenant_hash = hashlib.sha256(raw.encode()).hexdigest()[:16]
        self.db_path = DB_ROOT / self.tenant_hash

    def ensure_dirs(self) -> Path:
        """Create tenant database directories if they don't exist."""
        self.db_path.mkdir(parents=True, exist_ok=True)
        (self.db_path / "chroma").mkdir(exist_ok=True)
        return self.db_path

    @property
    def episodic_db_path(self) -> Path:
        return self.db_path / "episodic.sqlite"

    @property
    def chroma_path(self) -> Path:
        return self.db_path / "chroma"

    @property
    def graph_path(self) -> Path:
        return self.db_path / "graph.json"

    def __repr__(self) -> str:
        return f"Tenant(user={self.user_id!r}, project={self.project_id!r}, hash={self.tenant_hash})"


def resolve_tenant(user_id: str, project_id: str) -> Tenant:
    """
    Resolve a (user_id, project_id) pair to an isolated Tenant.
    Creates the tenant directory structure on first access.
    """
    tenant = Tenant(user_id=user_id, project_id=project_id)
    tenant.ensure_dirs()
    return tenant
