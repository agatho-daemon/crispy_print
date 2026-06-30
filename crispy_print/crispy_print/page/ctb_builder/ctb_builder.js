frappe.pages["ctb-builder"].on_page_load = function (wrapper) {
	frappe.ui.make_app_page({
		parent: wrapper,
		title: __("Crispy Typst Block Builder"),
		single_column: true,
	});

	if (frappe.boot.developer_mode) {
		frappe.hot_update = frappe.hot_update || [];
		frappe.hot_update.push(() => load_ctb_builder(wrapper));
	}
};

frappe.pages["ctb-builder"].on_page_show = function (wrapper) {
	load_ctb_builder(wrapper);
};

function load_ctb_builder(wrapper) {
	const route = frappe.get_route();
	const parent = wrapper.querySelector(".layout-main-section");
	const page = wrapper.page;

	if (!parent) {
		console.error("[CrispyPrint] CTB page container not found");
		return;
	}

	wrapper.classList.add("ctb-builder-page");
	parent.classList.add("ctb-builder-host");
	parent.innerHTML = "";
	page.clear_actions();
	page.clear_icons();
	page.clear_custom_actions();

	if (route.length > 1) {
		const blockName = route[1];
		page.set_title(__("Editing: {0}", [blockName]));
		parent.innerHTML = '<div id="ctb-builder-root"></div>';

		load_crispy_print_bundle(() => {
			const mounted = window.mountCtbBuilder("#ctb-builder-root", { blockName });
			if (!mounted) {
				parent.innerHTML =
					'<div class="alert alert-danger">Unable to mount Crispy Typst Block Builder.</div>';
				return;
			}

			const component = mounted.component;
			page.set_primary_action(__("Save"), () => {
				if (component && typeof component.save === "function") {
					component.save();
				}
			});

			page.add_button(__("Edit DocType Form"), () => {
				frappe.set_route("Form", "Crispy Typst Block", blockName);
			});

			page.add_menu_item(__("Change Block"), () => {
				frappe.set_route("ctb-builder");
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

	show_block_dialog();
}

function load_crispy_print_bundle(callback) {
	if (window.mountCtbBuilder) {
		callback();
		return;
	}
	frappe.require("ctb_builder.bundle.js", () => {
		if (!window.mountCtbBuilder) {
			console.error("[CrispyPrint] mountCtbBuilder not found. Bundle may not be loaded.");
			return;
		}
		callback();
	});
}

function show_block_dialog() {
	const dialog = new frappe.ui.Dialog({
		title: __("Open Crispy Typst Block"),
		fields: [
			{
				label: __("Crispy Typst Block"),
				fieldname: "block_name",
				fieldtype: "Link",
				options: "Crispy Typst Block",
				reqd: 1,
			},
		],
		primary_action_label: __("Open Builder"),
		primary_action(values) {
			dialog.hide();
			frappe.set_route("ctb-builder", values.block_name);
		},
	});
	dialog.show();
}
