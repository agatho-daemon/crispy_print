from __future__ import annotations

import base64
import json
from copy import deepcopy
from typing import Any

import frappe
from frappe import _

from crispy_print.json_utils import parse_json_object, parse_json_value

from .company_context import resolve_effective_company
from .fiscal_credentials import get_fiscal_credential_doc

PROFILE_DOCTYPE = "Crispy Document Code Profile"
REGULATORY_PROFILE_DOCTYPE = "Crispy QR Regulatory Profile"
FISCAL_CREDENTIAL_DOCTYPE = "Crispy Fiscal Credential"

JSONDict = dict[str, Any]


def resolve_document_code(
	doctype: str,
	name: str,
	code_purpose: str = "Regulatory",
	environment: str = "Production",
	document_role: str | None = None,
	company: str | None = None,
	profile_name: str | None = None,
) -> JSONDict:
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	return resolve_document_code_for_doc(
		doc=doc,
		code_purpose=code_purpose,
		environment=environment,
		document_role=document_role,
		company=company,
		profile_name=profile_name,
	)


def generate_document_code(
	doctype: str,
	name: str,
	code_purpose: str = "Regulatory",
	environment: str = "Production",
	document_role: str | None = None,
	company: str | None = None,
	profile_name: str | None = None,
) -> JSONDict:
	doc = frappe.get_doc(doctype, name)
	doc.check_permission("read")
	return generate_document_code_for_doc(
		doc=doc,
		code_purpose=code_purpose,
		environment=environment,
		document_role=document_role,
		company=company,
		profile_name=profile_name,
	)


def resolve_document_code_for_doc(
	doc: Any,
	code_purpose: str = "Regulatory",
	environment: str = "Production",
	document_role: str | None = None,
	company: str | None = None,
	profile_name: str | None = None,
	allow_custom_methods: bool = True,
) -> JSONDict:
	company = resolve_effective_company(source_doc=doc, explicit_company=company)
	if not company:
		frappe.throw(_("Unable to resolve company for document code generation."))

	profile = _select_profile(
		doc=doc,
		company=company,
		environment=environment,
		code_purpose=code_purpose,
		document_role=document_role,
		profile_name=profile_name,
		allow_custom_methods=allow_custom_methods,
	)
	matched_rules = _get_matched_rules(
		profile,
		doc,
		document_role=document_role,
		throw_on_custom=allow_custom_methods,
	)
	regulatory_profile = _get_linked_regulatory_profile(profile)
	credential = _resolve_fiscal_credential(profile, company=company, environment=environment)
	resolved = _build_resolved_config(
		doc=doc,
		profile=profile,
		matched_rules=matched_rules,
		regulatory_profile=regulatory_profile,
		credential=credential,
		company=company,
		environment=environment,
		code_purpose=code_purpose,
		document_role=document_role,
	)
	return resolved


def generate_document_code_for_doc(
	doc: Any,
	code_purpose: str = "Regulatory",
	environment: str = "Production",
	document_role: str | None = None,
	company: str | None = None,
	profile_name: str | None = None,
	allow_custom_methods: bool = True,
) -> JSONDict:
	resolved = resolve_document_code_for_doc(
		doc=doc,
		code_purpose=code_purpose,
		environment=environment,
		document_role=document_role,
		company=company,
		profile_name=profile_name,
		allow_custom_methods=allow_custom_methods,
	)
	payload = _build_document_code_payload(doc, resolved)
	encoded_value = _encode_document_code_payload(payload, resolved)
	return {
		**resolved,
		"payload": payload,
		"encoded_value": encoded_value,
	}


