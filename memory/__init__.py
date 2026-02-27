"""
Memory engine package — the three-layer storage system.

Layers:
  1. Episodic Log  (SQLite + FTS5)  — append-only diary
  2. Semantic Store (ChromaDB)      — vector similarity search
  3. Knowledge Graph (NetworkX)     — structural relationships
"""
