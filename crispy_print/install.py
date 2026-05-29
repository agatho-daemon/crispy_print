from crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile import (
	ensure_default_branding_profiles_for_all_companies,
)


def after_install():
	ensure_default_branding_profiles_for_all_companies()
