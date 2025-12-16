// crispy_print_builder.js

// Route: /app/crispy-print-builder
frappe.pages["crispy-print-builder"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Crispy Print Builder"),
		single_column: true,
	});

	// Hot reload in development
	if (frappe.boot.developer_mode) {
		frappe.hot_update = frappe.hot_update || [];
		frappe.hot_update.push(() => load_crispy_print_builder(wrapper));
	}
};

frappe.pages["crispy-print-builder"].on_page_show = function (wrapper) {
	load_crispy_print_builder(wrapper);
};

function load_crispy_print_builder(wrapper) {
	let route = frappe.get_route();
	const parent = wrapper.querySelector(".layout-main-section");

	if (!parent) {
		console.error("[CrispyPrint] Page container not found");
		return;
	}

	parent.innerHTML = "";

	if (route.length > 1) {
		// Format specified in route - load builder with toolbar
		const format_name = route[1];
		const page = wrapper.page;

		// Clear existing actions
		page.clear_actions();
		page.clear_icons();
		page.clear_custom_actions();

		// Set page title
		page.set_title(__("Editing {0}", [format_name]));

		// Mount Vue app
		parent.innerHTML =
			'<div id="crispy-print-root" style="height: calc(100vh - 60px);"></div>';
		
		if (window.mountCrispyPrint) {
			const vueApp = window.mountCrispyPrint("#crispy-print-root");
			
			if (!vueApp) {
				console.error("[CrispyPrint] Failed to mount Vue app");
				return;
			}

			const store = vueApp.store;
			const component = vueApp.component;

			// Primary action: Save
			page.set_primary_action(__("Save"), () => {
				store.saveChanges();
			});

			// Secondary actions
			let reset_changes_btn = page
				.add_button(__("Reset Changes"), () => {
					store.resetLayout();
				})
				.get(0);

			let edit_properties_btn = page
				.add_button(__("Edit Crispy Properties"), () => {
					frappe.set_route("Form", "Crispy Format", format_name);
				})
				.get(0);

			// Menu items
			page.add_menu_item(__("Change Format"), () => {
				frappe.set_route("crispy-print-builder");
			});

			// Watch dirty state to update page indicator
			if (window.Vue && window.Vue.watch) {
				window.Vue.watch(
					() => store.dirty.value,
					(dirty) => {
						if (dirty) {
							page.set_indicator(__("Not Saved"), "orange");
							if (reset_changes_btn) {
								reset_changes_btn.style.display = "";
							}
						} else {
							page.clear_indicator();
							if (reset_changes_btn) {
								reset_changes_btn.style.display = "none";
							}
						}
					}
				);
			}

			// Initial button state
			if (reset_changes_btn) {
				reset_changes_btn.style.display = "none";
			}
		} else {
			console.error("[CrispyPrint] mountCrispyPrint not found. Bundle may not be loaded.");
		}
	} else {
		// No format specified - show dialog to create/edit
		let d = new frappe.ui.Dialog({
			title: __("Create or Edit Crispy Format"),
			get_primary_button_element() {
				const btn = d.get_primary_btn();
				return btn && btn.get ? btn.get(0) : btn;
			},
			fields: [
				{
					label: __("Action"),
					fieldname: "action",
					fieldtype: "Select",
					options: [
						{ label: __("Create New"), value: "Create" },
						{ label: __("Edit Existing"), value: "Edit" },
					],
					change() {
						let action = d.get_value("action");
						const primaryBtn = d.get_primary_button_element();
						if (primaryBtn) {
							primaryBtn.textContent =
								action === "Create" ? __("Create") : __("Edit");
						}
					},
				},
				{
					label: __("Select Document Type"),
					fieldname: "doctype",
					fieldtype: "Link",
					options: "DocType",
					filters: {
						istable: 0,
					},
					reqd: 1,
					default: frappe.route_options ? frappe.route_options.doctype : null,
				},
				{
					label: __("New Format Name"),
					fieldname: "format_name",
					fieldtype: "Data",
					depends_on: (doc) => doc.action === "Create",
					mandatory_depends_on: (doc) => doc.action === "Create",
				},
				{
					label: __("Select Crispy Format"),
					fieldname: "crispy_format",
					fieldtype: "Link",
					options: "Crispy Format",
					only_select: 1,
					depends_on: (doc) => doc.action === "Edit",
					get_query() {
						return {
							filters: {
								doc_type: d.get_value("doctype"),
							},
						};
					},
					mandatory_depends_on: (doc) => doc.action === "Edit",
				},
			],
			primary_action_label: __("Edit"),
			primary_action({ action, doctype, crispy_format, format_name }) {
				if (action === "Edit") {
					frappe.set_route("crispy-print-builder", crispy_format);
				} else if (action === "Create") {
					const primaryBtn = d.get_primary_button_element();
					if (primaryBtn) {
						primaryBtn.disabled = true;
					}
					frappe.db
						.insert({
							doctype: "Crispy Format",
							name: format_name,
							doc_type: doctype,
						})
						.then((doc) => {
							frappe.set_route("crispy-print-builder", doc.name);
						})
						.finally(() => {
							const enabledPrimaryBtn = d.get_primary_button_element();
							if (enabledPrimaryBtn) {
								enabledPrimaryBtn.disabled = false;
							}
						});
				}
			},
		});
		d.set_value("action", "Create");
		d.show();
	}
}
