# Lessons Learned

> After any correction or mistake, add the pattern here.
> Format: **Mistake** → **Rule derived**
> Review this file at the start of every session.

---

**Mistake:** Passed empty `{}` as metadata to ChromaDB `collection.upsert()`. ChromaDB v1.5+ raises `ValueError: Expected metadata to be a non-empty dict`.
→ **Rule:** Always pass `None` (not `{}`) to ChromaDB when there's no metadata. Guard with `meta = metadata if metadata else None` and conditionally include `metadatas` in the call.

**Mistake:** Used `python` or `py -3` to run pytest — both resolve to wrong Python installations (msys64 / Python 3.14) that lack project dependencies.
→ **Rule:** Always use the explicit path `C:\Users\HP\AppData\Local\Programs\Python\Python311\python.exe` (or set PATH priority) for running tests and the MCP server on this machine. Date: 2026-02-28.