def get_preferred_document_code_for_doc(
	doc: Any,
	purposes: list[str] | tuple[str, ...] | None = None,
	environments: list[str] | tuple[str, ...] | None = None,
	allow_custom_methods: bool = True,
) -> JSONDict | None:
	purposes = tuple(purposes or ("Regulatory", "Verification", "Portal Link", "Other"))
	environments = tuple(environments or ("Production", "Sandbox"))
	last_error: Exception | None = None
	original_messages = list(getattr(frappe.local, "message_log", []) or [])

	for environment in environments:
		for purpose in purposes:
			frappe.local.message_log = []
			try:
				result = generate_document_code_for_doc(
					doc=doc,
					code_purpose=purpose,
					environment=environment,
					allow_custom_methods=allow_custom_methods,
				)
			except Exception as exc:
				last_error = exc
				frappe.local.message_log = []
				continue
			success_messages = list(getattr(frappe.local, "message_log", []) or [])
			frappe.local.message_log = [*original_messages, *success_messages]
			return result

	frappe.local.message_log = original_messages
	if last_error:
		frappe.flags.crispy_document_code_error = str(last_error)
	return None


def _select_profile(
	doc: Any,
	company: str,
	environment: str,
	code_purpose: str,
	document_role: str | None,
	profile_name: str | None,
	allow_custom_methods: bool = True,
):
	if profile_name:
		profile = frappe.get_doc(PROFILE_DOCTYPE, profile_name)
		if not profile.enabled:
			frappe.throw(_("Selected Document Code Profile is disabled."))
		if profile.company != company:
			frappe.throw(_("Selected Document Code Profile does not belong to company {0}.").format(company))
		if profile.environment != environment:
			frappe.throw(
				_("Selected Document Code Profile environment does not match {0}.").format(environment)
			)
		return profile

	names = frappe.get_all(
		PROFILE_DOCTYPE,
		filters={
			"enabled": 1,
			"company": company,
			"environment": environment,
			"code_purpose": code_purpose,
		},
		fields=["name", "priority"],
		order_by="priority asc, modified desc",
	)
	applicable: list[tuple[int, str, Any]] = []
	for row in names:
		profile = frappe.get_doc(PROFILE_DOCTYPE, row["name"])
		matched_rules = _get_matched_rules(
			profile,
			doc,
			document_role=document_role,
			throw_on_custom=allow_custom_methods,
		)
		profile_rules = [rule for rule in (profile.document_rules or []) if rule.enabled]
		if profile_rules and not matched_rules:
			continue
		applicable.append((int(profile.priority or 100), profile.name, profile))

	if not applicable:
		frappe.throw(_("No enabled Document Code Profile matches this document context."))

	applicable.sort(key=lambda item: (item[0], item[1]))
	if len(applicable) > 1 and applicable[0][0] == applicable[1][0]:
		frappe.throw(_("Multiple Document Code Profiles match this document context with the same priority."))
	return applicable[0][2]


def _get_matched_rules(
	profile: Any,
	doc: Any,
	document_role: str | None = None,
	throw_on_custom: bool = True,
) -> list[Any]:
	matches: list[Any] = []
	for rule in sorted(
		profile.document_rules or [], key=lambda row: (int(row.priority or 100), row.idx or 0)
	):
		if not rule.enabled:
			continue
		if rule.document_type and rule.document_type != doc.doctype:
			continue
		if document_role and rule.document_role and rule.document_role != document_role:
			continue
		if _rule_matches(rule, doc, profile, throw_on_custom=throw_on_custom):
			matches.append(rule)
	return matches


def _rule_matches(rule: Any, doc: Any, profile: Any, throw_on_custom: bool = True) -> bool:
	condition_type = rule.condition_type or "Always"
	if condition_type == "Always":
		return True
	if condition_type == "Filter JSON":
		filters = parse_json_object(rule.condition_json, _("Condition JSON"))
		return _document_matches_filters(doc.as_dict(), filters)
	if condition_type == "Python Expression":
		return bool(
			frappe.safe_eval(
				rule.condition_expression,
				None,
				{
					"doc": doc.as_dict(),
					"profile": profile.as_dict(),
					"rule": rule.as_dict(),
				},
			)
		)
	if condition_type == "Custom Method":
		if not throw_on_custom:
			return False
		method = frappe.get_attr((rule.condition_expression or "").strip())
		return bool(method(doc=doc, profile=profile, rule=rule))
	return False


