"""
FastAPI Entrypoint — MCP Gateway API.

Hosts the MCP server with Streamable HTTP transport.
Supports both JSON and SSE response modes per MCP spec.

Start with:
    python -m uvicorn server.main:app --host 0.0.0.0 --port 8000
"""

import os
import sys
import json
import uuid
import logging
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request, HTTPException, Response
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from server.auth import authenticate_request, register_api_key
from server.router import resolve_project_namespace
from server.mcp_handler import TOOL_DEFINITIONS, handle_tool_call

load_dotenv()

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan — startup and shutdown hooks."""
    logger.info("🧠 Memory Layer MCP Server starting...")

    # Register a default dev API key for local testing
    register_api_key("skp_dev_key_12345", user_id="dev_user", key_name="dev-local")
    logger.info("📝 Registered dev API key: skp_dev_key_12345")

    # Register production key from environment if present
    env_api_key = os.getenv("MEMLAYER_API_KEY")
    if env_api_key:
        register_api_key(env_api_key, user_id="production_user", key_name="production-env")
        logger.info(f"📝 Registered API key from environment: {env_api_key[:8]}...")

    yield

    logger.info("🧠 Memory Layer MCP Server shutting down...")


app = FastAPI(
    title="Memory Layer — AI Persistent Memory Service",
    description="MCP-compatible persistent memory for AI coding assistants",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS for dashboard
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Mcp-Session-Id"],
)


@app.get("/health")
async def health_check():
    """Health check endpoint for Docker/monitoring."""
    return {"status": "ok", "service": "memory-layer"}


def _handle_mcp_method(method: str, params: dict, req_id, auth) -> dict | None:
    """
    Handle an MCP JSON-RPC method call. Returns the result dict,
    or None for notifications (no response expected).
    """
    if method == "initialize":
        return {
            "protocolVersion": "2024-11-05",
            "capabilities": {
                "tools": {"listChanged": False},
            },
            "serverInfo": {
                "name": "memory-layer",
                "version": "0.1.0",
            },
        }

    elif method == "notifications/initialized":
        return None  # Notification — no response

    elif method == "tools/list":
        return {"tools": TOOL_DEFINITIONS}

    elif method == "tools/call":
        tool_name = params.get("name", "")
        arguments = params.get("arguments", {})

        # Extract project_id from arguments
        project_id = arguments.pop("project_id", None)
        if not project_id:
            raise ValueError("project_id is required in arguments")

        # Resolve tenant namespace
        tenant = resolve_project_namespace(auth, project_id)

        # Dispatch tool call (sync wrapper since we handle async at the endpoint level)
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(handle_tool_call(tenant, tool_name, arguments))

        return {
            "content": [
                {
                    "type": "text",
                    "text": json.dumps(result, default=str),
                }
            ],
        }

    else:
        raise ValueError(f"Method not found: {method}")


@app.post("/mcp")
async def mcp_endpoint(request: Request):
    """
    MCP Streamable HTTP endpoint.

    Handles JSON-RPC 2.0 requests with proper Streamable HTTP transport:
    - Single requests return JSON
    - Notifications return 202 Accepted (no body)
    - Supports Mcp-Session-Id header for session tracking
    """
    # Authenticate
    auth = await authenticate_request(request)

    # Parse JSON-RPC request
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(
            content={"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": "Parse error"}},
            status_code=400,
        )

    # Get or create session ID
    session_id = request.headers.get("Mcp-Session-Id", str(uuid.uuid4()))

    # Handle batch requests (array of JSON-RPC calls)
    if isinstance(body, list):
        responses = []
        for item in body:
            resp = await _process_single_request(item, auth)
            if resp is not None:
                responses.append(resp)
        if not responses:
            return Response(status_code=202, headers={"Mcp-Session-Id": session_id})
        return JSONResponse(
            content=responses,
            headers={"Mcp-Session-Id": session_id},
        )

    # Single request
    resp = await _process_single_request(body, auth)

    if resp is None:
        # Notification — return 202 with no body
        return Response(status_code=202, headers={"Mcp-Session-Id": session_id})

    return JSONResponse(
        content=resp,
        headers={"Mcp-Session-Id": session_id},
    )


@app.get("/mcp")
async def mcp_sse_endpoint(request: Request):
    """
    SSE endpoint for server-initiated messages (optional).
    Returns 405 since we don't use server-initiated SSE.
    """
    return Response(status_code=405, content="SSE not supported, use POST")


@app.delete("/mcp")
async def mcp_delete_session(request: Request):
    """Delete/close an MCP session."""
    return Response(status_code=200)


async def _process_single_request(body: dict, auth) -> dict | None:
    """Process a single JSON-RPC request and return the response dict, or None for notifications."""
    req_id = body.get("id")
    method = body.get("method", "")
    params = body.get("params", {})

    # Notifications have no "id" field — no response expected
    is_notification = "id" not in body

    try:
        if method == "tools/call":
            # Async tool calls
            tool_name = params.get("name", "")
            arguments = dict(params.get("arguments", {}))
            project_id = arguments.pop("project_id", None)

            if not project_id:
                if is_notification:
                    return None
                return _jsonrpc_error(req_id, -32602, "project_id is required in arguments")

            tenant = resolve_project_namespace(auth, project_id)
            result = await handle_tool_call(tenant, tool_name, arguments)

            if is_notification:
                return None

            return _jsonrpc_result(req_id, {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, default=str),
                    }
                ],
            })

        elif method == "initialize":
            result = {
                "protocolVersion": "2024-11-05",
                "capabilities": {
                    "tools": {"listChanged": False},
                },
                "serverInfo": {
                    "name": "memory-layer",
                    "version": "0.1.0",
                },
            }
            if is_notification:
                return None
            return _jsonrpc_result(req_id, result)

        elif method == "notifications/initialized":
            return None  # Always a notification

        elif method == "tools/list":
            if is_notification:
                return None
            return _jsonrpc_result(req_id, {"tools": TOOL_DEFINITIONS})

        elif method == "ping":
            if is_notification:
                return None
            return _jsonrpc_result(req_id, {})

        else:
            if is_notification:
                return None
            return _jsonrpc_error(req_id, -32601, f"Method not found: {method}")

    except ValueError as e:
        if is_notification:
            return None
        return _jsonrpc_error(req_id, -32602, str(e))
    except Exception as e:
        logger.error(f"Tool call failed: {e}", exc_info=True)
        if is_notification:
            return None
        return _jsonrpc_error(req_id, -32603, f"Internal error: {str(e)}")


# --- Dashboard API endpoints (for the React UI) ---

@app.get("/api/projects")
async def list_projects(request: Request):
    """List all known projects with basic stats for the dashboard home screen."""
    await authenticate_request(request)
    import os, json, sqlite3
    from pathlib import Path

    db_root = Path(os.getenv("DB_ROOT", "./db"))
    projects = []

    if not db_root.exists():
        return projects

    for tenant_dir in db_root.iterdir():
        if not tenant_dir.is_dir():
            continue

        project_info = {
            "tenant_hash": tenant_dir.name,
            "project_id": tenant_dir.name[:8],  # short display name
            "obs_count": 0,
            "entity_count": 0,
            "session_count": 0,
            "last_active": None,
        }

        # Read episodic.sqlite for obs count + sessions + last active
        episodic_path = tenant_dir / "episodic.sqlite"
        if episodic_path.exists():
            try:
                conn = sqlite3.connect(str(episodic_path))
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM observations")
                project_info["obs_count"] = cur.fetchone()[0]
                cur.execute("SELECT COUNT(DISTINCT session_id) FROM observations")
                project_info["session_count"] = cur.fetchone()[0]
                cur.execute("SELECT MAX(timestamp) FROM observations")
                row = cur.fetchone()
                project_info["last_active"] = row[0] if row else None
                # Try to read the original project_id from the first session
                cur.execute("SELECT raw_content FROM observations WHERE action_type='session_start' LIMIT 1")
                row = cur.fetchone()
                if row and row[0]:
                    # Session start content often contains the project name
                    project_info["project_id"] = row[0][:50] if len(row[0]) > 2 else project_info["project_id"]
                conn.close()
            except Exception:
                pass

        # Read graph.json for entity count
        graph_path = tenant_dir / "graph.json"
        if graph_path.exists():
            try:
                with open(graph_path, "r") as f:
                    graph_data = json.load(f)
                project_info["entity_count"] = len(graph_data.get("nodes", []))
            except Exception:
                pass

        # Only include if there's actual data
        if project_info["obs_count"] > 0:
            projects.append(project_info)

    # Sort by last_active descending
    projects.sort(key=lambda p: p.get("last_active") or "", reverse=True)
    return projects

# Helper: resolve tenant by raw hash (for dashboard, avoids double-hashing)
def _resolve_tenant_by_hash(tenant_hash: str):
    """Create a Tenant-like object from a raw hash (for dashboard endpoints)."""
    import os
    from pathlib import Path
    from types import SimpleNamespace
    db_root = Path(os.getenv("DB_ROOT", "./db"))
    db_path = db_root / tenant_hash
    return SimpleNamespace(
        tenant_hash=tenant_hash,
        db_path=db_path,
        episodic_db_path=db_path / "episodic.sqlite",
        chroma_path=db_path / "chroma",
        graph_path=db_path / "graph.json",
    )

@app.get("/api/observations")
async def list_observations(request: Request, project_id: str, limit: int = 50):
    """List recent observations for the dashboard."""
    await authenticate_request(request)
    tenant = _resolve_tenant_by_hash(project_id)
    from memory import episodic
    episodic.initialize(tenant)
    return episodic.get_recent(tenant, limit=limit)


@app.get("/api/graph")
async def get_graph(request: Request, project_id: str):
    """Get the full knowledge graph for visualization."""
    await authenticate_request(request)
    tenant = _resolve_tenant_by_hash(project_id)
    from memory import graph as graph_module
    nodes = graph_module.get_all_nodes(tenant, include_invalidated=True)
    edges = graph_module.get_all_edges(tenant, include_invalidated=True)
    return {"nodes": nodes, "edges": edges}


@app.get("/api/search")
async def search_observations(request: Request, project_id: str, q: str):
    """Search observations for the dashboard."""
    await authenticate_request(request)
    tenant = _resolve_tenant_by_hash(project_id)
    from memory import episodic
    episodic.initialize(tenant)
    return episodic.search_fts(tenant, q)


@app.post("/api/observations/{obs_id}/invalidate")
async def invalidate_observation(request: Request, obs_id: str, project_id: str):
    """Soft-invalidate an observation (never hard-delete per agent.md)."""
    await authenticate_request(request)
    tenant = _resolve_tenant_by_hash(project_id)
    from memory import episodic
    episodic.initialize(tenant)
    success = episodic.invalidate(tenant, obs_id)
    if not success:
        raise HTTPException(status_code=404, detail="Observation not found or already invalidated")
    return {"status": "invalidated", "obs_id": obs_id}


@app.post("/api/observations/{obs_id}/summary")
async def update_observation_summary(request: Request, obs_id: str, project_id: str):
    """Update the compressed summary for an observation (inline edit from dashboard)."""
    await authenticate_request(request)
    tenant = _resolve_tenant_by_hash(project_id)
    body = await request.json()
    summary = body.get("summary", "")
    token_count = len(summary) // 4
    from memory import episodic
    episodic.initialize(tenant)
    episodic.update_summary(tenant, obs_id, summary, token_count)
    return {"status": "updated", "obs_id": obs_id, "token_count": token_count}


# --- Key Management API (for Dashboard Key Manager) ---

@app.get("/api/keys")
async def list_api_keys(request: Request):
    """List all API keys for the authenticated user."""
    await authenticate_request(request)
    from server.auth import _init_keys_db, DB_ROOT
    import sqlite3
    _init_keys_db()
    db_path = DB_ROOT / "_keys.sqlite"
    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(
            "SELECT key_hash, user_id, key_name, key_prefix, created_at, revoked_at FROM api_keys ORDER BY created_at DESC"
        ).fetchall()
        return [dict(r) for r in rows]
    finally:
        conn.close()


@app.post("/api/keys")
async def generate_api_key(request: Request):
    """Generate a new API key."""
    auth = await authenticate_request(request)
    import secrets
    body = await request.json()
    key_name = body.get("key_name", "default")
    # Generate a secure random key with skp_ prefix
    raw_key = f"skp_{secrets.token_urlsafe(32)}"
    key_hash = register_api_key(raw_key, user_id=auth.user_id, key_name=key_name)
    return {"api_key": raw_key, "key_hash": key_hash, "key_name": key_name}


@app.delete("/api/keys/{key_hash}")
async def revoke_api_key(request: Request, key_hash: str):
    """Revoke an API key by its hash."""
    await authenticate_request(request)
    from server.auth import _init_keys_db, DB_ROOT
    import sqlite3
    _init_keys_db()
    db_path = DB_ROOT / "_keys.sqlite"
    conn = sqlite3.connect(str(db_path))
    try:
        conn.execute(
            "UPDATE api_keys SET revoked_at = datetime('now') WHERE key_hash = ?",
            (key_hash,),
        )
        conn.commit()
    finally:
        conn.close()
    return {"status": "revoked", "key_hash": key_hash}


# --- JSON-RPC helpers ---

def _jsonrpc_result(req_id, result):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "result": result,
    }


def _jsonrpc_error(req_id, code, message):
    return {
        "jsonrpc": "2.0",
        "id": req_id,
        "error": {"code": code, "message": message},
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("server.main:app", host=HOST, port=PORT, reload=True)
