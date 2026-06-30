app_name = "crispy_print"
app_title = "Crispy Print"
app_publisher = "Agathodaemon"
app_description = (
	"A Frappe App that uses Typst CLI engine with Vue based frontend to format DocType print formats."
)
app_email = "agatho_daemon@icloud.com"
app_license = "MIT"
app_logo_url = "/assets/crispy_print/icons/crispy-print-logo.svg"

# START VERSION COMPATIBILITY
# Version compatibility for Frappe Desk routes and icon loading.

from frappe import __version__ as frappe_version

frappe_major = int(frappe_version.lstrip("v").split(".", 1)[0])

if frappe_major >= 16:
	app_home = "/desk/crispy-studio"
	app_include_icons = [
		"/assets/crispy_print/icons/sprite-crispy-print-logo.svg",
	]
else:
	app_home = "/app/crispy"
	app_include_icons = [
		"crispy_print/icons/sprite-crispy-print-logo.svg",
	]

add_to_apps_screen = [
	{
		"name": app_name,
		"logo": app_logo_url,
		"title": app_title,
		"route": app_home,
		"has_permission": "crispy_print.check_app_permission",
	}
]
# END VERSION COMPATIBILITY


# include js, css files in header of desk.html
app_include_js = [
	# "crispy_print.bundle.js",
	# "crispy_preview.bundle.js",
	"report_button.bundle.js",
	"/assets/crispy_print/js/crispy_print_button.js",
]

fixtures = [{"dt": "Crispy Format"}]

after_install = "crispy_print.install.after_install"
after_sync = "crispy_print.install.after_sync"
before_uninstall = "crispy_print.install.before_uninstall"

doc_events = {
	"Company": {
		"after_insert": "crispy_print.crispy_print.doctype.crispy_branding_profile.crispy_branding_profile.on_company_after_insert"
	},
	"Letter Head": {
		"validate": "crispy_print.letterhead_lifecycle.on_letterhead_validate",
	},
}
