"""
Tests for the Episodic Log (SQLite + FTS5).

Covers:
  - Write and read observations
  - FTS5 full-text search
  - Timeline retrieval
  - Soft invalidation (no hard deletes)
  - Namespace isolation
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Use temp DB root for tests
os.environ["DB_ROOT"] = tempfile.mkdtemp()

from namespacing.tenant import resolve_tenant
from memory import episodic


def _make_tenant(user="test_user", project="test_project"):
    return resolve_tenant(user, project)


class TestEpisodicWrite:
    def test_write_and_read(self):
        tenant = _make_tenant()
        episodic.initialize(tenant)

        obs_id = episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="file_read",
            raw_content="Read file main.py to understand entrypoint",
            entities=["main.py"],
        )

        assert obs_id is not None
        obs = episodic.get_observation(tenant, obs_id)
        assert obs is not None
        assert obs["action_type"] == "file_read"
        assert obs["raw_content"] == "Read file main.py to understand entrypoint"
        assert obs["invalidated_at"] is None

    def test_write_multiple(self):
        tenant = _make_tenant(project="multi_write")
        episodic.initialize(tenant)

        ids = []
        for i in range(5):
            obs_id = episodic.write_observation(
                tenant=tenant,
                session_id="sess-1",
                action_type="observation",
                raw_content=f"Observation number {i}",
            )
            ids.append(obs_id)

        assert len(set(ids)) == 5  # All unique IDs


class TestEpisodicSearch:
    def test_fts_search(self):
        tenant = _make_tenant(project="fts_test")
        episodic.initialize(tenant)

        episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="file_edit",
            raw_content="Fixed authentication bug in login handler",
            entities=["login.py", "auth_handler"],
        )
        episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="file_read",
            raw_content="Read database migration scripts",
            entities=["migrations/"],
        )

        results = episodic.search_fts(tenant, "authentication")
        assert len(results) >= 1
        assert any("authentication" in r.get("snippet", "").lower() for r in results)

    def test_fts_no_results(self):
        tenant = _make_tenant(project="fts_empty")
        episodic.initialize(tenant)

        results = episodic.search_fts(tenant, "nonexistent_query_xyz")
        assert len(results) == 0


class TestEpisodicTimeline:
    def test_timeline(self):
        tenant = _make_tenant(project="timeline_test")
        episodic.initialize(tenant)

        ids = []
        for i in range(10):
            obs_id = episodic.write_observation(
                tenant=tenant,
                session_id="sess-1",
                action_type="observation",
                raw_content=f"Event {i} in the session",
            )
            ids.append(obs_id)

        timeline = episodic.get_timeline(tenant, ids[5], window=3)
        assert len(timeline) > 0
        assert len(timeline) <= 7  # 3 before + target + 3 after


class TestEpisodicInvalidation:
    def test_soft_invalidate(self):
        tenant = _make_tenant(project="invalidate_test")
        episodic.initialize(tenant)

        obs_id = episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="observation",
            raw_content="This will be invalidated",
        )

        result = episodic.invalidate(tenant, obs_id)
        assert result is True

        obs = episodic.get_observation(tenant, obs_id)
        assert obs is not None  # NOT deleted
        assert obs["invalidated_at"] is not None  # But marked as invalidated

    def test_invalidated_excluded_from_search(self):
        tenant = _make_tenant(project="invalidate_search")
        episodic.initialize(tenant)

        obs_id = episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="observation",
            raw_content="Unique searchable term xylophone",
        )

        # Should be findable before invalidation
        results = episodic.search_fts(tenant, "xylophone")
        assert len(results) >= 1

        episodic.invalidate(tenant, obs_id)

        # Should be excluded after invalidation
        results = episodic.search_fts(tenant, "xylophone")
        assert len(results) == 0


class TestEpisodicCompression:
    def test_uncompressed_batch(self):
        tenant = _make_tenant(project="compression_test")
        episodic.initialize(tenant)

        for i in range(3):
            episodic.write_observation(
                tenant=tenant,
                session_id="sess-1",
                action_type="observation",
                raw_content=f"Uncompressed event {i}",
            )

        uncompressed = episodic.get_uncompressed(tenant, limit=10)
        assert len(uncompressed) == 3

    def test_update_summary(self):
        tenant = _make_tenant(project="summary_test")
        episodic.initialize(tenant)

        obs_id = episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="observation",
            raw_content="A long observation that needs compression",
        )

        episodic.update_summary(tenant, obs_id, "Compressed: observation about compression", 12)

        obs = episodic.get_observation(tenant, obs_id)
        assert obs["compressed_summary"] == "Compressed: observation about compression"
        assert obs["token_count"] == 12
