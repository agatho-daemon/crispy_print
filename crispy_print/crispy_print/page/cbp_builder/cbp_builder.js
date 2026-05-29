frappe.pages["cbp-builder"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Crispy Branding Profile Builder"),
		single_column: true,
	});

	if (frappe.boot.developer_mode) {
		frappe.hot_update = frappe.hot_update || [];
		frappe.hot_update.push(() => load_cbp_builder(wrapper));
	}
};

frappe.pages["cbp-builder"].on_page_show = function (wrapper) {
	load_cbp_builder(wrapper);
};

function load_cbp_builder(wrapper) {
	const route = frappe.get_route();
	const parent = wrapper.querySelector(".layout-main-section");
	const page = wrapper.page;

	if (!parent) {
		console.error("[CrispyPrint] CBP page container not found");
		return;
	}

	wrapper.classList.add("cbp-builder-page");
	parent.classList.add("cbp-builder-host");
	parent.innerHTML = "";
	page.clear_actions();
	page.clear_icons();
	page.clear_custom_actions();

	if (route.length > 1) {
		const profileName = route[1];
		page.set_title(__("Branding Profile: {0}", [profileName]));
		parent.innerHTML = '<div id="cbp-builder-root"></div>';

		load_crispy_print_bundle(() => {
			const mounted = window.mountCbpBuilder("#cbp-builder-root", { profileName });
			if (!mounted) return;

			const component = mounted.component;
			page.set_primary_action(__("Save"), () => {
				if (component && typeof component.save === "function") {
					component.save();
				}
			});

			page.add_button(__("Edit DocType Form"), () => {
				frappe.set_route("Form", "Crispy Branding Profile", profileName);
			});

			page.add_menu_item(__("Change Profile"), () => {
				frappe.set_route("cbp-builder");
			});

			if (window.Vue && window.Vue.watch && component?.dirty !== undefined) {
				window.Vue.watch(
					() => Boolean(component.dirty?.value ?? component.dirty),
					(dirty) => {
						page.set_indicator(
							dirty ? __("Not Saved") : __("Saved"),
							dirty ? "orange" : "green"
						);
					},
					{ immediate: true }
				);
			}
		});
		return;
	}

	show_profile_dialog();
}

function load_crispy_print_bundle(callback) {
	if (window.mountCbpBuilder) {
		callback();
		return;
	}
	frappe.require("crispy_print.bundle.js", () => {
		if (!window.mountCbpBuilder) {
			console.error("[CrispyPrint] mountCbpBuilder not found. Bundle may not be loaded.");
			return;
		}
		callback();
	});
}

function show_profile_dialog() {
	const dialog = new frappe.ui.Dialog({
		title: __("Create or Edit Branding Profile"),
		fields: [
			{
				label: __("Action"),
				fieldname: "action",
				fieldtype: "Select",
				options: [
					{ label: __("Create New"), value: "Create" },
					{ label: __("Edit Existing"), value: "Edit" },
				],
				default: "Create",
			},
			{
				label: __("Company"),
				fieldname: "company",
				fieldtype: "Link",
				options: "Company",
				reqd: 1,
			},
			{
				label: __("New Profile Name"),
				fieldname: "profile_name",
				fieldtype: "Data",
				depends_on: (doc) => doc.action === "Create",
				mandatory_depends_on: (doc) => doc.action === "Create",
			},
			{
				label: __("Branding Profile"),
				fieldname: "branding_profile",
				fieldtype: "Link",
				options: "Crispy Branding Profile",
				only_select: 1,
				depends_on: (doc) => doc.action === "Edit",
				mandatory_depends_on: (doc) => doc.action === "Edit",
				get_query() {
					return {
						filters: {
							company: dialog.get_value("company"),
						},
					};
				},
			},
		],
		primary_action_label: __("Open"),
		primary_action(values) {
			if (values.action === "Edit") {
				frappe.set_route("cbp-builder", values.branding_profile);
				dialog.hide();
				return;
			}

			const primary = dialog.get_primary_btn();
			primary && primary.prop && primary.prop("disabled", true);
			frappe.db
				.insert({
					doctype: "Crispy Branding Profile",
					profile_name: values.profile_name,
					company: values.company,
				})
				.then((doc) => {
					frappe.set_route("cbp-builder", doc.name);
					dialog.hide();
				})
				.finally(() => {
					primary && primary.prop && primary.prop("disabled", false);
				});
		},
	});

	dialog.show();
	dialog.set_value("action", "Create");
}
