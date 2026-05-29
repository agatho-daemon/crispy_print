from typing import Any

from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	get_branding_profile_presentation_settings as _get_branding_profile_presentation_settings,
)
from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	get_branding_profiles as _get_branding_profiles,
)

JSONDict = dict[str, Any]


def get_branding_profiles(company: str | None = None) -> list[JSONDict]:
	return _get_branding_profiles(company=company)


def get_branding_profile_presentation_settings(name: str) -> JSONDict:
	return _get_branding_profile_presentation_settings(name)
