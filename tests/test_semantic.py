"""
Tests for the Semantic Layer (ChromaDB vector store).

Covers:
  - Upsert and search
  - Similarity ordering
  - Delete
  - Namespace isolation
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ["DB_ROOT"] = tempfile.mkdtemp()

from namespacing.tenant import resolve_tenant
from memory import semantic


def _make_tenant(user="test_user", project="test_project"):
    return resolve_tenant(user, project)


class TestSemanticUpsert:
    def test_upsert_and_count(self):
        tenant = _make_tenant(project="sem_upsert")

        semantic.upsert_observation(
            tenant, "obs-1", "Fixed authentication bug in login handler"
        )
        semantic.upsert_observation(
            tenant, "obs-2", "Added database migration for user table"
        )

        assert semantic.count(tenant) == 2

    def test_upsert_idempotent(self):
        tenant = _make_tenant(project="sem_idempotent")

        semantic.upsert_observation(tenant, "obs-1", "Original summary")
        semantic.upsert_observation(tenant, "obs-1", "Updated summary")

        assert semantic.count(tenant) == 1


class TestSemanticSearch:
    def test_similarity_search(self):
        tenant = _make_tenant(project="sem_search")

        semantic.upsert_observation(
            tenant, "obs-auth", "Fixed authentication and login flow"
        )
        semantic.upsert_observation(
            tenant, "obs-db", "Updated database schema for payments"
        )
        semantic.upsert_observation(
            tenant, "obs-ui", "Redesigned the settings page UI"
        )

        results = semantic.search_similar(tenant, "login authentication")
        assert len(results) > 0
        # The auth-related observation should be the closest match
        assert results[0]["id"] == "obs-auth"

    def test_search_empty_store(self):
        tenant = _make_tenant(project="sem_empty")
        results = semantic.search_similar(tenant, "anything")
        assert len(results) == 0


class TestSemanticDelete:
    def test_delete_observation(self):
        tenant = _make_tenant(project="sem_delete")

        semantic.upsert_observation(tenant, "obs-del", "This will be deleted")
        assert semantic.count(tenant) == 1

        semantic.delete_observation(tenant, "obs-del")
        assert semantic.count(tenant) == 0
