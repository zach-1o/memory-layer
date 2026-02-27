"""
Tests for namespace isolation — zero cross-project memory bleed.

Covers:
  - Two projects with the same user cannot see each other's data
  - Two users with the same project cannot see each other's data
  - Tenant hash determinism
  - Scoping context manager
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ["DB_ROOT"] = tempfile.mkdtemp()

import pytest
from namespacing.tenant import Tenant, resolve_tenant
from namespacing.scoping import tenant_scope, get_current_tenant, ScopeError
from memory import episodic


def _make_tenant(user="test_user", project="test_project"):
    return resolve_tenant(user, project)


class TestTenantIsolation:
    def test_different_projects_different_paths(self):
        t1 = _make_tenant(user="user_a", project="project_1")
        t2 = _make_tenant(user="user_a", project="project_2")

        assert t1.tenant_hash != t2.tenant_hash
        assert t1.db_path != t2.db_path

    def test_different_users_different_paths(self):
        t1 = _make_tenant(user="user_a", project="shared_project")
        t2 = _make_tenant(user="user_b", project="shared_project")

        assert t1.tenant_hash != t2.tenant_hash
        assert t1.db_path != t2.db_path

    def test_same_inputs_same_hash(self):
        t1 = _make_tenant(user="user_a", project="project_1")
        t2 = _make_tenant(user="user_a", project="project_1")

        assert t1.tenant_hash == t2.tenant_hash
        assert t1.db_path == t2.db_path

    def test_cross_project_data_isolation(self):
        """Core test: data written in project A must NOT be visible in project B."""
        tenant_a = _make_tenant(user="user_x", project="project_alpha")
        tenant_b = _make_tenant(user="user_x", project="project_beta")

        episodic.initialize(tenant_a)
        episodic.initialize(tenant_b)

        # Write to project A
        obs_id = episodic.write_observation(
            tenant=tenant_a,
            session_id="sess-1",
            action_type="observation",
            raw_content="Secret data only for project alpha isolation_marker_xyz",
        )

        # Should be visible in project A
        obs = episodic.get_observation(tenant_a, obs_id)
        assert obs is not None

        # Should NOT be visible in project B
        obs_in_b = episodic.get_observation(tenant_b, obs_id)
        assert obs_in_b is None

        # FTS search in project B should NOT find it
        results = episodic.search_fts(tenant_b, "isolation_marker_xyz")
        assert len(results) == 0

    def test_cross_user_data_isolation(self):
        """Data from user A's project must NOT be visible to user B's same-named project."""
        tenant_a = _make_tenant(user="alice", project="myapp")
        tenant_b = _make_tenant(user="bob", project="myapp")

        episodic.initialize(tenant_a)
        episodic.initialize(tenant_b)

        episodic.write_observation(
            tenant=tenant_a,
            session_id="sess-1",
            action_type="observation",
            raw_content="Alice's private data crossuser_marker_abc",
        )

        results = episodic.search_fts(tenant_b, "crossuser_marker_abc")
        assert len(results) == 0


class TestScopingContextManager:
    def test_scope_provides_tenant(self):
        with tenant_scope("user_1", "proj_1") as tenant:
            assert isinstance(tenant, Tenant)
            assert tenant.user_id == "user_1"
            assert tenant.project_id == "proj_1"

    def test_scope_sets_context_var(self):
        with tenant_scope("user_2", "proj_2"):
            current = get_current_tenant()
            assert current.user_id == "user_2"

    def test_scope_error_outside_context(self):
        with pytest.raises(ScopeError):
            get_current_tenant()

    def test_scope_cleanup(self):
        with tenant_scope("user_3", "proj_3"):
            pass

        with pytest.raises(ScopeError):
            get_current_tenant()

    def test_nested_scopes(self):
        with tenant_scope("outer_user", "outer_proj") as outer:
            assert get_current_tenant().project_id == "outer_proj"

            with tenant_scope("inner_user", "inner_proj") as inner:
                assert get_current_tenant().project_id == "inner_proj"

            # After inner scope exits, should revert to outer
            assert get_current_tenant().project_id == "outer_proj"


class TestTenantDirectories:
    def test_ensure_dirs_creates_structure(self):
        tenant = _make_tenant(user="dir_user", project="dir_project")

        assert tenant.db_path.exists()
        assert (tenant.db_path / "chroma").exists()

    def test_paths_are_correct(self):
        tenant = _make_tenant(user="path_user", project="path_project")

        assert tenant.episodic_db_path == tenant.db_path / "episodic.sqlite"
        assert tenant.chroma_path == tenant.db_path / "chroma"
        assert tenant.graph_path == tenant.db_path / "graph.json"
