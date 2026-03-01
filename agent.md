# agent.md — Memory Layer
### Persistent Cognitive Infrastructure for Autonomous AI Systems

> Read this file **completely** at the start of every session. No exceptions.
> This is not documentation. This is your operating system.

---

## 0. Session Start Ritual

Before touching a single file, complete this checklist:

```
- [ ] Read tasks/lessons.md — internalize every rule before writing code
- [ ] Read tasks/todo.md — know the current sprint state
- [ ] Read project_structure.md — know what changed last session
- [ ] Identify which layer you're working in (server / memory / namespacing / dashboard)
- [ ] Is today's task 3+ steps or architectural? Write the plan to todo.md FIRST
```

If you skip this, you will repeat mistakes. Don't skip it.

---

## 1. What This Project Is

We are building a **cloud-hosted, multi-tenant persistent memory service** — the cognitive infrastructure layer beneath autonomous AI systems.

### The Problem We Solve

AI agents forget everything between sessions. They re-explain architecture. They repeat fixed bugs. They hallucinate deprecated patterns. They burn tokens re-establishing context.

This is not a minor inconvenience — it is an existential limitation for autonomous agents operating over days, weeks, or months.

### What We Build

A structured, permanent memory engine with three storage layers:

| Layer | Technology | Purpose |
|-------|-----------|---------|
| **Episodic Log** | SQLite + FTS5 | Append-only diary of every agent action |
| **Semantic Layer** | ChromaDB + embeddings | Fuzzy meaning-based search over summaries |
| **Knowledge Graph** | NetworkX → Neo4j | Structural relationships between code entities, with temporal history |

Exposed universally via an **MCP server** — one API key, compatible with Cursor, Claude Code, VS Code, Google Antigravity, any MCP-compliant host.

### One-Sentence Pitch

> We give AI agents a permanent, structured, auditable brain — so they never forget a codebase, understand how code connects, and get smarter every session instead of starting from zero.

---

## 2. Architecture

```
AI Agent / IDE / Multi-Agent Orchestrator
            │
            │  MCP over HTTPS
            │  X-Api-Key: skp_xxx
            │  project_id: my-project
            ▼
┌────────────────────────────────────────┐
│           MCP Gateway (SaaS)           │
│  auth.py → rate limiting → key lookup  │
└──────────────────┬─────────────────────┘
                   │
                   ▼
┌────────────────────────────────────────┐
│        Project Namespace Router        │
│   (api_key, project_id) → tenant_hash  │
│   SHA-256 deterministic isolation      │
└────────┬─────────────────┬─────────────┘
         │                 │
         ▼                 ▼
┌─────────────┐   ┌────────────────────────────────┐
│  Episodic   │   │         Memory Engine          │
│  SQLite+FTS5│   │  ChromaDB        NetworkX      │
│  (diary)    │   │  (fuzzy recall)  (graph)       │
└─────────────┘   └────────────────────────────────┘
         │
         ▼
┌────────────────────────────────────────┐
│         Web Dashboard (React)          │
│  Graph View · Timeline · Search · Keys │
└────────────────────────────────────────┘
```

**Isolation rule:** Every storage operation is scoped to `tenant_hash = SHA256(api_key + project_id)`. This is enforced at the `namespacing/` layer. No exceptions.

---

## 3. Project Structure

