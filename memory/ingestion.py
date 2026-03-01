"""
Ingestion — Lifecycle hooks for memory capture.

Hooks:
  - SessionStart:  Initialize session, record start event
  - PostToolUse:   Record each agent action (file read, edit, search, etc.)
  - SessionEnd:    Record end event, trigger batch compression

These hooks are called by the MCP server to capture agent activity
into the three-layer memory system.
"""

import uuid
import asyncio
import logging
# Removed: from typing import Optional

from namespacing.tenant import Tenant
from memory import episodic, graph, compression, graph_extractor # Removed: semantic

logger = logging.getLogger(__name__)


class SessionManager:
    """Manages the lifecycle of a coding session."""

    def __init__(self, tenant: Tenant):
        self.tenant = tenant
        self.session_id = str(uuid.uuid4())
        self._observation_count = 0
        self._compression_threshold = 5  # Trigger compression after N observations

    def start_session(self) -> str:
        """
        Initialize a new session.
        Creates DB tables if needed and records the session start.
        """
        # Ensure episodic DB is initialized
        episodic.initialize(self.tenant)

        # Record session start
        obs_id = episodic.write_observation(
            tenant=self.tenant,
            session_id=self.session_id,
            action_type="session_start",
            raw_content=f"Session {self.session_id} started",
            entities=[],
        )

        logger.info(f"Session {self.session_id} started (obs: {obs_id})")
        return self.session_id

    def record_action(
        self,
        action_type: str,
        content: str,
        entities: list[str] | None = None,
        graph_operations: list[dict] | None = None,
    ) -> str:
        """
        Record an agent action (PostToolUse hook).

        Args:
            action_type: Type of action (file_read, file_edit, search, etc.)
            content: Raw content describing what happened
            entities: List of entity names mentioned
            graph_operations: Optional list of graph mutations to apply
                Each dict: {action: 'add_node'|'add_edge'|'invalidate', ...params}

        Returns:
            The observation ID
        """
        # Write to episodic log
        obs_id = episodic.write_observation(
            tenant=self.tenant,
            session_id=self.session_id,
            action_type=action_type,
            raw_content=content,
            entities=entities,
        )

        # Auto-populate knowledge graph from entities (CO_OCCURS)
        if entities and len(entities) > 0:
            try:
                for entity_name in entities:
                    graph.add_node(
                        self.tenant, entity_name, node_type="entity"
                    )
                # Connect entities that appear together in the same observation
                for i, e1 in enumerate(entities):
                    for e2 in entities[i + 1 :]:
                        graph.add_edge(
                            self.tenant, e1, e2, relationship="CO_OCCURS"
                        )
            except Exception as e:
                logger.error(f"Auto-graph population failed: {e}")

        # Apply explicit graph operations if provided
        if graph_operations:
            for op in graph_operations:
                try:
                    self._apply_graph_op(op)
                except Exception as e:
                    logger.error(f"Graph operation failed: {e}")

        # Check if we should trigger background compression
        self._observation_count += 1
        if self._observation_count >= self._compression_threshold:
            self._trigger_compression()
            self._observation_count = 0

        # Trigger background graph extraction (async, never blocks)
        self._trigger_graph_extraction(obs_id, content, entities)

        return obs_id

    def end_session(self) -> str:
        """
        End the current session.
        Records the event and triggers final compression.
        """
        obs_id = episodic.write_observation(
            tenant=self.tenant,
            session_id=self.session_id,
            action_type="session_end",
            raw_content=f"Session {self.session_id} ended",
            entities=[],
        )

        # Trigger final compression for any remaining uncompressed observations
        self._trigger_compression()

        logger.info(f"Session {self.session_id} ended (obs: {obs_id})")
        return obs_id

    def _apply_graph_op(self, op: dict) -> None:
        """Apply a single graph operation."""
        action = op.get("action")

        if action == "add_node":
            graph.add_node(
                self.tenant,
                name=op["name"],
                node_type=op.get("type", "unknown"),
                metadata=op.get("metadata"),
            )
        elif action == "add_edge":
            graph.add_edge(
                self.tenant,
                source=op["source"],
                target=op["target"],
                relationship=op["relationship"],
                metadata=op.get("metadata"),
            )
        elif action == "invalidate_node":
            graph.invalidate_node(
                self.tenant,
                name=op["name"],
                replaced_by=op.get("replaced_by"),
            )
        elif action == "invalidate_edge":
            graph.invalidate_edge(
                self.tenant,
                source=op["source"],
                target=op["target"],
            )
        else:
            logger.warning(f"Unknown graph operation: {action}")

    def _trigger_compression(self) -> None:
        """Trigger background compression. Never blocks the caller."""
        try:
            # Fire and forget — compression failures must never block MCP
            asyncio.get_event_loop().create_task(
                compression.compress_batch(self.tenant)
            )
        except RuntimeError:
            # No event loop running — skip compression (will be caught at session end)
            logger.debug("No event loop available for background compression")

    def _trigger_graph_extraction(self, obs_id: str, raw_content: str, entities: list) -> None:
        """Trigger background LLM graph extraction. Never blocks the caller."""
        try:
            import json
            entities_str = json.dumps(entities) if isinstance(entities, list) else str(entities)
            asyncio.get_event_loop().create_task(
                graph_extractor.extract_and_apply(
                    self.tenant, obs_id, raw_content, entities_str
                )
            )
        except RuntimeError:
            logger.debug("No event loop available for background graph extraction")
