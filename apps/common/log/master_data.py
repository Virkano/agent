"""Minimal, value-free access audit for direct master-data read APIs."""

import hashlib
from functools import wraps

from system_manage.models import MasterDataAccessEvent


def master_data_read_audit(resource_model):
    def decorator(method):
        @wraps(method)
        def wrapped(view, request, *args, **kwargs):
            outcome = "SUCCESS"
            try:
                return method(view, request, *args, **kwargs)
            except Exception as exc:
                outcome = "DENIED" if getattr(exc, "status_code", None) in {401, 403} else "ERROR"
                raise
            finally:
                user = getattr(request, "user", None)
                scope = kwargs.get("user_id") or kwargs.get("task_id") or ""
                resolver_match = getattr(request, "resolver_match", None)
                route = getattr(resolver_match, "route", None) or "UNRESOLVED"
                MasterDataAccessEvent.objects.create(
                    workspace_id=str(kwargs.get("workspace_id") or "global"),
                    actor_id=str(getattr(user, "id", "") or ""),
                    resource_model=resource_model,
                    action="DETAIL" if kwargs.get("user_id") else "LIST",
                    outcome=outcome,
                    route_template=route[:512],
                    scope_hash=hashlib.sha256(str(scope).encode()).hexdigest() if scope else "",
                    query_keys=sorted(str(key) for key in request.query_params.keys()),
                )

        return wrapped

    return decorator
