"""
search_index — Tier 1 MCP Tool (lightweight, ~50 tokens).

Returns only IDs, titles, types, and estimated token costs.
This is the first step of Progressive Disclosure — the AI starts here
and drills down only if it needs more detail.
"""

from namespacing.tenant import Tenant
from memory import episodic, semantic, graph


async def search_index(tenant: Tenant, query: str) -> list[dict]:
    """
    Search across all three memory layers and return lightweight results.

    Returns list of:
        { id, title, type, source, token_cost }
    """
    results = []

    # 1. FTS search on episodic log
    fts_hits = episodic.search_fts(tenant, query, limit=10)
    for hit in fts_hits:
        results.append({
            "id": hit["id"],
            "title": hit.get("snippet", "")[:80],
            "type": hit["action_type"],
            "source": "episodic",
            "token_cost": hit.get("token_count", 50),
        })

    # 2. Semantic similarity search
    try:
        vector_hits = semantic.search_similar(tenant, query, n_results=5)
        for hit in vector_hits:
            # Skip duplicates already found via FTS
            if hit["id"] not in {r["id"] for r in results}:
                results.append({
                    "id": hit["id"],
                    "title": hit["document"][:80] if hit["document"] else "",
                    "type": hit.get("metadata", {}).get("action_type", "observation"),
                    "source": "semantic",
                    "token_cost": 50,
                })
    except Exception:
        pass  # Semantic layer may not be populated yet

    # 3. Graph node name matching
    all_nodes = graph.get_all_nodes(tenant)
    query_lower = query.lower()
    for node in all_nodes:
        if query_lower in node.get("name", "").lower():
            results.append({
                "id": node["name"],
                "title": f"{node.get('type', 'entity')}: {node['name']}",
                "type": "graph_node",
                "source": "graph",
                "token_cost": 30,
            })

    return results[:20]  # Cap at 20 results
