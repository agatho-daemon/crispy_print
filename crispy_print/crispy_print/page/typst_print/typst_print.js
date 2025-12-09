frappe.pages["typst-print"].on_page_load = function (wrapper) {
    frappe.ui.make_app_page({ parent: wrapper });
    frappe.pages["typst-print"].print_view = new frappe.ui.CrispyPrintView(wrapper);
};

frappe.pages["typst-print"].on_page_show = function () {
    const route = frappe.get_route();
    const doctype = route[1];
    const docname = route.slice(2, 3).join(""); // keep simple join for performance
    const format = route[3];

    const print_view = frappe.pages["typst-print"].print_view;
    if (!print_view || !doctype || !docname) return;

    // fetch doc + meta before rendering; cache prevents redundant network calls
    frappe.model.with_doc(doctype, docname, () => {
        frappe.model.with_doctype(doctype, () => {
            const frm = {
                doctype,
                docname,
                doc: frappe.get_doc(doctype, docname),
                meta: frappe.get_meta(doctype),
            };
            print_view.show(frm, format);
        });
    });
};

frappe.ui.CrispyPrintView = class {
    constructor(wrapper) {
        this.wrapper = $(wrapper);
        this.page = wrapper.page;
        this.current = {};
        this.make();
    }

    make() {
        this.print_wrapper = this.page.main.empty().html(
            `<div class="print-preview-wrapper" style="padding: 0; background: transparent; border-radius: 6px; overflow: hidden;">
                <div id="crispy-preview-root"></div>
                <div class="text-muted small" id="crispy-preview-status"></div>
            </div>`
        );

        this.status_el = this.print_wrapper.find("#crispy-preview-status");
        this.setup_toolbar();
        
        // Hide Frappe's sidebar completely (settings are in CrispyPP.vue)
        this.page.sidebar.hide();
        this.wrapper.find(".page-head").removeClass("drop-shadow");
    }

    show(frm, format) {
        const same_doc = this.current.doctype === frm.doctype && this.current.docname === frm.docname;
        const same_format = this.current.format === format;

        this.current = { doctype: frm.doctype, docname: frm.docname, format, frm };

        this.page.set_title(__(frm.docname));
        this.setup_menu(format);

        if (!same_doc || !same_format) {
            this.render_preview(frm, format);
        }
    }

    render_preview(frm, format) {
        this.status_el.text(__("Loading preview..."));
        
        // Mount Vue component if not already mounted
        if (!this.vue_instance) {
            this.vue_instance = window.mountCrispyPreview("#crispy-preview-root", {
                doctype: frm.doctype,
                docname: frm.docname,
                format,
            });
            
            // Setup worker after Vue mounts
            this.setup_worker(frm, format);
        }
        
        this.status_el.text(__("")); // clear after mount
    }

    setup_worker(frm, format) {
        // Wait for Vue to load format data and mount
        setTimeout(() => {
            const container = document.getElementById("typst-svg-container");
            if (!container) {
                console.error("[CrispyPrint] Preview container not found");
                return;
            }

            // Initialize worker with format and document data
            if (typeof window.setupWorker === "function") {
                // Create a modified container that provides document data
                const previewContainer = container;
                
                // Pre-populate with document data (no sample selection needed)
                this.current_doc_data = frm.doc;
                
                this.teardown_worker = window.setupWorker(format, previewContainer, {
                    getLayout: () => this.vue_instance?.component?.getLayout() || null,
                    getLetterhead: () => this.vue_instance?.component?.getLetterhead() || "",
                    getDoctype: () => frm.doctype,
                    getPageSettings: () => this.vue_instance?.component?.getPageSettings() || this.get_default_page_settings(),
                    hookDataChanges: (callback) => {
                        // Listen for settings/layout changes from Vue
                        const handler = (event) => {
                            console.log("[CrispyPrint] Refresh event:", event.detail);
                            callback();
                        };
                        window.addEventListener("crispy-refresh-preview", handler);
                        return () => window.removeEventListener("crispy-refresh-preview", handler);
                    },
                    hookDoctypeChanges: (callback) => {
                        // Doctype doesn't change in preview, but needed by setupWorker
                        callback(frm.doctype);
                        return () => {};
                    }
                });
                
                // Simulate document selection by directly setting the data
                setTimeout(() => {
                    this.trigger_compile_with_document(frm);
                }, 500);
                
                console.log("[CrispyPrint] Worker setup complete for format:", format);
            } else {
                console.error("[CrispyPrint] setupWorker not available");
            }
        }, 300);
    }

    trigger_compile_with_document(frm) {
        // Directly trigger compilation with the document data
        const event = new CustomEvent("crispy-compile-document", {
            detail: {
                doctype: frm.doctype,
                docname: frm.docname,
                doc: frm.doc
            }
        });
        window.dispatchEvent(event);
        console.log("[CrispyPrint] Triggered compile with document:", frm.docname);
    }

    get_default_page_settings() {
        return {
            pageSize: "A4",
            orientation: "portrait",
            margins: { top: 25, bottom: 20, left: 20, right: 20 },
            language: "en",
            letterhead: ""
        };
    }

    setup_toolbar() {
        this.page.set_primary_action(__("Print"), () => this.print_document(), "printer");
        this.page.add_button(__("PDF"), () => this.render_pdf(), { icon: "small-file" });
        this.page.add_button(__("Refresh"), () => this.refresh_preview(), { icon: "refresh" });
        this.page.add_action_icon("es-line-filetype", () => this.go_to_form_view(), "", __("Form"));
    }

    go_to_form_view() {
        if (this.current.doctype && this.current.docname) {
            frappe.set_route("Form", this.current.doctype, this.current.docname);
        }
    }

    setup_menu(format) {
        this.page.clear_menu();
        this.page.add_menu_item(__("Print Settings"), () => frappe.set_route("Form", "Print Settings"));
        if (format) {
            this.page.add_menu_item(__("Customize"), () => frappe.set_route("crispy-print-builder", format));
        }
    }

    print_document() {
        frappe.msgprint({
            title: __("Print"),
            message: __("Printing {0}...", [this.current.docname || ""]),
            primary_action: { label: __("Close"), action: () => {} },
        });
    }

    render_pdf() {
        frappe.show_alert({ message: __("Opening PDF..."), indicator: "blue" });
    }

    refresh_preview() {
        // Trigger refresh via Vue component
        if (this.vue_instance?.component?.triggerRefresh) {
            this.vue_instance.component.triggerRefresh();
        } else {
            // Fallback: remount
            this.vue_instance = null;
            this.render_preview(this.current.frm, this.current.format);
        }
    }
};
