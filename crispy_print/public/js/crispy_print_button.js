;(() => {
	const ns = (window.typstPrint = window.typstPrint || {})

	// Load doctypes with default Crispy Formats
	frappe.call({
		method: "crispy_print.api.get_default_doctypes",
		freeze: false,
		callback: (r) => {
			const doctypes = r.message || []
			if (doctypes.length > 0) {
				ns.registerButtonsFor(doctypes)
			}
		},
		error: () => {
			console.error("[CrispyPrint] Failed to load default doctypes")
		},
	})

	const registered = new Set()

	ns.registerButtonsFor = function (doctypes = []) {
		doctypes.forEach((dt) => {
			if (!dt || registered.has(dt)) return
			registered.add(dt)

			frappe.ui.form.on(dt, {
				refresh(frm) {
					// Only show for saved documents
					if (frm.is_new()) return

					frm.add_custom_button(
						`<img src="/assets/crispy_print/icons/typst.svg"
                             style="width:45px;height:45px;margin-top:2px;"
                             alt="Crispy Print"
                             title="Open Crispy Print Preview"/>`,
						() => {
							frappe.set_route("typst-print", frm.doctype, frm.docname)
						}
					)
				},
			})
		})
	}
})()
