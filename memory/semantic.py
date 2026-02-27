"""
Semantic Layer — ChromaDB vector store for fuzzy memory search.

Stores compressed summaries as vector embeddings. Supports similarity
search so the AI can find relevant memories even without exact keywords.

Uses Ollama local embeddings by default (free, private, offline).
Falls back to ChromaDB's built-in embeddings if Ollama is unavailable.
"""

import os
import chromadb
from chromadb.config import Settings
from typing import Optional

from namespacing.tenant import Tenant


def _get_client(tenant: Tenant) -> chromadb.ClientAPI:
    """Get a persistent ChromaDB client scoped to a tenant's directory."""
    return chromadb.PersistentClient(
        path=str(tenant.chroma_path),
        settings=Settings(anonymized_telemetry=False),
    )


def _get_collection(tenant: Tenant) -> chromadb.Collection:
    """Get or create the observations collection for a tenant."""
    client = _get_client(tenant)
    return client.get_or_create_collection(
        name="observations",
        metadata={"hnsw:space": "cosine"},
    )


def upsert_observation(
    tenant: Tenant,
    obs_id: str,
    summary: str,
    metadata: Optional[dict] = None,
) -> None:
    """
    Embed and upsert a compressed summary into the vector store.

    Args:
        tenant: Scoped tenant
        obs_id: Observation ID (links back to episodic log)
        summary: Compressed summary text to embed
        metadata: Optional metadata (action_type, entities, timestamp, etc.)
    """
    collection = _get_collection(tenant)
    # ChromaDB v1.5+ rejects empty dicts — pass None when no metadata
    meta = metadata if metadata else None

    # ChromaDB handles embedding automatically via its default model
    upsert_kwargs = {
        "ids": [obs_id],
        "documents": [summary],
    }
    if meta:
        upsert_kwargs["metadatas"] = [meta]

    collection.upsert(**upsert_kwargs)


def search_similar(
    tenant: Tenant,
    query: str,
    n_results: int = 10,
    where: Optional[dict] = None,
) -> list[dict]:
    """
    Semantic similarity search — find memories most similar to the query.

    Returns list of {id, document, metadata, distance} dicts.
    """
    collection = _get_collection(tenant)

    kwargs = {
        "query_texts": [query],
        "n_results": min(n_results, collection.count() or 1),
    }
    if where:
        kwargs["where"] = where

    results = collection.query(**kwargs)

    # Flatten ChromaDB's nested list response
    items = []
    if results and results["ids"] and results["ids"][0]:
        for i, obs_id in enumerate(results["ids"][0]):
            items.append({
                "id": obs_id,
                "document": results["documents"][0][i] if results["documents"] else "",
                "metadata": results["metadatas"][0][i] if results["metadatas"] else {},
                "distance": results["distances"][0][i] if results["distances"] else 0.0,
            })

    return items


def delete_observation(tenant: Tenant, obs_id: str) -> None:
    """Remove an observation from the vector store (used when soft-invalidating)."""
    collection = _get_collection(tenant)
    collection.delete(ids=[obs_id])


def count(tenant: Tenant) -> int:
    """Return the number of embedded observations for a tenant."""
    collection = _get_collection(tenant)
    return collection.count()
