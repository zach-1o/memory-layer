# Project Structure — Change Log

> Update this file after every meaningful change. This is the project's memory.

---

## 2026-02-25 — Initial Project Scaffold
**What changed:** Created the full project structure from scratch per `agent.md` specifications.
**Why:** Greenfield build for the Memory Layer hackathon project.
**Files affected:** All files — server/, memory/, namespacing/, dashboard/, tests/, config files.
**Anything to watch out for:** All modules have stub implementations. Each needs to be fleshed out incrementally per `tasks/todo.md`.

## 2026-02-25 — All 54 Tests Green
**What changed:** Fixed ChromaDB v1.5 compatibility in `memory/semantic.py` — empty metadata dicts rejected, now passes `None`.
**Why:** ChromaDB v1.5+ enforces non-empty metadata validation.
**Files affected:** `memory/semantic.py`
**Anything to watch out for:** Always pass `None` instead of `{}` to ChromaDB metadatas. See `tasks/lessons.md`.

## 2026-02-28 — Phase 1 Verification Complete
**What changed:** Ran full test suite (54/54 green, 8.77s). Updated `tasks/todo.md` to check off all completed items. Confirmed all Python deps installed.
**Why:** Starting a new sprint — needed to verify baseline before building dashboard Search + Key Manager tabs.
**Files affected:** `tasks/todo.md`, `project_structure.md`
**Anything to watch out for:** Use `C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe` for pytest — the default `python` and `py -3` resolve to msys64/Python 3.14 which lack project deps.

## 2026-02-28 — Phase 2: Dashboard Completion
**What changed:** Full dashboard rebuild. Added `SearchView.jsx` (FTS5 search, tier badges, token costs, detail panels), `KeyManager.jsx` (generate/revoke/list keys, IDE config snippet). Rewrote `GraphView.jsx` (toggle deprecated, trace mode with Dijkstra path highlighting, node inspector, color legend). Rewrote `MemoryList.jsx` (session grouping, inline summary editing, soft-invalidate button). Updated `App.jsx` with 4 tabs. Added 5 backend endpoints for observation invalidation, summary editing, and key management. Added 550+ lines of CSS.
**Why:** MVP dashboard completion per `agent.md` Section 6.
**Files affected:** `dashboard/src/App.jsx`, `dashboard/src/GraphView.jsx`, `dashboard/src/MemoryList.jsx`, `dashboard/src/SearchView.jsx` (new), `dashboard/src/KeyManager.jsx` (new), `dashboard/src/index.css`, `server/main.py`
**Anything to watch out for:** Use `& "C:\Program Files\nodejs\npm.cmd"` to run npm commands — PowerShell execution policy blocks `npm.ps1`. Vite build shows CJS deprecation warning (cosmetic, not an error).

## 2026-03-01 — Phase 4: Polish & Final Tests
**What changed:** Implemented end-to-end (E2E) smoke test simulating progressive disclosure memory retrieval (`search_index` -> `get_timeline` -> `trace_flow`). Fixed missing FTS5 update trigger and token-saving field names. Added robust disconnection banners and empty states to the React dashboard. Ran `flake8` to completely strip unused imports and variables, and wrapped asyncio background tasks in global `try/except` blocks to prevent silent queue crashes.
**Why:** Final polish to ensure the system is entirely stable and ready for production use.
**Files affected:** `tests/smoke_test_e2e.py`, `dashboard/src/App.jsx`, `memory/compression.py`, `memory/graph_extractor.py`, `server/main.py` + multiple file cleanups.
**Anything to watch out for:** The background tasks in `ingestion.py` no longer crash silently if the DB layer or API fails, but check logs if LLM graph extraction stops producing nodes.
