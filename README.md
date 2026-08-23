# Memory Layer

A lightweight, multi-tenant memory engine for LLM-driven agents. Memory Layer provides a three-layer storage system that captures timestamped events (episodic log), semantic embeddings for similarity search, and a knowledge graph for structured relationships. It is built to be private-by-default and tenant-isolated (per-project directories).

## Key features / Intended use-cases
- Persistent, append-only episodic log for agent observations and conversations (audit-friendly).
- Semantic search over compressed summaries so models can recall context without exact keywords.
- Knowledge graph to represent structural relationships between program artifacts or domain entities.
- Multi-tenant isolation: each (user_id, project_id) maps to its own filesystem-backed database directory.
- Use cases:
  - Personal assistant memory (recall past actions, preferences).
  - LLM agents that need long-term memory across sessions.
  - Codebase reasoning: extract relations between files/functions and query dependency/flow.
  - Project-specific knowledge stores for multi-project tools.

## Architecture (three-layer design)
- Episodic Log (Layer 1): SQLite append-only database with FTS5 for full-text search. Holds raw content, compressed summaries, metadata, and invalidation flags.
- Semantic Store (Layer 2): ChromaDB persistent collection per-tenant that stores embeddings for compressed summaries and allows similarity search.
- Knowledge Graph (Layer 3): NetworkX-directed graph persisted as graph.json per-tenant with soft-invalidation semantics and typed edges.

## Stack
- Language: Python
- Framework / runtime: plain Python (library + small CLI/tests); suitable to run in Docker
- Notable libraries:
  - sqlite3 (standard library) with FTS5
  - chromadb (vector store / persistent client)
  - networkx (graph serialization / queries)
  - dotenv (config)
  - Ollama (local embeddings) integration (optional, local model)

## Storage backends — details & notes

SQLite (episodic)
- Purpose: append-only event diary of observations.
- Location: per-tenant file `DB_ROOT/<tenant_hash>/episodic.sqlite`.
- Rationale: durable, simple, supports FTS5 for fast full-text queries and small operational footprint.
- Important rules in code:
  - NEVER hard-delete rows. Use `invalidated_at` for soft-deprecation.
  - FTS5 virtual table synced with triggers and used for text search.
- Notes: SQLite is used directly via the standard library sqlite3. WAL mode is enabled for concurrency.

ChromaDB (vector DB)
- Purpose: persistent vector store for semantic embeddings (observations collection).
- Location: per-tenant directory `DB_ROOT/<tenant_hash>/chroma`.
- Default embedding flow:
  - The code uses the ChromaDB PersistentClient and lets ChromaDB handle embeddings by default.
  - If available, Ollama local embeddings are preferred for offline/private embedding generation (configured via OLLAMA_BASE_URL / OLLAMA_MODEL).
- Alternatives: you can swap to other vector DBs (FAISS, Milvus, Weaviate, Pinecone) by replacing the semantic layer client code. Keep IDs consistent with episodic observation IDs so you can correlate results.

Redis (optional integration)
- Redis is not used by default in this repository, but can be introduced for:
  - Caching recent queries or user session state.
  - Pub/Sub wiring between background workers (e.g., compression/embedding workers) and the API worker.
  - Rate-limiting and ephemeral locks.
- Suggestion:
  - Use Redis for ephemeral state only; persist long-term in SQLite/Chroma/graph.
  - If integrating, add a small wrapper module (e.g., `storage/redis_cache.py`) and configure via .env (REDIS_URL).
  - Do not move the authoritative episodic or graph store to Redis — Redis is best as a performance/cross-process coordination layer.

Vector DB Alternatives (considerations)
- FAISS: fast local nearest-neighbor; pairs well with disk-backed index snapshots.
- Pinecone / Milvus / Weaviate: managed/scale options — useful if you need distributed indexing or cloud-managed service.
- When switching:
  - Keep embedding IDs equal to episodic.observation.id.
  - Preserve metadata fields so you can filter by project/session/time.

## Configuration
Important environment variables (see `.env.example`):
- DB_ROOT — root directory for per-tenant stores (default `./db`).
- HOST / PORT — server settings if you run any HTTP layer.
- OLLAMA_BASE_URL / OLLAMA_MODEL — optional local embedding service.
- GOOGLE_API_KEY, ANTHROPIC_API_KEY — used by some extraction/compression workers if enabled.

## Quickstart (development)
1. Create a Python virtual environment and install dependencies:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

2. Configure environment variables:
   - Copy `.env.example` to `.env` and edit values (DB_ROOT, embedding service, API keys if used).

3. Run tests:
   ```bash
   pytest -q
   ```

4. Run via Docker Compose (repository includes a docker-compose.yml):
   ```bash
   docker-compose up --build
   ```
   Adjust ports and env as needed with a `.env` file or compose overrides.

## Usage examples (Python)

Note: the library is not a single-run CLI; these snippets show programmatic usage of the core modules.

1) Resolve a tenant and initialize episodic DB
```python
from namespacing.tenant import resolve_tenant
from memory import episodic

tenant = resolve_tenant(user_id="alice@example.com", project_id="notebook-1")
# ensure directories already created by resolve_tenant
episodic.initialize(tenant)
```

2) Append an observation to the episodic log
```python
obs_id = episodic.write_observation(
    tenant=tenant,
    session_id="session-123",
    action_type="user_message",
    raw_content="I changed the email preferences in settings and saved.",
    entities=["settings", "email_preferences"],
)
print("Saved obs:", obs_id)
```

3) Compress/update a summary (e.g., after running a compression worker)
```python
compressed = "Updated email preferences saved by user (pref: daily newsletter off)."
token_count = 42
episodic.update_summary(tenant, obs_id, compressed, token_count)
```

4) Upsert into semantic vector store (keeps vectors in sync)
```python
from memory import semantic

semantic.upsert_observation(
    tenant=tenant,
    obs_id=obs_id,
    summary=compressed,
    metadata={"action_type": "user_message", "session_id": "session-123"}
)
```

5) Semantic similarity search
```python
results = semantic.search_similar(
    tenant=tenant,
    query="How did the user modify notification preferences?",
    n_results=5,
)
for r in results:
    print(r["id"], r["distance"], r["metadata"])
```

6) Knowledge graph: add nodes/edges and trace flow
```python
from memory import graph

graph.add_node(tenant, name="settings_page", node_type="file")
graph.add_node(tenant, name="save_settings()", node_type="function")
graph.add_edge(tenant, source="save_settings()", target="settings_page", relationship="LOCATED_IN")

path = graph.trace_flow(tenant, "save_settings()", "settings_page")
print("Path:", path)
```

## Operational notes & best practices
- Maintain the invariant that every read/write is scoped to a Tenant. Tenant directories isolate data and make multi-project deployments safer.
- For GDPR/retention: use `invalidate()` / `invalidated_at` to soft-deprecate content rather than deleting.
- Embedding model decisions affect privacy: using Ollama (local) keeps data private. Cloud embeddings (OpenAI, Anthropic, etc.) require data handling review.
- Back up per-tenant directories periodically (episodic.sqlite and chroma directory plus graph.json).

## Development & tests
- Tests in the repo (pytest) exercise models and larger flows; run them in an isolated env so DB_ROOT is a temp directory.
- To iterate on embeddings locally, run a local Ollama model or configure Chroma's fallback behavior.

## Contributing
- Open a PR with a descriptive title and link to the issue (if any).
- Keep cross-tenant isolation in mind when adding features.
- For large feature changes (e.g., swapping vector DBs), include migration steps and compatibility notes.

## Where to add this file
Place this content as `README.md` at the repository root.
