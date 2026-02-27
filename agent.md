# CLAUDE.md — AI Memory Layer (Persistent Agentic Memory Service)

> This file is the agent's operating manual. Read it fully at the start of every session before touching any code.

---

## 🧠 What This Project Is

We are building a **cloud-hosted, project-scoped persistent memory service** for AI coding assistants.

The core idea: AI agents forget everything between sessions. We fix that by giving them a structured, permanent memory — a hybrid of an event log, a semantic vector store, and a temporal knowledge graph — exposed universally via an MCP server that any IDE (Cursor, Claude Code, VS Code, Google Antigravity) can connect to with a single API key.

**Key constraints to never forget:**
- Every project's memory is strictly isolated — no bleed between projects, ever
- All memory is scoped by `(api_key, project_id)` — not by git URL
- The MCP server is the only interface external tools talk to
- The system must work as a hosted SaaS (not just a local tool)
- Progressive Disclosure retrieval: index → timeline → deep dive (never dump everything)

---

## 🏗️ Architecture Overview

```
Client IDE (Cursor / Claude Code / Antigravity)
        │
        │  MCP over HTTPS + X-Api-Key header
        ▼
┌─────────────────────────────────┐
│        MCP Gateway API          │  ← Auth, rate limiting, key validation
└──────────────┬──────────────────┘
               │
               ▼
┌─────────────────────────────────┐
│     Project Namespace Router    │  ← Resolves (api_key + project_id) → tenant
└──────┬──────────┬───────────────┘
       │          │
       ▼          ▼
┌──────────┐  ┌──────────────────────────────────────┐
│  SQLite  │  │         Memory Engine                │
│  Episodic│  │  ┌─────────────┐  ┌───────────────┐ │
│  Log     │  │  │ Vector Store│  │ Knowledge     │ │
│  (FTS5)  │  │  │ (ChromaDB)  │  │ Graph         │ │
└──────────┘  │  └─────────────┘  │ (NetworkX)    │ │
              │                   └───────────────┘ │
              └──────────────────────────────────────┘
```

**Three storage layers per project:**
1. **Episodic Log (SQLite + FTS5)** — append-only timestamped diary of every agent action
2. **Semantic Layer (ChromaDB)** — vector embeddings of compressed summaries for fuzzy search
3. **Knowledge Graph (NetworkX)** — nodes (files, functions, components) + directed edges (CALLS, IMPORTS, INVOKES_IPC, MODIFIES_STATE) with temporal invalidation

---

## 📁 Project Structure

> **IMPORTANT:** After every meaningful change, update `project_structure.md` with what changed and why. This is non-negotiable.

```
/
├── CLAUDE.md                    ← You are here. Read every session.
├── project_structure.md         ← Living document. Update after every change.
├── tasks/
│   ├── todo.md                  ← Current sprint plan with checkable items
│   └── lessons.md               ← Mistakes made + rules derived. Review each session.
│
├── server/                      ← MCP Gateway + API
│   ├── main.py                  ← FastAPI entrypoint
│   ├── auth.py                  ← API key validation + rate limiting
│   ├── router.py                ← Project namespace resolution
│   ├── mcp_handler.py           ← MCP protocol implementation (JSON-RPC 2.0)
│   └── tools/                   ← MCP tool definitions
│       ├── search_index.py      ← Tier 1: returns IDs + titles + token costs
│       ├── get_timeline.py      ← Tier 2: chronological context around an ID
│       └── retrieve_node.py     ← Tier 3: full raw content of one memory node
│
├── memory/                      ← Core memory engine
│   ├── episodic.py              ← SQLite log: write, read, FTS search
│   ├── semantic.py              ← ChromaDB: embed, upsert, similarity search
│   ├── graph.py                 ← NetworkX: add nodes/edges, traverse, invalidate
│   ├── compression.py           ← Claude Haiku worker: raw log → 200-token summary
│   └── ingestion.py             ← Lifecycle hooks: SessionStart, PostToolUse, SessionEnd
│
├── namespacing/
│   ├── tenant.py                ← Tenant model: api_key + project_id → isolated DB path
│   └── scoping.py               ← Enforces zero cross-project bleed
│
├── dashboard/                   ← localhost React UI (or hosted)
│   ├── src/
│   │   ├── App.jsx
│   │   ├── GraphView.jsx        ← Cytoscape.js knowledge graph visualization
│   │   └── MemoryList.jsx       ← Searchable observation log with edit/delete
│   └── package.json
│
├── db/                          ← Per-tenant database files (gitignored)
│   └── {tenant_hash}/
│       ├── episodic.sqlite
│       ├── chroma/
│       └── graph.json
│
├── tests/
│   ├── test_episodic.py
│   ├── test_semantic.py
│   ├── test_graph.py
│   ├── test_mcp_tools.py
│   └── test_namespacing.py
│
├── .env.example                 ← Required env vars (never commit .env)
├── requirements.txt
└── docker-compose.yml           ← For hosted deployment
```

---

## ⚙️ Workflow Rules

### 1. Plan Before You Touch Code
- For ANY task with 3+ steps or an architectural decision: write the plan to `tasks/todo.md` first
- Format: checkable items `- [ ] step` so progress is trackable
- If something breaks or goes sideways mid-task: **STOP. Re-plan. Don't keep pushing.**
- Verify the plan makes sense before implementing

### 2. Update `project_structure.md` After Every Change
Every time you add a file, rename something, change a module's responsibility, or make an architectural decision, append an entry to `project_structure.md` in this format:

```
## [DATE] — [Short title]
**What changed:** 
**Why:** 
**Files affected:** 
**Anything to watch out for:**
```

This is the project's memory. It should be readable by a new developer joining mid-project.

