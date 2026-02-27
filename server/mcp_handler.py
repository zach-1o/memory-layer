"""
MCP Handler — JSON-RPC 2.0 protocol implementation.

Registers all 6 MCP tools and dispatches incoming JSON-RPC calls
to the appropriate tool handler, scoped to the authenticated tenant.

Tools per agent.md:
  1. search_index  — Tier 1 (~50 tokens)
  2. get_timeline  — Tier 2 (~200 tokens)
  3. retrieve_node — Tier 3 (~500 tokens)
  4. add_observation — write new observation
  5. get_entity    — graph node + 1-hop edges (~300 tokens)
  6. trace_flow    — shortest path between entities (~200 tokens)
"""

import json
import logging
from typing import Any

from namespacing.tenant import Tenant
from memory import episodic, graph as graph_module
from memory.ingestion import SessionManager
from server.tools.search_index import search_index
from server.tools.get_timeline import get_timeline
from server.tools.retrieve_node import retrieve_node

logger = logging.getLogger(__name__)

# Active sessions per tenant hash
_sessions: dict[str, SessionManager] = {}


def _get_session(tenant: Tenant) -> SessionManager:
    """Get or create a session manager for the tenant."""
    if tenant.tenant_hash not in _sessions:
        session = SessionManager(tenant)
        session.start_session()
        _sessions[tenant.tenant_hash] = session
    return _sessions[tenant.tenant_hash]


# --- Tool definitions for MCP capabilities listing ---

TOOL_DEFINITIONS = [
    {
        "name": "search_index",
        "description": "Search the memory index. Returns lightweight results: IDs, titles, types. Start here before drilling down. (~50 tokens per result)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "query": {"type": "string", "description": "Search query"},
            },
            "required": ["project_id", "query"],
        },
    },
    {
        "name": "get_timeline",
        "description": "Get chronological observations around a specific memory. Use after search_index to understand context. (~200 tokens)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "obs_id": {"type": "string", "description": "Observation ID from search_index"},
                "window": {"type": "integer", "description": "Number of events on each side", "default": 5},
            },
            "required": ["project_id", "obs_id"],
        },
    },
    {
        "name": "retrieve_node",
        "description": "Get full raw details of one memory node, including graph connections. Use only when you need deep detail. (~500 tokens)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "obs_id": {"type": "string", "description": "Observation or node ID"},
            },
            "required": ["project_id", "obs_id"],
        },
    },
    {
        "name": "add_observation",
        "description": "Record a new observation/action in project memory.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "content": {"type": "string", "description": "What happened"},
                "action_type": {"type": "string", "description": "Type: file_read, file_edit, decision, etc.", "default": "observation"},
                "entities": {
                    "type": "array",
                    "items": {"type": "string"},
                    "description": "Entity names mentioned (files, functions, etc.)",
                    "default": [],
                },
            },
            "required": ["project_id", "content"],
        },
    },
    {
        "name": "get_entity",
        "description": "Get a knowledge graph entity and all its direct connections (1-hop). (~300 tokens)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "entity_name": {"type": "string", "description": "Name of the entity node"},
            },
            "required": ["project_id", "entity_name"],
        },
    },
    {
        "name": "trace_flow",
        "description": "Find the shortest path between two entities in the knowledge graph. (~200 tokens)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_id": {"type": "string", "description": "Project identifier"},
                "from_entity": {"type": "string", "description": "Source entity name"},
                "to_entity": {"type": "string", "description": "Target entity name"},
            },
            "required": ["project_id", "from_entity", "to_entity"],
        },
    },
]


async def handle_tool_call(
    tenant: Tenant,
    tool_name: str,
    arguments: dict[str, Any],
) -> Any:
    """
    Dispatch an MCP tool call to the appropriate handler.
    All handlers receive an already-scoped tenant.
    """
    session = _get_session(tenant)

    if tool_name == "search_index":
        return await search_index(tenant, query=arguments["query"])

    elif tool_name == "get_timeline":
        return await get_timeline(
            tenant,
            obs_id=arguments["obs_id"],
            window=arguments.get("window", 5),
        )

    elif tool_name == "retrieve_node":
        return await retrieve_node(tenant, obs_id=arguments["obs_id"])

    elif tool_name == "add_observation":
        obs_id = session.record_action(
            action_type=arguments.get("action_type", "observation"),
            content=arguments["content"],
            entities=arguments.get("entities", []),
        )
        return {"status": "ok", "observation_id": obs_id}

    elif tool_name == "get_entity":
        node_data = graph_module.get_node(tenant, arguments["entity_name"])
        if node_data is None:
            return {"error": f"Entity '{arguments['entity_name']}' not found"}
        return node_data

    elif tool_name == "trace_flow":
        path = graph_module.trace_flow(
            tenant,
            source=arguments["from_entity"],
            target=arguments["to_entity"],
        )
        if path is None:
            return {"error": "No path found between entities"}
        return {"path": path}

    else:
        return {"error": f"Unknown tool: {tool_name}"}
