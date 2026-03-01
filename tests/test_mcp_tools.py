"""
Integration tests for MCP tools (end-to-end).

Tests all 6 MCP tools through the handler:
  - search_index
  - get_timeline
  - retrieve_node
  - add_observation
  - get_entity
  - trace_flow
"""

import sys
import os
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))
os.environ["DB_ROOT"] = tempfile.mkdtemp()

import pytest
import asyncio
from namespacing.tenant import resolve_tenant
from memory import episodic, graph
from server.mcp_handler import handle_tool_call, TOOL_DEFINITIONS


def _make_tenant(user="test_user", project="test_project"):
    return resolve_tenant(user, project)


def _run(coro):
    """Helper to run async functions in sync tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestToolDefinitions:
    def test_all_tools_defined(self):
        names = {t["name"] for t in TOOL_DEFINITIONS}
        expected = {"search_index", "get_timeline", "retrieve_node",
                    "add_observation", "get_entity", "trace_flow"}
        assert expected == names

    def test_tools_have_schemas(self):
        for tool in TOOL_DEFINITIONS:
            assert "inputSchema" in tool
            assert "properties" in tool["inputSchema"]
            assert "project_id" in tool["inputSchema"]["properties"]


class TestAddObservation:
    def test_add_and_confirm(self):
        tenant = _make_tenant(project="mcp_add")
        episodic.initialize(tenant)

        result = _run(handle_tool_call(tenant, "add_observation", {
            "content": "Fixed a critical bug in the payment handler",
            "action_type": "file_edit",
            "entities": ["payment.py", "process_payment()"],
        }))

        assert result["status"] == "ok"
        assert "observation_id" in result


class TestSearchIndex:
    def test_search_finds_observation(self):
        tenant = _make_tenant(project="mcp_search")
        episodic.initialize(tenant)

        # Add an observation directly
        episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="decision",
            raw_content="Decided to use Redis for caching instead of Memcached",
            entities=["cache_layer"],
        )

        results = _run(handle_tool_call(tenant, "search_index", {
            "query": "Redis caching",
        }))

        assert isinstance(results, list)
        assert len(results) > 0

    def test_search_returns_lightweight(self):
        tenant = _make_tenant(project="mcp_search_light")
        episodic.initialize(tenant)

        episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="observation",
            raw_content="Lightweight test observation about databases",
        )

        results = _run(handle_tool_call(tenant, "search_index", {
            "query": "databases",
        }))

        if results:
            result = results[0]
            assert "id" in result
            assert "title" in result
            assert "type" in result
            assert "source" in result
            # Should NOT contain raw_content (that's Tier 3)
            assert "raw_content" not in result


class TestGetTimeline:
    def test_timeline_around_observation(self):
        tenant = _make_tenant(project="mcp_timeline")
        episodic.initialize(tenant)

        ids = []
        for i in range(10):
            obs_id = episodic.write_observation(
                tenant=tenant,
                session_id="sess-1",
                action_type="observation",
                raw_content=f"Timeline event {i}",
            )
            ids.append(obs_id)

        results = _run(handle_tool_call(tenant, "get_timeline", {
            "obs_id": ids[5],
            "window": 3,
        }))

        assert isinstance(results, list)
        assert len(results) > 0


class TestRetrieveNode:
    def test_retrieve_full_observation(self):
        tenant = _make_tenant(project="mcp_retrieve")
        episodic.initialize(tenant)

        obs_id = episodic.write_observation(
            tenant=tenant,
            session_id="sess-1",
            action_type="file_edit",
            raw_content="Full content: refactored the entire auth module to use JWT tokens",
            entities=["auth.py", "jwt_handler"],
        )

        result = _run(handle_tool_call(tenant, "retrieve_node", {
            "obs_id": obs_id,
        }))

        assert result is not None
        assert "observation" in result
        assert result["observation"]["raw_content"].startswith("Full content:")

    def test_retrieve_nonexistent(self):
        tenant = _make_tenant(project="mcp_retrieve_none")
        episodic.initialize(tenant)

        result = _run(handle_tool_call(tenant, "retrieve_node", {
            "obs_id": "nonexistent-id",
        }))

        assert result is None


class TestGetEntity:
    def test_get_entity_with_edges(self):
        tenant = _make_tenant(project="mcp_entity")

        graph.add_node(tenant, "App.jsx", "component")
        graph.add_node(tenant, "api.js", "file")
        graph.add_edge(tenant, "App.jsx", "api.js", "CALLS")

        result = _run(handle_tool_call(tenant, "get_entity", {
            "entity_name": "App.jsx",
        }))

        assert "node" in result
        assert result["node"]["name"] == "App.jsx"
        assert len(result["outgoing_edges"]) == 1

    def test_get_entity_not_found(self):
        tenant = _make_tenant(project="mcp_entity_404")

        result = _run(handle_tool_call(tenant, "get_entity", {
            "entity_name": "ghost.py",
        }))

        assert "error" in result


class TestTraceFlow:
    def test_trace_flow_path(self):
        tenant = _make_tenant(project="mcp_trace")

        graph.add_edge(tenant, "button", "api", "CALLS")
        graph.add_edge(tenant, "api", "db", "WRITES")

        result = _run(handle_tool_call(tenant, "trace_flow", {
            "from_entity": "button",
            "to_entity": "db",
        }))

        assert "path" in result
        assert len(result["path"]) == 2

    def test_trace_flow_no_path(self):
        tenant = _make_tenant(project="mcp_trace_none")

        graph.add_node(tenant, "island_a", "file")
        graph.add_node(tenant, "island_b", "file")

        result = _run(handle_tool_call(tenant, "trace_flow", {
            "from_entity": "island_a",
            "to_entity": "island_b",
        }))

        assert "error" in result


class TestUnknownTool:
    def test_unknown_tool(self):
        tenant = _make_tenant(project="mcp_unknown")

        result = _run(handle_tool_call(tenant, "nonexistent_tool", {}))
        assert "error" in result
