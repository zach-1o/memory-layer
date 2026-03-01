"""
Knowledge Graph — NetworkX directed graph with temporal invalidation.

Stores structural relationships between code entities:
  Nodes: files, functions, components, variables
  Edges: CALLS, IMPORTS, INVOKES_IPC, MODIFIES_STATE, RENDERS, DEPENDS_ON, DEPRECATED_BY

Rules from agent.md:
  - Never hard-delete. Use invalidated_at + DEPRECATED_BY edges.
  - Serialize to graph.json after every mutation.
  - All access must be scoped to a tenant.
"""

import json
import networkx as nx
from datetime import datetime, timezone
from typing import Optional

from namespacing.tenant import Tenant

# Valid relationship types per agent.md
VALID_RELATIONSHIPS = {
    "RELATES_TO",
    "DEPENDS_ON",
    "CONTAINS",
    "USES",
    "CREATED_BY",
    "MODIFIED_BY",
    "PART_OF",
    "REFERENCES",
    "IMPLEMENTS",
    "EXTENDS",
    "OVERRIDES",
    "CO_OCCURS",
    # Phase 3: LLM-extracted directional relationships
    "CALLS",
    "READS",
    "WRITES",
    "IMPORTS",
    "LOCATED_IN",
    "SENDS_TO",
    "TRIGGERS",
    "RETURNS",
    "LOCKS",
    "CREATES",
    "FIXES",
}


