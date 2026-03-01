"""
End-to-End Smoke Test: Memory Layer Cross-Session Retrieval

This script simulates the 'Amnesia Fix' scenario defined in EXPLAINER.md:
1. Session A: An AI fixes a simulated 'Mutex bug' and records observations.
2. Background: Compression and Graph Extraction run on Session A data.
3. Session B: A new AI session starts with no context.
4. Retrieval: Session B uses MCP tools to search the index, get the timeline,
   and trace the flow to completely understand Session A's fix without being fed
   the entire project history.
"""

import sys
import os
import asyncio
import logging

# Ensure the local memory-layer package is in the Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from namespacing.tenant import Tenant
from memory import episodic, semantic, graph, compression, graph_extractor
from server.mcp_handler import handle_tool_call

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger("SmokeTest")


async def run_smoke_test():
    # Use a dedicated fresh tenant for the smoke test
    tenant = Tenant(
        user_id="smoke_test_user",
        project_id="e2e_demo"
    )
    tenant.ensure_dirs()
    episodic.initialize(tenant)

    logger.info("====== Starting E2E Smoke Test ======")

    # ----------------------------------------------------------------
    # 1. Simulate Session A: Fixing the Mutex Bug
    # ----------------------------------------------------------------
    logger.info("--- Session A: Fixing the bug ---")
    session_a_id = "session_A_1001"
    
    # AI reads the file
    obs1_id = episodic.write_observation(
        tenant, session_a_id, "file_read", 
        "Read main.rs. Noticed that the save_settings function is locking the AppState Mutex but not releasing it if an error occurs.",
        ["main.rs", "save_settings", "AppState"]
    )
    
    # AI modifies the file
    obs2_id = episodic.write_observation(
        tenant, session_a_id, "file_edit", 
        "Fixed the Mutex deadlock in save_settings by using a scoped lock that drops automatically on error.",
        ["main.rs", "save_settings", "AppState", "ScopedLock"]
    )
    
    # AI modifies graph manually (in reality, tools would do this or extractor would find it)
    graph.add_edge(tenant, "save_settings", "main.rs", "LOCATED_IN")
    graph.add_edge(tenant, "save_settings", "AppState", "LOCKS")
    graph.add_edge(tenant, "ScopedLock", "AppState", "FIXES")
    
    # Trigger background tasks (simulating SessionEnd)
    logger.info("Triggering background compression and generic extraction...")
    
    # Mock compression to avoid requiring valid Anthropic API key
    async def mock_compress_batch(tenant_obj):
        conn = episodic._get_connection(tenant_obj)
        try:
            rows = conn.execute("SELECT id, raw_content, action_type, compressed_summary FROM observations WHERE compressed_summary = ''").fetchall()
            for row in rows:
                obs = dict(row)
                summary = "MOCK COMPRESSED: " + obs["raw_content"][:50]
                episodic.update_summary(tenant_obj, obs["id"], summary, len(summary.split()))
                semantic.upsert_observation(
                    tenant_obj,
                    obs_id=obs["id"],
                    summary=obs["raw_content"] + " " + summary,
                    metadata={"action_type": obs["action_type"]}
                )
            return len(rows)
        finally:
            conn.close()
    
    # Replace real function with mock for this test
    compression.compress_batch = mock_compress_batch
    
    await compression.compress_batch(tenant)
    # We skip actual Gemini extraction here to avoid quota issues and latency,
    # as we manually injected the critical edges above.
    
    
    # ----------------------------------------------------------------
    # 2. Simulate Session B: The "Amnesiac" AI Retries Context
    # ----------------------------------------------------------------
    logger.info("--- Session B: Cross-Session Retrieval ---")
    
    # Scenario: The user asks "What did we do with the Mutex deadlock?"
    # Debug search layers directly
    logger.info("DEBUG: FTS search results:")
    for doc in episodic.search_fts(tenant, "deadlock"):
        logger.info("  " + str(doc))
    logger.info("DEBUG: Semantic search results:")
    for doc in semantic.search_similar(tenant, "deadlock"):
        logger.info("  " + str(doc))
        
    logger.info("[Agent] Calling tool 'search_index' for 'deadlock'")
    search_res = await handle_tool_call(tenant, "search_index", {"query": "deadlock"})
    
    if not search_res:
        logger.error("❌ SEARCH FAILED: Could not find the previous fix in semantic index.")
        sys.exit(1)
        
    top_result = search_res[0]
    logger.info(f"✅ SEARCH SUCCESS: Found relevant observation! (ID: {top_result['id']}, Cost: {top_result['token_cost']} tokens)")
    
    # The AI now wants to see what happened around that fix
    logger.info(f"[Agent] Calling tool 'get_timeline' for observation {top_result['id']}")
    timeline_res = await handle_tool_call(tenant, "get_timeline", {"obs_id": top_result['id'], "window": 1})
    
    if not timeline_res or len(timeline_res) < 2:
         logger.error("❌ TIMELINE FAILED: Could not fetch chronological context.")
         sys.exit(1)
         
    logger.info("✅ TIMELINE SUCCESS: Retrieved previous and current actions:")
    for evt in timeline_res:
        logger.info(f"   -> [{evt['action_type']}] {evt.get('summary', '')}")
        
    # The AI wants to understand how the components are structurally related
    logger.info("[Agent] Calling tool 'trace_flow' between 'save_settings' and 'AppState'")
    trace_res = await handle_tool_call(tenant, "trace_flow", {"from_entity": "save_settings", "to_entity": "AppState"})
    
    if not trace_res or "path" not in trace_res or not trace_res["path"]:
        logger.error("❌ TRACE FLOW FAILED: Could not find graph path.")
        sys.exit(1)
        
    logger.info("✅ TRACE FLOW SUCCESS: Retrieved relationship path:")
    path_str = " -> ".join([step['entity'] if 'entity' in step else f"[{step.get('relationship', 'edge')}]" for step in trace_res["path"]])
    logger.info(f"   {path_str}")
    
    logger.info("====== Smoke Test PASSED! ======")
    logger.info("The agent successfully restored project context using progressive disclosure (search -> timeline -> trace) without a full context dump.")

if __name__ == "__main__":
    asyncio.run(run_smoke_test())
