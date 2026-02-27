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
