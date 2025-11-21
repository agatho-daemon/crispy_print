// crispy_print_builder.js

// Route: /app/crispy-print-builder
frappe.pages["crispy-print-builder"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Crispy Print Builder"),
		single_column: true,
	});
};

frappe.pages["crispy-print-builder"].on_page_show = function (wrapper) {
	const $parent = $(wrapper).find(".layout-main-section");
	$parent.empty();
	$parent.html('<div id="crispy-print-root" style="height: 100vh;"></div>');
	
	// Mount Vue app
	if (window.mountCrispyPrint) {
		window.mountCrispyPrint("#crispy-print-root");
	} else {
		console.error("[CrispyPrint] mountCrispyPrint not found. Bundle may not be loaded.");
	}
};