```
memory-layer/
│
├── agent.md                         ← THIS FILE. Read every session.
├── EXPLAINER.md                     ← Plain-language overview (for humans / pitch)
├── project_structure.md             ← Living changelog. Update after every change.
├── requirements.txt
├── .env.example
├── .gitignore                       ← Protects .env, db/, node_modules/
├── docker-compose.yml
│
├── tasks/
│   ├── todo.md                      ← Current sprint. Checkable items only.
│   └── lessons.md                   ← Mistakes → Rules. Review every session.
│
├── server/                          ← MCP Gateway + FastAPI
│   ├── main.py                      ← Entrypoint. JSON-RPC 2.0 over HTTPS.
│   ├── auth.py                      ← X-Api-Key validation + rate limiting
│   ├── router.py                    ← (api_key, project_id) → tenant_hash
│   ├── mcp_handler.py               ← Tool dispatch + JSON-RPC plumbing
│   └── tools/
│       ├── search_index.py          ← Tier 1: IDs + titles + token costs (~50 tok)
│       ├── get_timeline.py          ← Tier 2: chronological context (~200 tok)
│       ├── retrieve_node.py         ← Tier 3: full observation + edges (~500 tok)
│       ├── add_observation.py       ← Write new memory entry
│       ├── get_entity.py            ← Node + 1-hop edges (~300 tok)
│       └── trace_flow.py            ← Shortest path between two entities (~200 tok)
│
├── memory/
│   ├── episodic.py                  ← SQLite: write, read, FTS5 search, invalidate
│   ├── semantic.py                  ← ChromaDB: embed, upsert, similarity search
│   ├── graph.py                     ← NetworkX: nodes, edges, traverse, soft-delete
│   ├── compression.py               ← Async Claude Haiku worker → ≤200 token summary
│   └── ingestion.py                 ← Lifecycle hooks: SessionStart/PostToolUse/SessionEnd
│
├── namespacing/
│   ├── tenant.py                    ← SHA-256 hash → isolated db path per tenant
│   └── scoping.py                   ← Context-var enforcement. Raises ScopeError if violated.
│
├── dashboard/                       ← React + Cytoscape.js
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.jsx                  ← Tab nav: Graph / Timeline / Search / Keys
│       ├── GraphView.jsx            ← Cytoscape.js interactive knowledge graph
│       ├── MemoryList.jsx           ← Searchable observation log + CRUD controls
│       ├── KeyManager.jsx           ← API key generation, revocation, usage stats
│       └── index.css                ← Dark theme design system
│
├── db/                              ← Per-tenant data (gitignored)
│   └── {tenant_hash}/
│       ├── episodic.sqlite
│       ├── chroma/
│       └── graph.json
│
└── tests/
    ├── test_episodic.py             ← 8 tests: CRUD, FTS5, timeline, invalidation
    ├── test_semantic.py             ← 5 tests: upsert, search, delete
    ├── test_graph.py                ← 14 tests: nodes, edges, trace_flow, persistence
    ├── test_mcp_tools.py            ← 11 tests: all 6 tools end-to-end
    └── test_namespacing.py          ← 10 tests: isolation, scoping, ScopeError
```

---

## 4. MCP Contract

Any IDE connects via:

```jsonc
{
  "mcpServers": {
    "memory-layer": {
      "serverUrl": "https://api.memorylayer.ai/mcp",
      "headers": {
        "X-Api-Key": "skp_your_key_here"
      }
    }
  }
}
```

### Auth Flow (never change this without a plan)

```
Request arrives → auth.py extracts X-Api-Key
                → validates key → resolves user_id
                → extracts project_id from request body
                → router.py computes tenant_hash = SHA256(user_id + project_id)
                → all storage ops use that hash as the root path
```

### Tool Definitions

| Tool | Input | Returns | Token budget |
|------|-------|---------|-------------|
| `search_index` | `query: str` | `[{id, title, type, token_cost}]` | ~50 |
| `get_timeline` | `obs_id: str, window: int` | Ordered observations | ~200 |
| `retrieve_node` | `obs_id: str` | Full content + graph edges | ~500 |
| `add_observation` | `content: str, entities: list` | `{id, status}` | — |
| `get_entity` | `entity_name: str` | Node + 1-hop neighbors | ~300 |
| `trace_flow` | `from: str, to: str` | Shortest path list | ~200 |

**Progressive Disclosure is non-negotiable.** The agent always starts at Tier 1. It escalates only when needed. Never build a shortcut that bypasses this.

---

## 5. Memory Engine Rules

### Episodic Log
- **Append-only.** Never `DELETE` a row. Ever.
- Soft-deprecate with `invalidated_at = timestamp`.
- Schema: `id, project_id, session_id, timestamp, action_type, raw_content, compressed_summary, token_count, entities_mentioned, invalidated_at`
- FTS5 triggers auto-sync on INSERT/UPDATE — do not manage the index manually.

