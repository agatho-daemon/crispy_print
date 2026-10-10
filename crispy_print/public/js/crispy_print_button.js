(() => {
	const getLogger = (scope = {}) => {
		const base = window?.CrispyPrintLogger;
		if (base && typeof base.child === "function") {
			return base.child(scope);
		}
		const noop = {
			debug: () => {},
			info: () => {},
			warn: () => {},
			error: () => {},
			child: () => noop,
			setLevel: () => {},
		};
		return noop;
	};
	const logger = getLogger({ module: "CrispyPrintButton" });
	const ns = (window.typstPrint = window.typstPrint || {});

	// Load doctypes with default Crispy Formats
	frappe.call({
		method: "crispy_print.api.v1.get_default_doctypes",
		freeze: false,
		callback: (r) => {
			const doctypes = r.message || [];
			if (doctypes.length > 0) {
				ns.registerButtonsFor(doctypes);
			}
		},
		error: () => {
			logger.error("Failed to load default doctypes");
		},
	});

	const registered = new Set();

	ns.registerButtonsFor = function (doctypes = []) {
		doctypes.forEach((dt) => {
			if (!dt || registered.has(dt)) return;
			registered.add(dt);

			frappe.ui.form.on(dt, {
				refresh(frm) {
					// Only show for saved documents
					if (frm.is_new()) return;

					const button = frm.add_custom_button(__("Crispy Print"), () => {
						frappe.set_route("crispy-print-preview", frm.doctype, frm.docname);
					});
					crispy_print.decorate_print_button(button);
				},
			});
		});
	};
})();
