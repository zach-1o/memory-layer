"""
Router — Project namespace resolution.

Resolves (user_id, project_id) from authenticated request to an isolated
tenant database path. This is the single gateway that ensures all memory
operations are scoped correctly.
"""

import logging

from server.auth import AuthResult
from namespacing.tenant import Tenant, resolve_tenant

logger = logging.getLogger(__name__)


def resolve_project_namespace(auth: AuthResult, project_id: str) -> Tenant:
    """
    Resolve an authenticated request + project_id to an isolated tenant.

    Args:
        auth: Validated auth result containing user_id
        project_id: Project identifier from the MCP request

    Returns:
        Tenant with fully resolved, isolated database paths
    """
    if not project_id or not project_id.strip():
        raise ValueError("project_id is required and cannot be empty")

    tenant = resolve_tenant(
        user_id=auth.user_id,
        project_id=project_id.strip(),
    )

    logger.info(f"Resolved namespace: user={auth.user_id}, project={project_id} → {tenant.tenant_hash}")
    return tenant