def _document_matches_filters(doc: Any, filters: JSONDict) -> bool:
	for path, expected in (filters or {}).items():
		actual = _get_value_by_path(doc, path)
		if not _match_filter_value(actual, expected):
			return False
	return True


def _match_filter_value(actual: Any, expected: Any) -> bool:
	if isinstance(expected, list) and len(expected) == 2 and isinstance(expected[0], str):
		operator, operand = expected[0].lower(), expected[1]
		if operator in {"=", "==", "eq"}:
			return actual == operand
		if operator in {"!=", "<>", "ne"}:
			return actual != operand
		if operator == "in":
			return actual in (operand or [])
		if operator == "not in":
			return actual not in (operand or [])
		if operator == ">":
			return actual is not None and actual > operand
		if operator == ">=":
			return actual is not None and actual >= operand
		if operator == "<":
			return actual is not None and actual < operand
		if operator == "<=":
			return actual is not None and actual <= operand
	return actual == expected


def _build_resolved_config(
	doc: Any,
	profile: Any,
	matched_rules: list[Any],
	regulatory_profile: Any | None,
	credential: Any | None,
	company: str,
	environment: str,
	code_purpose: str,
	document_role: str | None,
) -> JSONDict:
	profile_data = {
		"profile_name": profile.name,
		"company": company,
		"environment": environment,
		"code_purpose": code_purpose,
		"document_role": document_role,
		"code_format": profile.code_format,
		"code_symbology": profile.code_symbology,
		"payload_format": profile.payload_format,
		"output_encoding": profile.output_encoding,
		"error_correction": profile.error_correction,
		"quiet_zone": profile.quiet_zone,
		"module_size_pt": profile.module_size_pt,
		"datamatrix_encodation": _datamatrix_encodation_value(profile.datamatrix_encodation),
		"datamatrix_symbols": _datamatrix_symbols_value(profile.datamatrix_symbols),
		"content_source": profile.content_source,
		"payload_template": profile.payload_template,
		"selected_fields": _normalize_profile_selected_fields(profile, doc),
		"field_mapping": _normalize_json_dict(profile.field_mapping_json),
		"encoder_key": (profile.encoder_key or "custom").strip() or "custom",
		"encoder_settings": _normalize_json_dict(profile.encoder_settings_json),
		"requires_signature": bool(profile.requires_signature),
		"signature_method": profile.signature_method,
		"include_hash": bool(profile.include_hash),
		"hash_method": profile.hash_method,
		"requires_verification_url": bool(profile.requires_verification_url),
		"verification_url_template": profile.verification_url_template,
		"presentation": {
			"use_branding_profile_presentation": bool(profile.use_branding_profile_presentation),
			"code_label": profile.code_label,
			"width_mm": profile.width_mm,
			"height_mm": profile.height_mm,
		},
		"matched_rules": [rule.name for rule in matched_rules],
		"document": {"doctype": doc.doctype, "name": doc.name},
	}

	if regulatory_profile:
		profile_data["regulatory_profile"] = {
			"name": regulatory_profile.name,
			"authority_code": regulatory_profile.authority_code,
			"standard": regulatory_profile.standard,
			"version": regulatory_profile.version,
		}
	if credential:
		profile_data["fiscal_credential"] = {
			"name": credential.name,
			"company": credential.company,
			"environment": credential.environment,
			"authority_code": credential.authority_code,
			"regulatory_profile": credential.regulatory_profile,
		}

	for rule in sorted(matched_rules, key=lambda row: (int(row.priority or 100), row.idx or 0), reverse=True):
		if rule.payload_template_override:
			profile_data["payload_template"] = rule.payload_template_override
		if rule.selected_fields_json_override:
			profile_data["selected_fields"] = _normalize_selected_fields(rule.selected_fields_json_override)
		if rule.field_mapping_json_override:
			profile_data["field_mapping"] = _normalize_json_dict(rule.field_mapping_json_override)
		if rule.encoder_settings_json_override:
			profile_data["encoder_settings"] = _deep_merge(
				profile_data["encoder_settings"], _normalize_json_dict(rule.encoder_settings_json_override)
			)
		if rule.presentation_override_json:
			profile_data["presentation"] = _deep_merge(
				profile_data["presentation"], _normalize_json_dict(rule.presentation_override_json)
			)

	return profile_data


