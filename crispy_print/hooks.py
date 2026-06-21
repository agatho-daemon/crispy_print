import frappe
from packaging.version import parse

from . import __version__ as app_version

app_name = "crispy_print"
app_title = "Crispy Print"
app_publisher = "Agathodaemon"
app_description = (
	"A Frappe App that uses Typst CLI engine with Vue based frontend to format DocType print formats."
)
app_email = "agatho_daemon@icloud.com"
app_license = "MIT"
app_logo_url = "/assets/crispy_print/icons/crispy-print-logo.svg"

# include js, css files in header of desk.html
app_include_js = [
	# "crispy_print.bundle.js",
	# "crispy_preview.bundle.js",
	"report_button.bundle.js",
	"/assets/crispy_print/js/crispy_print_button.js",
]

fixtures = [{"dt": "Crispy Format"}]

after_install = "crispy_print.install.after_install"

doc_events = {
	"Company": {
		"after_insert": "crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile.on_company_after_insert"
	},
	"Letter Head": {
		"validate": "crispy_print.letterhead_lifecycle.on_letterhead_validate",
	},
}

version = parse(frappe.__version__)

if version.major in (14, 15):
	app_include_icons = [
		"crispy_print/icons/crispy-print-logo.svg",
	]

# TODO: WIP Required for Frappe 16+
# if version.major > 15:
# 	add_to_apps_screen = [
# 		{
# 			"name": app_name,
# 			"logo": app_logo_url,
# 			"title": app_title,
# 			"route": "/crispy-print",
# 			# "has_permission": "crispy_print.api.check_app_permission"
# 		}
# 	]
