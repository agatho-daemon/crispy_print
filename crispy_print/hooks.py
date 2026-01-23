from . import __version__ as app_version

app_name = "crispy_print"
app_title = "Crispy Print"
app_publisher = "Agathodaemon"
app_description = (
	"A Frappe App that uses Typst CLI engine with Vue based frontend to format DocType print formats."
)
app_email = "agatho_daemon@icloud.com"
app_license = "mit"


# include js, css files in header of desk.html
app_include_js = [
	"crispy_print.bundle.js",
	"crispy_preview.bundle.js",
	"/assets/crispy_print/js/crispy_print_button.js",
	"/assets/crispy_print/js/report_button.js",
]