### Knowledge Graph
- **No hard deletes.** Set `invalidated_at` + add `DEPRECATED_BY` edge.
- Valid node types: `file`, `function`, `component`, `api`, `task`, `service`
- Valid edge types: `CALLS`, `IMPORTS`, `INVOKES_IPC`, `MODIFIES_STATE`, `RENDERS`, `DEPENDS_ON`, `DEPRECATED_BY`
- Serialize to `graph.json` after every mutation.
- Nodes schema: `{id, name, type, created_at, invalidated_at, invalidated_by}`
- Edges schema: `{from, to, relationship, created_at, invalidated_at}`

### Compression Worker
- **Trigger:** Session end OR 5+ raw observations queued.
- **Model:** Claude Haiku only (cheap, fast, sufficient).
- **Output:** ≤ 200 tokens. Extracts: intent, files touched, entities modified, decisions made.
- **Always async.** Never block an MCP tool response waiting for compression.
- A compression failure must never surface to the agent as an error.

### Namespace Scoping
- All storage functions receive `tenant_hash` — never a raw `api_key` or `project_id`.
- `scoping.py` uses Python context vars — thread-safe and async-safe.
- If any function accesses storage without a valid scope, it raises `ScopeError` immediately.
- This is enforced at the call site, not just in tests.

---

## 6. Dashboard Requirements

The dashboard is not cosmetic. It is the **trust layer** — how humans audit, correct, and control what the AI knows.

### Views

**Graph View (`GraphView.jsx`)**
- Cytoscape.js interactive canvas
- Node colors: files=blue, functions=green, components=purple, deprecated=red/dimmed
- Edge labels show relationship type
- Click any node → inspect full content + edges
- Toggle: show/hide deprecated nodes
- Trace mode: click two nodes → highlight shortest path

**Timeline View (`MemoryList.jsx`)**
- Chronological list of observations, grouped by session
- Expand any entry → full content + compressed summary
- Inline edit of compressed summary
- Soft-invalidate button (never delete)
- Token cost shown per entry

**Search View**
- Semantic search bar over all observations + entities
- Returns: relevance score, token cost, last accessed, tier needed
- Results link directly to graph nodes

**Key Manager (`KeyManager.jsx`)**
- Generate new API keys
- Assign key to a project name (user-defined)
- Revoke any key instantly
- View: requests/day, tokens consumed, projects attached

---

## 7. Workflow Rules

### Rule 1: Plan Before Code
Any task with 3+ steps or an architectural decision requires a written plan in `tasks/todo.md` before implementation starts. Format:

```markdown
## Task: [name]
- [ ] Step one
- [ ] Step two
- [ ] Step three
**Verify by:** [how you'll prove it works]
```

If something breaks mid-task — **stop. Re-plan. Never keep pushing into a hole.**

### Rule 2: Update `project_structure.md` After Every Change

Format:

```markdown
## YYYY-MM-DD — [Short title]
**What changed:** 
**Why:** 
**Files affected:** 
**Watch out for:** 
```

This file is the project's own memory. A new developer (or a new agent session) must be able to understand the full build history from this file alone.

### Rule 3: Capture Lessons

After any user correction → immediately add to `tasks/lessons.md`:

```markdown
## Lesson [N]
**Mistake:** what went wrong
**Rule:** the rule that prevents it
**Date:** 
```

### Rule 4: Never Mark Done Without Proof
- Run `pytest tests/` — zero failures
- Demonstrate the behavior manually if it's a UI or MCP change
- Ask: *"Would a senior engineer approve this PR?"*

### Rule 5: Fix Bugs Autonomously
Bug report received → read logs → find root cause → fix it. No hand-holding. No temporary patches. No "I'll look at it later." Root cause only.

If the fix feels hacky: stop and implement the elegant solution instead.

---

## 8. Hard Rules (Non-Negotiable)

These are inviolable. No exception. No "just this once."

