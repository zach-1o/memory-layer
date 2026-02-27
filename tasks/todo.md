# MVP Sprint Plan

## Core Memory Engine
- [ ] SQLite episodic log with FTS5 full-text search
- [ ] ChromaDB semantic layer with Ollama embeddings
- [ ] NetworkX knowledge graph with temporal invalidation
- [ ] Claude Haiku async compression worker
- [ ] Ingestion lifecycle hooks (SessionStart, PostToolUse, SessionEnd)

## MCP Server
- [ ] FastAPI entrypoint with CORS + lifespan
- [ ] API key auth + rate limiting
- [ ] Project namespace router
- [ ] MCP JSON-RPC 2.0 handler
- [ ] Tool: search_index (Tier 1 — ~50 tokens)
- [ ] Tool: get_timeline (Tier 2 — ~200 tokens)
- [ ] Tool: retrieve_node (Tier 3 — ~500 tokens)
- [ ] Tool: add_observation
- [ ] Tool: get_entity
- [ ] Tool: trace_flow

## Namespacing
- [ ] Tenant model (api_key + project_id → isolated path)
- [ ] Cross-project isolation enforcement

## Dashboard
- [ ] React app setup
- [ ] Cytoscape.js knowledge graph visualization
- [ ] Searchable memory list with edit/delete

## Testing
- [ ] test_episodic.py
- [ ] test_semantic.py
- [ ] test_graph.py
- [ ] test_mcp_tools.py
- [ ] test_namespacing.py

## Infrastructure
- [ ] Docker Compose for hosted deployment
- [ ] Environment configuration
