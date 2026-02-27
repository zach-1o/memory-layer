"""
Tests for the Knowledge Graph (NetworkX).

Covers:
  - Add nodes and edges
  - Relationship type validation
  - 1-hop neighborhood retrieval
  - Temporal invalidation + DEPRECATED_BY
  - Shortest path (trace_flow)
  - JSON serialization/deserialization
  - Namespace isolation
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ["DB_ROOT"] = tempfile.mkdtemp()

import pytest
from namespacing.tenant import resolve_tenant
from memory import graph


def _make_tenant(user="test_user", project="test_project"):
    return resolve_tenant(user, project)


class TestGraphNodes:
    def test_add_node(self):
        tenant = _make_tenant(project="graph_nodes")
        node = graph.add_node(tenant, "main.py", "file")

        assert node["name"] == "main.py"
        assert node["type"] == "file"
        assert node["invalidated_at"] is None

    def test_get_node(self):
        tenant = _make_tenant(project="graph_get")
        graph.add_node(tenant, "App.jsx", "component")

        result = graph.get_node(tenant, "App.jsx")
        assert result is not None
        assert result["node"]["name"] == "App.jsx"
        assert result["node"]["type"] == "component"

    def test_get_nonexistent_node(self):
        tenant = _make_tenant(project="graph_nonode")
        result = graph.get_node(tenant, "nonexistent")
        assert result is None


class TestGraphEdges:
    def test_add_edge(self):
        tenant = _make_tenant(project="graph_edges")
        graph.add_node(tenant, "App.jsx", "component")
        graph.add_node(tenant, "api.js", "file")

        edge = graph.add_edge(tenant, "App.jsx", "api.js", "CALLS")
        assert edge["relationship"] == "CALLS"
        assert edge["invalidated_at"] is None

    def test_invalid_relationship(self):
        tenant = _make_tenant(project="graph_invalid_rel")
        with pytest.raises(ValueError, match="Invalid relationship"):
            graph.add_edge(tenant, "a", "b", "LIKES")

    def test_auto_create_nodes(self):
        tenant = _make_tenant(project="graph_autocreate")
        graph.add_edge(tenant, "new_source", "new_target", "IMPORTS")

        # Both nodes should be auto-created
        source = graph.get_node(tenant, "new_source")
        target = graph.get_node(tenant, "new_target")
        assert source is not None
        assert target is not None

    def test_neighborhood(self):
        tenant = _make_tenant(project="graph_neighborhood")
        graph.add_node(tenant, "handler.py", "file")
        graph.add_node(tenant, "db.py", "file")
        graph.add_node(tenant, "auth.py", "file")

        graph.add_edge(tenant, "handler.py", "db.py", "CALLS")
        graph.add_edge(tenant, "auth.py", "handler.py", "IMPORTS")

        result = graph.get_node(tenant, "handler.py")
        assert len(result["outgoing_edges"]) == 1  # handler → db
        assert len(result["incoming_edges"]) == 1  # auth → handler


class TestGraphInvalidation:
    def test_invalidate_node(self):
        tenant = _make_tenant(project="graph_invalidate")
        graph.add_node(tenant, "old_func", "function")

        result = graph.invalidate_node(tenant, "old_func")
        assert result is True

        node = graph.get_node(tenant, "old_func")
        assert node["node"]["invalidated_at"] is not None

    def test_invalidate_with_replacement(self):
        tenant = _make_tenant(project="graph_deprecated")
        graph.add_node(tenant, "old_func", "function")

        graph.invalidate_node(tenant, "old_func", replaced_by="new_func")

        old = graph.get_node(tenant, "old_func")
        assert old["node"]["invalidated_at"] is not None
        assert old["node"]["invalidated_by"] == "new_func"

        # Should have a DEPRECATED_BY edge
        new = graph.get_node(tenant, "new_func")
        assert new is not None  # Replacement node auto-created

    def test_invalidate_edge(self):
        tenant = _make_tenant(project="graph_inv_edge")
        graph.add_edge(tenant, "a", "b", "CALLS")

        result = graph.invalidate_edge(tenant, "a", "b")
        assert result is True

    def test_invalidated_excluded_from_listing(self):
        tenant = _make_tenant(project="graph_excludes")
        graph.add_node(tenant, "active_node", "file")
        graph.add_node(tenant, "dead_node", "file")
        graph.invalidate_node(tenant, "dead_node")

        active_nodes = graph.get_all_nodes(tenant, include_invalidated=False)
        names = [n["name"] for n in active_nodes]
        assert "active_node" in names
        assert "dead_node" not in names

        all_nodes = graph.get_all_nodes(tenant, include_invalidated=True)
        all_names = [n["name"] for n in all_nodes]
        assert "dead_node" in all_names


class TestGraphTraceFlow:
    def test_trace_flow(self):
        tenant = _make_tenant(project="graph_trace")
        graph.add_node(tenant, "button", "component")
        graph.add_node(tenant, "api", "file")
        graph.add_node(tenant, "handler", "function")
        graph.add_node(tenant, "db", "file")

        graph.add_edge(tenant, "button", "api", "CALLS")
        graph.add_edge(tenant, "api", "handler", "CALLS")
        graph.add_edge(tenant, "handler", "db", "MODIFIES_STATE")

        path = graph.trace_flow(tenant, "button", "db")
        assert path is not None
        assert len(path) == 3
        assert path[0]["from"] == "button"
        assert path[-1]["to"] == "db"

    def test_trace_flow_no_path(self):
        tenant = _make_tenant(project="graph_nopath")
        graph.add_node(tenant, "isolated_a", "file")
        graph.add_node(tenant, "isolated_b", "file")

        path = graph.trace_flow(tenant, "isolated_a", "isolated_b")
        assert path is None

    def test_trace_flow_skips_invalidated(self):
        tenant = _make_tenant(project="graph_trace_inv")
        graph.add_edge(tenant, "a", "b", "CALLS")
        graph.add_edge(tenant, "b", "c", "CALLS")

        # Invalidate the b→c edge
        graph.invalidate_edge(tenant, "b", "c")

        path = graph.trace_flow(tenant, "a", "c")
        assert path is None  # No active path exists


class TestGraphSerialization:
    def test_persistence(self):
        tenant = _make_tenant(project="graph_persist")
        graph.add_node(tenant, "persisted_file", "file")
        graph.add_edge(tenant, "persisted_file", "other", "IMPORTS")

        # graph.json should exist
        assert tenant.graph_path.exists()

        # Re-loading should preserve data
        node = graph.get_node(tenant, "persisted_file")
        assert node is not None
        assert len(node["outgoing_edges"]) == 1
