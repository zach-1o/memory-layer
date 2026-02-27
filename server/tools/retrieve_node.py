"""
retrieve_node — Tier 3 MCP Tool (heavy, ~500 tokens).

Returns the full raw content of a single observation plus its
knowledge graph connections. This is the deepest level of
Progressive Disclosure — only used when the AI needs full detail.
"""

from namespacing.tenant import Tenant
from memory import episodic, graph as graph_module


async def retrieve_node(tenant: Tenant, obs_id: str) -> dict | None:
    """
    Get full details of a single observation, including graph connections.

    Args:
        tenant: Scoped tenant
        obs_id: Observation ID or graph node name

    Returns:
        Full observation data + connected graph edges, or None if not found
    """
    result = {}

    # Try as episodic observation first
    obs = episodic.get_observation(tenant, obs_id)
    if obs:
        result["observation"] = {
            "id": obs["id"],
            "session_id": obs["session_id"],
            "timestamp": obs["timestamp"],
            "action_type": obs["action_type"],
            "raw_content": obs["raw_content"],
            "compressed_summary": obs.get("compressed_summary", ""),
            "token_count": obs.get("token_count", 0),
            "entities_mentioned": obs.get("entities_mentioned", "[]"),
            "invalidated_at": obs.get("invalidated_at"),
        }

    # Try as graph node
    node_data = graph_module.get_node(tenant, obs_id)
    if node_data:
        result["graph"] = {
            "node": node_data["node"],
            "outgoing_edges": node_data["outgoing_edges"],
            "incoming_edges": node_data["incoming_edges"],
        }

    if not result:
        return None

    return result