def _build_document_code_payload(doc: Any, resolved: JSONDict) -> Any:
	source = resolved.get("content_source") or "Encoder"
	if source == "Payload Template":
		return _render_payload_template(resolved.get("payload_template"), doc, resolved)
	if source == "Selected Fields":
		return _build_selected_fields_payload(doc, resolved)
	if source == "Verification URL":
		return _render_verification_url(doc, resolved)
	if source == "Static Text":
		text = resolved.get("payload_template")
		if not (text or "").strip():
			frappe.throw(_("Payload Template is required when Content Source is Static Text."))
		return str(text)
	if source == "Encoder":
		payload = _build_encoder_payload(doc, resolved)
		if resolved.get("requires_verification_url") and resolved.get("verification_url_template"):
			payload = {
				**(payload if isinstance(payload, dict) else {"value": payload}),
				"verification_url": _render_verification_url(doc, resolved),
			}
		return payload
	frappe.throw(_("Unsupported Content Source: {0}").format(source))


def _encode_document_code_payload(payload: Any, resolved: JSONDict) -> str:
	encoder_key = (resolved.get("encoder_key") or "custom").strip().lower()
	payload_format = (resolved.get("payload_format") or "Plain Text").strip()
	output_encoding = (resolved.get("output_encoding") or "Plain Text").strip()

	if encoder_key in {"url"}:
		base_value = str(payload)
	elif encoder_key in {"custom", "zatca_tlv", "gs1"}:
		base_value = _serialize_payload(payload, payload_format)
	else:
		frappe.throw(_("Unsupported encoder key: {0}").format(resolved.get("encoder_key")))

	encoded_value = _apply_output_encoding(
		base_value,
		payload if isinstance(payload, dict) else None,
		output_encoding,
	)
	_validate_final_document_code_payload(encoded_value, resolved)
	return encoded_value


def _serialize_payload(payload: Any, payload_format: str) -> str:
	if payload_format in {"Plain Text", "Text", "URL"}:
		return (
			payload
			if isinstance(payload, str)
			else json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
		)
	if payload_format == "JSON":
		return json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
	if payload_format == "XML":
		if isinstance(payload, str):
			return payload
		frappe.throw(_("XML payloads must be provided as rendered strings for now."))
	if payload_format == "TLV":
		if not isinstance(payload, dict):
			frappe.throw(_("TLV payloads must resolve to a JSON object."))
		return _encode_tlv_base64(payload)
	frappe.throw(_("Unsupported payload format: {0}").format(payload_format))


def _apply_output_encoding(base_value: str, payload_dict: JSONDict | None, output_encoding: str) -> str:
	if output_encoding == "Plain Text":
		return base_value
	if output_encoding == "Base64":
		if payload_dict is not None and _looks_like_base64(base_value):
			return base_value
		return base64.b64encode(base_value.encode("utf-8")).decode("ascii")
	if output_encoding == "URL Encoded":
		from urllib.parse import quote

		return quote(base_value, safe="")
	if output_encoding == "Hex":
		return base_value.encode("utf-8").hex()
	frappe.throw(_("Unsupported output encoding: {0}").format(output_encoding))