def _load_graph(tenant: Tenant) -> nx.DiGraph:
    """Load the knowledge graph from disk, or create a new empty one."""
    graph_path = tenant.graph_path
    if graph_path.exists():
        with open(graph_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return nx.node_link_graph(data, directed=True)
    return nx.DiGraph()


def _save_graph(tenant: Tenant, graph: nx.DiGraph) -> None:
    """Serialize graph to JSON after every mutation."""
    graph_path = tenant.graph_path
    data = nx.node_link_data(graph)
    with open(graph_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, default=str)


def add_node(
    tenant: Tenant,
    name: str,
    node_type: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Add or update a node in the knowledge graph.

    Args:
        name: Unique identifier (e.g., 'App.jsx', 'save_settings()')
        node_type: Category (e.g., 'file', 'function', 'component', 'variable')
        metadata: Optional extra data
    """
    graph = _load_graph(tenant)
    now = datetime.now(timezone.utc).isoformat()

    node_data = {
        "name": name,
        "type": node_type,
        "created_at": now,
        "invalidated_at": None,
        "invalidated_by": None,
        **(metadata or {}),
    }

    if graph.has_node(name):
        # Update existing node, preserve created_at
        existing = graph.nodes[name]
        node_data["created_at"] = existing.get("created_at", now)
        graph.nodes[name].update(node_data)
    else:
        graph.add_node(name, **node_data)

    _save_graph(tenant, graph)
    return node_data


def add_edge(
    tenant: Tenant,
    source: str,
    target: str,
    relationship: str,
    metadata: Optional[dict] = None,
) -> dict:
    """
    Add a directed edge between two nodes.

    Validates that the relationship type is in the allowed set.
    Auto-creates nodes if they don't exist.
    """
    if relationship not in VALID_RELATIONSHIPS:
        raise ValueError(
            f"Invalid relationship '{relationship}'. Must be one of: {VALID_RELATIONSHIPS}"
        )

    graph = _load_graph(tenant)
    now = datetime.now(timezone.utc).isoformat()

    # Auto-create nodes if they don't exist
    for node_name in (source, target):
        if not graph.has_node(node_name):
            graph.add_node(
                node_name,
                name=node_name,
                type="unknown",
                created_at=now,
                invalidated_at=None,
                invalidated_by=None,
            )

    edge_data = {
        "relationship": relationship,
        "created_at": now,
        "invalidated_at": None,
        **(metadata or {}),
    }

    graph.add_edge(source, target, **edge_data)
    _save_graph(tenant, graph)
    return edge_data


def get_node(tenant: Tenant, name: str) -> Optional[dict]:
    """Get a node and all its connected edges (1-hop neighborhood)."""
    graph = _load_graph(tenant)
    if not graph.has_node(name):
        return None

    node_data = dict(graph.nodes[name])

    # Get all edges connected to this node
    outgoing = []
    for _, target, data in graph.out_edges(name, data=True):
        if data.get("invalidated_at") is None:
            outgoing.append({"target": target, **data})

    incoming = []
    for source, _, data in graph.in_edges(name, data=True):
        if data.get("invalidated_at") is None:
            incoming.append({"source": source, **data})

    return {
        "node": node_data,
        "outgoing_edges": outgoing,
        "incoming_edges": incoming,
    }


def invalidate_node(
    tenant: Tenant,
    name: str,
    replaced_by: Optional[str] = None,
) -> bool:
    """
    Soft-invalidate a node. Never hard-delete.
    If replaced_by is provided, adds a DEPRECATED_BY edge.
    """
    graph = _load_graph(tenant)
    if not graph.has_node(name):
        return False

    now = datetime.now(timezone.utc).isoformat()
    graph.nodes[name]["invalidated_at"] = now

    if replaced_by:
        graph.nodes[name]["invalidated_by"] = replaced_by
        # Auto-create replacement node if needed
        if not graph.has_node(replaced_by):
            graph.add_node(
                replaced_by,
                name=replaced_by,
                type=graph.nodes[name].get("type", "unknown"),
                created_at=now,
                invalidated_at=None,
                invalidated_by=None,
            )
        graph.add_edge(
            name,
            replaced_by,
            relationship="DEPRECATED_BY",
            created_at=now,
            invalidated_at=None,
        )

    _save_graph(tenant, graph)
    return True


def invalidate_edge(
    tenant: Tenant, source: str, target: str
) -> bool:
    """Soft-invalidate an edge between two nodes."""
    graph = _load_graph(tenant)
    if not graph.has_edge(source, target):
        return False

    now = datetime.now(timezone.utc).isoformat()
    graph.edges[source, target]["invalidated_at"] = now
    _save_graph(tenant, graph)
    return True


def trace_flow(
    tenant: Tenant, source: str, target: str
) -> Optional[list[dict]]:
    """
    Find the shortest path between two entities.
    Only traverses active (non-invalidated) edges.
    """
    graph = _load_graph(tenant)

    # Build a subgraph with only active edges
    active_edges = [
        (u, v)
        for u, v, d in graph.edges(data=True)
        if d.get("invalidated_at") is None
    ]
    active_graph = graph.edge_subgraph(active_edges).copy()

    try:
        path = nx.shortest_path(active_graph, source, target)
    except (nx.NetworkXNoPath, nx.NodeNotFound):
        return None

    # Build the path with edge details
    result = []
    for i in range(len(path) - 1):
        edge_data = dict(active_graph.edges[path[i], path[i + 1]])
        result.append({
            "from": path[i],
            "to": path[i + 1],
            **edge_data,
        })
    return result


def get_all_nodes(tenant: Tenant, include_invalidated: bool = False) -> list[dict]:
    """Get all nodes in the graph, optionally including invalidated ones."""
    graph = _load_graph(tenant)
    nodes = []
    for name, data in graph.nodes(data=True):
        if not include_invalidated and data.get("invalidated_at") is not None:
            continue
        nodes.append({"name": name, **data})
    return nodes


def get_all_edges(tenant: Tenant, include_invalidated: bool = False) -> list[dict]:
    """Get all edges in the graph, optionally including invalidated ones."""
    graph = _load_graph(tenant)
    edges = []
    for source, target, data in graph.edges(data=True):
        if not include_invalidated and data.get("invalidated_at") is not None:
            continue
        edges.append({"source": source, "target": target, **data})
    return edges
