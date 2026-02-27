"""
get_timeline — Tier 2 MCP Tool (medium, ~200 tokens).

Returns chronological observations around a specific observation ID.
This is the second step of Progressive Disclosure.
"""

from namespacing.tenant import Tenant
from memory import episodic


async def get_timeline(tenant: Tenant, obs_id: str, window: int = 5) -> list[dict]:
    """
    Get chronological context around a specific observation.

    Args:
        tenant: Scoped tenant
        obs_id: The observation ID to center on
        window: Number of observations on each side

    Returns list of:
        { id, session_id, timestamp, action_type, summary, token_count, entities }
    """
    timeline = episodic.get_timeline(tenant, obs_id, window=window)

    results = []
    for obs in timeline:
        results.append({
            "id": obs["id"],
            "session_id": obs["session_id"],
            "timestamp": obs["timestamp"],
            "action_type": obs["action_type"],
            "summary": obs.get("compressed_summary", ""),
            "token_count": obs.get("token_count", 0),
            "entities": obs.get("entities_mentioned", "[]"),
        })

    return results