def _validate_final_document_code_payload(encoded_value: str, resolved: JSONDict) -> None:
	if (resolved.get("code_purpose") or "") != "Regulatory":
		return

	output_encoding = (resolved.get("output_encoding") or "Plain Text").strip()
	if output_encoding == "Plain Text":
		if encoded_value.isascii() or _allows_utf8_final_payload(resolved):
			return
		frappe.throw(
			_(
				"Regulatory Plain Text QR payload must be US-ASCII unless the regulatory profile explicitly allows UTF-8 final payloads."
			)
		)
	if output_encoding == "Base64":
		if _is_valid_base64_ascii(encoded_value):
			return
		frappe.throw(_("Regulatory Base64 QR payload must be valid US-ASCII Base64."))
	if output_encoding == "URL Encoded":
		if encoded_value.isascii() and not any(char.isspace() or ord(char) < 32 for char in encoded_value):
			return
		frappe.throw(_("Regulatory URL Encoded QR payload must be US-ASCII without raw whitespace."))
	if output_encoding == "Hex":
		if _is_hex_ascii(encoded_value):
			return
		frappe.throw(_("Regulatory Hex QR payload must be US-ASCII hexadecimal."))


def _allows_utf8_final_payload(resolved: JSONDict) -> bool:
	settings = resolved.get("encoder_settings")
	return isinstance(settings, dict) and settings.get("allow_utf8_final_payload") is True


def _is_valid_base64_ascii(value: str) -> bool:
	if not value.isascii():
		return False
	return _looks_like_base64(value)


def _is_hex_ascii(value: str) -> bool:
	if not value.isascii():
		return False
	text = str(value or "")
	return bool(text) and len(text) % 2 == 0 and all(char in "0123456789abcdefABCDEF" for char in text)


def _encode_tlv_base64(payload: JSONDict) -> str:
	buffer = bytearray()
	for index, value in enumerate(payload.values(), start=1):
		value_bytes = str(value or "").encode("utf-8")
		buffer.append(index)
		buffer.append(len(value_bytes))
		buffer.extend(value_bytes)
	return base64.b64encode(bytes(buffer)).decode("ascii")


def _build_selected_fields_payload(doc: Any, resolved: JSONDict) -> JSONDict:
	selected = resolved.get("selected_fields") or []
	mapping = resolved.get("field_mapping") or {}
	payload: JSONDict = {}

	if isinstance(selected, dict):
		for key, path in selected.items():
			payload[str(key)] = _get_value_by_path(doc.as_dict(), str(path))
		return payload

	for path in selected:
		source_path = str(path)
		output_key = str(mapping.get(source_path) or source_path.split(".")[-1])
		payload[output_key] = _get_value_by_path(doc.as_dict(), source_path)
	return payload


def _build_encoder_payload(doc: Any, resolved: JSONDict) -> Any:
	mapping = resolved.get("field_mapping") or {}
	if mapping:
		return {key: _get_value_by_path(doc.as_dict(), str(path)) for key, path in mapping.items()}
	selected = resolved.get("selected_fields") or []
	if selected:
		return _build_selected_fields_payload(doc, resolved)
	return {
		"doctype": doc.doctype,
		"name": doc.name,
		"company": _infer_company(doc.as_dict()),
	}


def _render_payload_template(template: str | None, doc: Any, resolved: JSONDict) -> Any:
	if not (template or "").strip():
		frappe.throw(_("Payload Template is required for this Document Code Profile."))
	rendered = frappe.render_template(
		template,
		{
			"doc": doc.as_dict(),
			"profile": resolved,
		},
	)
	parsed = _parse_json_if_possible(rendered)
	return parsed if parsed is not None else rendered


def _render_verification_url(doc: Any, resolved: JSONDict) -> str:
	template = resolved.get("verification_url_template")
	if not (template or "").strip():
		frappe.throw(_("Verification URL Template is required for this Document Code Profile."))
	return str(
		frappe.render_template(
			template,
			{
				"doc": doc.as_dict(),
				"profile": resolved,
			},
		)
	).strip()


def _resolve_fiscal_credential(profile: Any, company: str, environment: str) -> Any | None:
	if profile.fiscal_credential:
		doc = frappe.get_doc(FISCAL_CREDENTIAL_DOCTYPE, profile.fiscal_credential)
		if not _is_credential_active(doc):
			frappe.throw(_("Linked Fiscal Credential is not active."))
		return doc
	if profile.requires_signature and profile.regulatory_profile:
		return get_fiscal_credential_doc(
			company=company,
			regulatory_profile=profile.regulatory_profile,
			environment=environment,
		)
	return None


