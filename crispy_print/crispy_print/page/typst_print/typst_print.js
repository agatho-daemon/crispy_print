frappe.pages["typst-print"].on_page_load = function (wrapper) {
    var page = frappe.ui.make_app_page({
        parent: wrapper,
        title: "typst-print",
        single_column: true,
    })
}
