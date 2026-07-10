import time
from collections.abc import Callable, Iterable
from functools import wraps
from typing import Any

import frappe
from frappe import _


def ensure_compile_typst_permission() -> None:
	if frappe.session.user == "Administrator":
		return

	allowed_roles = {
		"System Manager",
		"Crispy Print User",
		"Crispy Print Manager",
		"Crispy Print Designer",
	}
	if allowed_roles.intersection(set(frappe.get_roles())):
		return

	if frappe.has_permission("Crispy Format", "read") or frappe.has_permission(
		"Crispy Branding Profile", "read"
	):
		return

	frappe.throw(_("Not permitted to compile Typst."), frappe.PermissionError)


def ensure_crispy_print_manager_permission() -> None:
	if frappe.session.user == "Administrator":
		return

	allowed_roles = {"System Manager", "Crispy Print Manager"}
	if allowed_roles.intersection(set(frappe.get_roles())):
		return

	frappe.throw(_("Not permitted."), frappe.PermissionError)


def ensure_doctype_read_permission(doctype: str) -> None:
	if not frappe.has_permission(doctype, "read"):
		frappe.throw(_("Not permitted to read {0}.").format(doctype), frappe.PermissionError)


def ensure_doctype_permission(doctype: str, ptype: str) -> None:
	if not frappe.has_permission(doctype, ptype):
		frappe.throw(
			_("Not permitted to {0} {1}.").format(ptype, doctype),
			frappe.PermissionError,
		)


def enforce_rate_limit(
	key: str,
	limit: int = 60,
	window_seconds: int = 60,
	error_message: str | None = None,
) -> None:
	"""Apply a per-site/per-user sliding-window rate limit.

	Uses Redis sorted sets when available. Falls back to the Frappe cache key API
	if the deployment exposes only the basic cache interface.
	"""
	cache = frappe.cache()
	site = getattr(frappe.local, "site", "default")
	user = frappe.session.user or "Guest"
	now = time.time()
	cache_key = f"crispy_print:rate:{key}:{site}:{user}"
	message = error_message or _("Too many requests. Please wait a moment and try again.")

	try:
		redis = getattr(cache, "redis_server", None)
		if redis:
			member = f"{now:.6f}"
			pipe = redis.pipeline()
			pipe.zremrangebyscore(cache_key, 0, now - window_seconds)
			pipe.zadd(cache_key, {member: now})
			pipe.zcard(cache_key)
			pipe.expire(cache_key, window_seconds + 5)
			results = pipe.execute()
			if not isinstance(results, list | tuple) or len(results) < 3:
				return
			count = int(results[2])
			if count > limit:
				redis.zrem(cache_key, member)
				frappe.throw(message, frappe.ValidationError)
			return
	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Crispy Print sliding rate limit failed",
		)

	bucket = int(now // window_seconds)
	fallback_key = f"{cache_key}:{bucket}"
	try:
		count = int(cache.get_value(fallback_key) or 0)
	except (TypeError, ValueError):
		return
	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Crispy Print rate limit check failed",
		)
		return

	if count >= limit:
		frappe.throw(message, frappe.ValidationError)

	try:
		cache.set_value(fallback_key, count + 1, expires_in_sec=window_seconds + 5)
	except Exception:
		frappe.log_error(
			message=frappe.get_traceback(),
			title="Crispy Print rate limit update failed",
		)


def rate_limited(
	key: str,
	limit: int = 60,
	window_seconds: int = 60,
) -> Callable:
	def decorator(fn: Callable) -> Callable:
		@wraps(fn)
		def wrapper(*args, **kwargs):
			enforce_rate_limit(key, limit=limit, window_seconds=window_seconds)
			return fn(*args, **kwargs)

		return wrapper

	return decorator


EndpointPermission = tuple[str, str]


def endpoint_policy(
	*,
	rate_key: str | None = None,
	limit: int = 60,
	window_seconds: int = 60,
	permissions: Iterable[EndpointPermission] | None = None,
	manager_only: bool = False,
	delegated: bool = False,
	exempt_reason: str | None = None,
) -> Callable:
	"""Declare and optionally enforce policy for a whitelisted v1 endpoint."""
	permission_list = tuple(permissions or ())
	policy: dict[str, Any] = {
		"rate_key": rate_key,
		"limit": limit if rate_key else None,
		"window_seconds": window_seconds if rate_key else None,
		"permissions": permission_list,
		"manager_only": manager_only,
		"delegated": delegated,
		"exempt_reason": exempt_reason,
	}

	def decorator(fn: Callable) -> Callable:
		@wraps(fn)
		def wrapper(*args, **kwargs):
			if manager_only:
				ensure_crispy_print_manager_permission()
			for doctype, ptype in permission_list:
				ensure_doctype_permission(doctype, ptype)
			if rate_key:
				enforce_rate_limit(rate_key, limit=limit, window_seconds=window_seconds)
			return fn(*args, **kwargs)

		wrapper.__crispy_endpoint_policy__ = policy
		return wrapper

	return decorator