```
1. NEVER cross project namespaces. (api_key, project_id) = one universe.
2. NEVER dump full memory into context. Progressive disclosure always.
3. NEVER hard-delete from episodic log or knowledge graph. Soft-invalidate only.
4. NEVER commit .env or db/ files.
5. NEVER let compression failure block an MCP tool response.
6. NEVER skip updating project_structure.md after a meaningful change.
7. NEVER access storage without going through namespacing/tenant.py first.
8. NEVER mark a task done without running pytest tests/ and seeing zero failures.
```

---

## 9. Testing Standards

- Test order of execution: `test_namespacing` → `test_episodic` → `test_semantic` → `test_graph` → `test_mcp_tools`
- Every new MCP tool needs a full end-to-end integration test
- Every new storage function needs a namespace isolation assertion
- Test naming: `test_{module}_{behavior}` e.g. `test_episodic_fts5_search_returns_correct_row`
- Before marking any todo item done: `python -m pytest tests/ -v` must show all green

---

## 10. MVP Scope

### In Scope (Ship for Hackathon)
- [x] Project scaffold — 34 files, 7 components
- [ ] SQLite episodic log with FTS5 (all tests green)
- [ ] ChromaDB semantic layer (all tests green)
- [ ] NetworkX knowledge graph with temporal invalidation (all tests green)
- [ ] FastMCP server — 6 tools with progressive disclosure (all tests green)
- [ ] API key auth + SHA-256 namespace isolation (all tests green)
- [ ] Claude Haiku async compression worker
- [ ] React dashboard — Graph + Timeline + Search + Key Manager
- [ ] End-to-end smoke test: cross-session memory retrieval demo
- [ ] `project_structure.md` discipline throughout

### Out of Scope (Post-Hackathon)
- Team-shared namespaces (multiple users → one project)
- GitHub OAuth
- Billing / usage metering
- One-click installer for non-technical users
- Production graph DB (Neo4j / TigerGraph)
- Production vector DB (Qdrant / Weaviate)
- SOC2 compliance

---

## 11. Environment Variables

```bash
# .env (never commit this)
ANTHROPIC_API_KEY=sk-ant-...         # For Claude Haiku compression worker
SECRET_KEY=...                        # For API key signing
DB_ROOT=./db                         # Root path for tenant databases
EMBEDDING_MODEL=nomic-embed-text     # Via Ollama (local) or swap for OpenAI
DASHBOARD_PORT=37777
MCP_PORT=8000
LOG_LEVEL=INFO
```

---

## 12. Running the Project

```bash
# Install Python dependencies
pip install -r requirements.txt

# Install dashboard dependencies
cd dashboard && npm install && cd ..

# Copy and fill environment variables
cp .env.example .env

# Run all tests (should be green before any feature work)
python -m pytest tests/ -v

# Start MCP server
python -m uvicorn server.main:app --reload --port 8000

# Start dashboard (separate terminal)
cd dashboard && npm run dev
# → http://localhost:37777

# Connect to MCP in your IDE
# Add to cursor settings / claude desktop config:
# serverUrl: http://localhost:8000/mcp
# X-Api-Key: any string in dev mode
```

---

## 13. Dual Usage Model

This system serves two distinct users with the same backend:

**🤖 AI Agents** — store cognition, query history, build cumulative knowledge, avoid repeated errors, trace execution flows, reduce token waste.

**👩‍💻 Developers** — audit agent reasoning, correct wrong memories, visualize architecture evolution, debug cross-session issues, enforce architectural consistency.

Same data. Same API. Different interfaces. Keep both users in mind when making design decisions.

---

## 14. Go-To-Market Path

| Phase | Target | Hook |
|-------|--------|------|
| 1 — Developer Adoption | Cursor / Claude Code users | Easy MCP setup + token savings |
| 2 — Agent Infrastructure | AI-native startups, automation builders | Persistent cognition API |
| 3 — Enterprise Governance | Companies deploying internal AI agents | Audit trail, compliance, org knowledge graph |

---

*This document is the agent's brain. Treat it accordingly.*
*Last updated: see `project_structure.md`*