### 3. Capture Lessons
- After any correction from the user: add the pattern to `tasks/lessons.md`
- Format: **Mistake** → **Rule derived**
- Review `tasks/lessons.md` at the start of every session

### 4. Never Mark Done Without Proof
- Run the relevant test or demonstrate the behavior before marking any `todo.md` item complete
- Ask: *"Would a senior engineer approve this PR?"*
- Check logs. Diff behavior. Don't assume.

### 5. Namespace Isolation Is Sacred
- Every DB read/write MUST be scoped to `(api_key, project_id)`
- No function should ever access raw paths without going through `namespacing/tenant.py`
- Write a test for any new storage operation that asserts cross-project isolation

### 6. Progressive Disclosure — Never Violate It
The MCP tools must always respect the 3-tier hierarchy:
- `search_index` → lightweight, returns titles + IDs only (~50 tokens)
- `get_timeline` → medium, chronological context (~200 tokens)  
- `retrieve_node` → heavy, full content (~500 tokens)

Never build a shortcut that dumps full memory into context. This defeats the entire purpose of the project.

### 7. Fix Bugs Autonomously
- When given a bug report: read the logs, find the root cause, fix it. No hand-holding needed.
- Don't apply temporary patches. Find the real cause.
- If a fix feels hacky, ask: *"Knowing everything I know, what is the elegant solution?"*

---

## 🔌 MCP Server Contract

The hosted MCP server must be reachable via:

```jsonc
{
  "mcpServers": {
    "your-product": {
      "serverUrl": "https://your-api.com/mcp",
      "headers": {
        "X-Api-Key": "skp_your_key_here"
      }
    }
  }
}
```

**Auth flow:**
1. Every MCP request arrives with `X-Api-Key` header
2. `auth.py` validates the key → resolves to a `user_id`
3. Request also includes `project_id` param (set by user in their MCP config or tool call)
4. `router.py` resolves `(user_id, project_id)` → isolated tenant DB path
5. All memory ops execute strictly within that tenant's namespace

**MCP Tools exposed:**

| Tool | Input | Output | Max tokens returned |
|------|-------|--------|-------------------|
| `search_index` | `query: str` | List of `{id, title, type, token_cost}` | ~50 |
| `get_timeline` | `obs_id: str, window: int` | Ordered observations around ID | ~200 |
| `retrieve_node` | `obs_id: str` | Full observation + graph edges | ~500 |
| `add_observation` | `content: str, entities: list` | Confirmation + new ID | — |
| `get_entity` | `entity_name: str` | Node + all connected edges (1-hop) | ~300 |
| `trace_flow` | `from: str, to: str` | Shortest path between two entities | ~200 |

---

## 🧩 Memory Engine Rules

### Episodic Log
- Append-only. Never delete rows. Use `invalidated_at` timestamp for soft-deprecation.
- Every row must have: `id, project_id, session_id, timestamp, action_type, raw_content, compressed_summary, token_count, entities_mentioned`
- FTS5 index on `raw_content` + `compressed_summary`

### Knowledge Graph
- Nodes: `{id, name, type, created_at, invalidated_at, invalidated_by}`
- Edges: `{from, to, relationship, created_at, invalidated_at}`
- Valid relationships: `CALLS`, `IMPORTS`, `INVOKES_IPC`, `MODIFIES_STATE`, `RENDERS`, `DEPENDS_ON`, `DEPRECATED_BY`
- When a function/file is deprecated: set `invalidated_at`, add `DEPRECATED_BY` edge to the replacement. Never hard-delete.
- Serialize graph to `graph.json` per tenant after every mutation

### Compression Worker
- Trigger: after session end OR after 5+ raw observations batch up
- Model: Claude Haiku (cheapest, fastest)
- Output must be ≤ 200 tokens
- Prompt must extract: core intent, files touched, entities created/modified, decision made
- Run in background — never block the MCP response

---

## 🚫 Hard Rules (Never Break These)

1. **Never cross project namespaces.** One API key + project ID = one isolated universe.
2. **Never dump full memory into context.** Always use progressive disclosure.
3. **Never hard-delete from the episodic log or knowledge graph.** Soft-invalidate only.
4. **Never commit `.env` or tenant database files.**
5. **Never let a compression failure block an MCP tool call.** Compression is async, retrieval must always work.
6. **Never skip updating `project_structure.md`** after a meaningful change.

---

## 🧪 Testing Standards

- Every new MCP tool needs an integration test that calls it end-to-end
- Every storage function needs a unit test asserting namespace isolation
- Before marking any task done: run `pytest tests/` and confirm zero failures
- Test file naming: `test_{module_name}.py`

---

## 🌱 Current MVP Scope

**In scope:**
- [ ] SQLite episodic log with FTS5
- [ ] ChromaDB semantic layer
- [ ] NetworkX knowledge graph with temporal invalidation
- [ ] FastMCP server with 3-tier progressive disclosure tools
- [ ] API key auth + project namespace isolation
- [ ] Claude Haiku async compression worker
- [ ] React dashboard with Cytoscape.js graph view
- [ ] `project_structure.md` auto-update discipline

**Out of scope for MVP (post-hackathon):**
- Team-shared memory (multiple users → one project namespace)
- One-click installer for non-technical users
- Billing / usage metering
- GitHub OAuth (using manual API keys for now)

---

## 📝 Session Start Checklist

Before writing any code, run through this:

```
- [ ] Read tasks/lessons.md — any patterns relevant to today's work?
- [ ] Read tasks/todo.md — what's the current plan?
- [ ] Read project_structure.md — what's the current state of the codebase?
- [ ] Confirm which project namespace I'm working in
- [ ] Is today's task 3+ steps? Write the plan to todo.md first.
```

---

*Last updated: see `project_structure.md` for change log*