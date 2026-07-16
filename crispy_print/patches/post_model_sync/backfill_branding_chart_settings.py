import frappe

DEFAULTS = {
	"report_chart_horizontal_grid": 1,
	"report_chart_vertical_grid": 1,
	"report_chart_minor_grid": 0,
	"report_chart_grid_color": "#CBD5E1",
	"report_chart_grid_stroke_pt": 0.4,
	"report_chart_axis_color": "#64748B",
	"report_chart_axis_stroke_pt": 0.6,
	"report_chart_zero_line_color": "#475569",
	"report_chart_zero_line_stroke_pt": 1,
	"report_chart_legend_position": "Auto",
	"report_chart_label_size_pt": 8,
	"report_chart_data_labels": "Auto",
	"report_chart_line_stroke_pt": 1.2,
	"report_chart_marker_size_pt": 4,
	"report_chart_accessibility_mode": 1,
}


def execute():
	fieldnames = ["name", *DEFAULTS]
	for profile in frappe.get_all("Crispy Branding Profile", fields=fieldnames):
		updates = {
			fieldname: default
			for fieldname, default in DEFAULTS.items()
			if profile.get(fieldname) in (None, "")
		}
		if updates:
			frappe.db.set_value(
				"Crispy Branding Profile",
				profile.name,
				updates,
				update_modified=False,
			)
