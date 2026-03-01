# MVP Sprint Plan

## Core Memory Engine
- [x] SQLite episodic log with FTS5 full-text search
- [x] ChromaDB semantic layer with Ollama embeddings
- [x] NetworkX knowledge graph with temporal invalidation
- [x] Claude Haiku async compression worker
- [x] Ingestion lifecycle hooks (SessionStart, PostToolUse, SessionEnd)

## MCP Server
- [x] FastAPI entrypoint with CORS + lifespan
- [x] API key auth + rate limiting
- [x] Project namespace router
- [x] MCP JSON-RPC 2.0 handler
- [x] Tool: search_index (Tier 1 — ~50 tokens)
- [x] Tool: get_timeline (Tier 2 — ~200 tokens)
- [x] Tool: retrieve_node (Tier 3 — ~500 tokens)
- [x] Tool: add_observation
- [x] Tool: get_entity
- [x] Tool: trace_flow

## Namespacing
- [x] Tenant model (api_key + project_id → isolated path)
- [x] Cross-project isolation enforcement

## Dashboard
- [x] React app setup
- [x] Cytoscape.js knowledge graph visualization
- [x] Searchable memory list with edit/delete
- [x] Search tab (semantic search bar) — SearchView.jsx
- [x] Key Manager tab (generate, revoke, view usage) — KeyManager.jsx

## Testing
- [x] test_episodic.py — 9 tests ✓
- [x] test_semantic.py — 5 tests ✓
- [x] test_graph.py — 14 tests ✓
- [x] test_mcp_tools.py — 13 tests ✓
- [x] test_namespacing.py — 13 tests ✓
> **54/54 tests green** — verified 2026-02-28

## Infrastructure
- [x] Docker Compose for hosted deployment
- [x] Environment configuration

## Remaining (Phase 2+)
- [x] Dashboard: Search tab + Key Manager tab
- [ ] End-to-end smoke test: cross-session memory retrieval demo
- [ ] project_structure.md discipline throughout
