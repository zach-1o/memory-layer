"""
Scoping — enforces zero cross-project memory bleed.

Provides a context manager that binds all memory operations to a specific
tenant namespace. Any storage call made outside a scope raises an error.
"""

from __future__ import annotations

import contextvars
from contextlib import contextmanager
from typing import Generator

from namespacing.tenant import Tenant, resolve_tenant

# Thread-/async-safe context variable holding the current tenant
_current_tenant: contextvars.ContextVar[Tenant | None] = contextvars.ContextVar(
    "_current_tenant", default=None
)


class ScopeError(Exception):
    """Raised when a memory operation is attempted outside a tenant scope."""
    pass


@contextmanager
def tenant_scope(user_id: str, project_id: str) -> Generator[Tenant, None, None]:
    """
    Context manager that binds all enclosed memory operations to a tenant.

    Usage:
        with tenant_scope(user_id, project_id) as tenant:
            episodic.write(tenant, ...)
            graph.add_node(tenant, ...)
    """
    tenant = resolve_tenant(user_id, project_id)
    token = _current_tenant.set(tenant)
    try:
        yield tenant
    finally:
        _current_tenant.reset(token)


def get_current_tenant() -> Tenant:
    """
    Get the tenant for the current scope. Raises ScopeError if called
    outside a tenant_scope context manager.
    """
    tenant = _current_tenant.get()
    if tenant is None:
        raise ScopeError(
            "Memory operation attempted outside a tenant scope. "
            "Wrap your call in `with tenant_scope(user_id, project_id):`"
        )
    return tenant


def require_tenant(tenant: Tenant | None = None) -> Tenant:
    """
    Convenience: accept an explicit tenant or fall back to the scoped one.
    Ensures every storage function always has a valid tenant.
    """
    if tenant is not None:
        return tenant
    return get_current_tenant()