def _is_credential_active(doc: Any) -> bool:
	if not doc.enabled:
		return False
	now = frappe.utils.now_datetime()
	if doc.valid_from and frappe.utils.get_datetime(doc.valid_from) > now:
		return False
	if doc.valid_until and frappe.utils.get_datetime(doc.valid_until) < now:
		return False
	return True


def _get_linked_regulatory_profile(profile: Any) -> Any | None:
	if not profile.regulatory_profile:
		return None
	if not frappe.db.exists(REGULATORY_PROFILE_DOCTYPE, profile.regulatory_profile):
		return None
	return frappe.get_doc(REGULATORY_PROFILE_DOCTYPE, profile.regulatory_profile)


def _infer_company(doc: JSONDict) -> str | None:
	for key in ("company", "company_name"):
		value = doc.get(key)
		if value:
			return str(value)
	return None


def _normalize_selected_fields(value: Any) -> list[str] | JSONDict:
	if not value:
		return []
	parsed = parse_json_value(value, _("Selected fields"))
	if isinstance(parsed, dict):
		return parsed
	if isinstance(parsed, list):
		return [str(item) for item in parsed]
	frappe.throw(_("Selected fields must be a JSON array or object."))


def _normalize_profile_selected_fields(profile: Any, doc: Any) -> list[str] | JSONDict:
	rows = [
		row
		for row in (profile.selected_fields or [])
		if row.field_key and (not row.source_doctype or row.source_doctype == doc.doctype)
	]
	if rows:
		if any((row.output_key or "").strip() for row in rows):
			return {(row.output_key or row.field_key.split(".")[-1]).strip(): row.field_key for row in rows}
		return [row.field_key for row in rows]

	return _normalize_selected_fields(profile.selected_fields_json)


def _normalize_json_dict(value: Any) -> JSONDict:
	if not value:
		return {}
	return parse_json_object(value, _("JSON value"))


def _datamatrix_encodation_value(value: str | None) -> str:
	return {
		"ASCII": "ascii",
		"C40": "c40",
		"Text": "text",
		"X12": "x12",
		"EDIFACT": "edifact",
		"Base256": "base256",
	}.get(str(value or "").strip(), "")


def _datamatrix_symbols_value(value: str | None) -> str:
	return {
		"Square": "",
		"Rectangular": "rect",
		"DMRE": "rect-ext",
	}.get(str(value or "").strip(), "")


def _parse_json_if_possible(value: str) -> Any | None:
	text = str(value or "").strip()
	if not text or text[0] not in "[{":
		return None
	return parse_json_value(text, _("Rendered Payload Template"))


def _get_value_by_path(value: Any, path: str) -> Any:
	parts = [part for part in str(path or "").split(".") if part]
	return _get_value_by_parts(value, parts)


def _get_value_by_parts(value: Any, parts: list[str]) -> Any:
	if not parts:
		return value

	head, tail = parts[0], parts[1:]
	if isinstance(value, dict):
		return _get_value_by_parts(value.get(head), tail)
	if isinstance(value, list):
		if head.isdigit():
			index = int(head)
			next_value = value[index] if 0 <= index < len(value) else None
			return _get_value_by_parts(next_value, tail)
		return [_get_value_by_parts(item, parts) for item in value]
	return _get_value_by_parts(getattr(value, head, None), tail)


def _deep_merge(base: Any, override: Any) -> Any:
	if isinstance(base, dict) and isinstance(override, dict):
		merged = dict(base)
		for key, value in override.items():
			merged[key] = _deep_merge(merged.get(key), value)
		return merged
	return deepcopy(override)


def _looks_like_base64(value: str) -> bool:
	text = str(value or "").strip()
	if not text or len(text) % 4 != 0:
		return False
	try:
		base64.b64decode(text, validate=True)
		return True
	except Exception:
		return False
