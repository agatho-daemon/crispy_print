// Typst Preview worker wiring for Crispy Print (Vue + Vite)

import { translateJSONToTypst } from "./JSONToTypst"
import { createTypstWorker } from "./createTypstWorker"
import { extractUsedFields, filterDocumentFields } from "../utils/layoutFieldExtractor"
import type { CrispyLayout } from "../utils/layout"
import type { LayoutField } from "../utils/layout"

export interface TypstAdapter {
	getLayout: () => CrispyLayout | null | undefined
	getDocHeader?: () => string | null | undefined
	getLetterhead?: () => any
	getDoctype?: () => string | null | undefined
	getDocname?: () => string | null | undefined
	getPageSettings?: () => any
	hookDataChanges?: (callback: () => void) => () => void
	hookDoctypeChanges?: (callback: (doctype: string | null | undefined) => void) => () => void
}

export function setupWorker(printFormatName: string, previewPane: HTMLElement, adapter: TypstAdapter) {
	const { worker, cleanup } = createTypstWorker()

	worker.addEventListener("error", (err) => {
		console.error("[Typst Preview] Worker error", err)
	})
	worker.addEventListener("messageerror", (err) => {
		console.error("[Typst Preview] Worker messageerror", err)
	})

	const statusEl = previewPane.querySelector<HTMLElement>("#typst-status")
	const svgContainer = previewPane.querySelector<HTMLElement>("#typst-svg-container")
	const downloadBtn = previewPane.querySelector<HTMLButtonElement>("#typst-download")
	const viewPdfBtn = previewPane.querySelector<HTMLButtonElement>("#typst-view-pdf")
	const refreshBtn = previewPane.querySelector<HTMLButtonElement>("#typst-refresh")
	const viewCodeBtn = previewPane.querySelector<HTMLButtonElement>("#typst-view-code")
	const sampleDocInput = previewPane.querySelector<HTMLInputElement>("#typst-sample-doc-input")

	let awesomplete: any = null
	let sampleDocData: Record<string, any> | null = null
	let currentDoctype: string | null = null
	let currentDocname: string | null = null
	let sampleDocSelected = false
	const docCache = new Map<string, Record<string, any>>()

	function cacheKey(doctype: string, docname: string) {
		return `${doctype}::${docname}`
	}

	function fetchDoc(doctype: string, docname: string, opts: { force?: boolean } = {}): Promise<Record<string, any> | null> {
		const key = cacheKey(doctype, docname)
		const cached = docCache.get(key)
		if (!opts.force && cached) return Promise.resolve(cached)

		return new Promise((resolve) => {
			if (typeof frappe === "undefined" || typeof frappe.call !== "function") {
				resolve(null)
				return
			}

			frappe.call({
				method: "frappe.client.get",
				args: { doctype, name: docname },
				callback: (r: any) => {
					if (r?.message && typeof r.message === "object") {
						docCache.set(key, r.message)
						resolve(r.message)
					} else {
						resolve(null)
					}
				},
				error: () => resolve(null),
			})
		})
	}

	function dispatchStatus(status: "fetching" | "compiling" | "ready" | "error", message?: string) {
		window.dispatchEvent(
			new CustomEvent("crispy-preview:status", {
				detail: { status, message },
			})
		)
	}

	function setCurrentDoc(doctype: string, docname: string, opts: { force?: boolean } = {}) {
		currentDoctype = doctype
		currentDocname = docname
		sampleDocSelected = false
		sampleDocData = null

		clearPreview()
		lastLayoutSerialized = ""
		lastTypstCode = ""

		if (statusEl) {
			statusEl.textContent = "fetching document…"
			statusEl.style.color = "#3498db"
		}
		dispatchStatus("fetching", docname)

		fetchDoc(doctype, docname, { force: Boolean(opts.force) }).then((doc) => {
			if (!doc) {
				console.warn("[Typst Preview] Failed to fetch document", doctype, docname)
				if (statusEl) {
					statusEl.textContent = "document not found"
					statusEl.style.color = "#e74c3c"
				}
				dispatchStatus("error", "document not found")
				return
			}

			sampleDocData = doc
			sampleDocSelected = true
			compile()

			frappe?.show_alert?.({
				message: __("Preview loaded: {0}", [docname]),
				indicator: "green",
			})
		})
	}

	const clearPreview = () => {
		if (svgContainer) {
			svgContainer.classList.remove("has-pages")
		}
	}
	const markHasPages = () => {
		if (svgContainer) {
			svgContainer.classList.add("has-pages")
		}
	}
	const renderTypstPages = (_rootEl: HTMLElement, svgPages: string[]) => {
		const container = document.getElementById("typst-svg-container")
		const placeholder = document.getElementById("typst-preview-placeholder")

		if (!container) return

		if (placeholder) {
			placeholder.remove()
		}

		container.innerHTML = ""

		svgPages.forEach((svg) => {
			const page = document.createElement("div")
			page.className = "typst-page"
			page.style.marginBottom = "1.5rem"
			page.style.boxShadow = "0 4px 12px rgba(148, 163, 184, 0.25), 0 2px 6px rgba(148, 163, 184, 0.2)"

			page.innerHTML = svg
			const svgEl = page.querySelector("svg");
			if (svgEl) {
				svgEl.style.width = "100%";
				svgEl.style.height = "auto";
				svgEl.removeAttribute("width");   // let viewBox control sizing
				svgEl.removeAttribute("height");
			}

			container.appendChild(page)
		})
	}

	// Unified preview events (single source of truth)
	const handleSetDoc = (event: any) => {
		const { doctype, docname } = event?.detail || {}
		if (!doctype || !docname) {
			console.warn("[Typst Preview] Invalid set-doc event", event?.detail)
			return
		}
		setCurrentDoc(doctype, docname, { force: true })
	}
	window.addEventListener("crispy-preview:set-doc", handleSetDoc)

	const handleRefresh = () => {
		if (!currentDoctype || !currentDocname) {
			// typst-print mode: a specific document is provided by the page
			const doctype = adapter.getDoctype?.()
			const docname = adapter.getDocname?.()
			if (doctype && docname) {
				setCurrentDoc(doctype, docname, { force: true })
				return
			}
			frappe?.show_alert?.({ message: __("Select a document first"), indicator: "orange" })
			return
		}
		// Refetch + recompile to ensure latest values (single source of truth).
		setCurrentDoc(currentDoctype, currentDocname, { force: true })
	}
	window.addEventListener("crispy-preview:refresh", handleRefresh)

	const handleSourceRequest = () => {
		window.dispatchEvent(
			new CustomEvent("crispy-preview:source", {
				detail: { source: lastTypstCode || null },
			})
		)
	}
	window.addEventListener("crispy-preview:request-source", handleSourceRequest)

	// PDF generation request (used by typst-print toolbar and any other UI)
	const handlePdfRequest = (event: any) => {
		const action = (event?.detail?.action || "view") as "view" | "download"

		if (currentPdfBlob) {
			if (action === "download") {
				triggerPdfDownload()
				return
			}

			const url = URL.createObjectURL(currentPdfBlob)
			window.open(url, "_blank")
			setTimeout(() => URL.revokeObjectURL(url), 1000)
			return
		}

		if (!lastTypstCode) {
			frappe?.show_alert({ message: __("Typst code not ready yet"), indicator: "orange" })
			return
		}

		if (statusEl) {
			statusEl.textContent = "generating pdf…"
			statusEl.style.color = "#3498db"
		}

		pendingPdfDownload = action === "download"

		let letterheadImage: string | null = null
		if (adapter && typeof adapter.getLetterhead === "function") {
			const letterhead = adapter.getLetterhead()
			if (letterhead && (letterhead as any).image) {
				letterheadImage = (letterhead as any).image
			}
		}

		const requestId = pendingPdfDownload ? DOWNLOAD_REQUEST_ID : "view-pdf"
		worker.postMessage({
			typstSrc: lastTypstCode,
			csrfToken: frappe?.csrf_token,
			outputFormat: "pdf",
			requestId,
			letterheadImage,
		})
	}
	window.addEventListener("crispy-preview:request-pdf", handlePdfRequest)

	function setupSampleDocAutocomplete(doctype: string) {
		if (!doctype) {
			console.warn("[Typst Preview] Cannot setup autocomplete - missing doctype")
			return
		}

		if (!sampleDocInput) {
			// In PP, the search input isn't rendered; silently skip autocomplete
			return
		}

		if (typeof Awesomplete === "undefined") {
			// Builder-only enhancement; skip quietly when not available
			return
		}

		currentDoctype = doctype
		currentDocname = null

		sampleDocInput.placeholder = `Search ${doctype}...`
		sampleDocInput.setAttribute("data-doctype", doctype)
		sampleDocInput.value = ""
		sampleDocData = null
		sampleDocSelected = false

		awesomplete = new Awesomplete(sampleDocInput, {
			minChars: 0,
			maxItems: 20,
			autoFirst: true,
			filter: () => true,
		})

		function searchDocs(txt: string) {
			frappe.call({
				method: "frappe.desk.search.search_link",
				args: {
					doctype,
					txt: txt || "",
					page_length: 20,
				},
				callback: (r: any) => {
					if (r.message && r.message.length) {
						awesomplete.list = r.message.map((d: any) => ({
							label: d.value + (d.description ? " - " + __(d.description) : ""),
							value: d.value,
						}))
					}
				},
			})
		}

		sampleDocInput.addEventListener("focus", () => {
			searchDocs(sampleDocInput.value)
		})

		sampleDocInput.addEventListener(
			"input",
			frappe.utils.debounce(() => {
				sampleDocSelected = false
				sampleDocData = null
				searchDocs(sampleDocInput.value)
			}, 300)
		)

		sampleDocInput.addEventListener("awesomplete-selectcomplete", () => {
			const selectedDoc = sampleDocInput.value
			sampleDocSelected = false
			currentDocname = selectedDoc

			if (!selectedDoc || !currentDoctype) {
				console.warn("[Typst Preview] No document or doctype selected")
				return
			}

			statusEl && (statusEl.textContent = "fetching document...")
			if (statusEl) statusEl.style.color = "#3498db"

			setCurrentDoc(currentDoctype, selectedDoc, { force: true })
		})

	}

	const PREVIEW_REQUEST_ID = "preview"
	const DOWNLOAD_REQUEST_ID = "download"
	const previewOutputFormat = "svg"
	svgContainer?.classList.remove("preview-hidden")

	let compilationTimeout: number | undefined
	let debounceTimer: number | undefined = undefined
	let lastTypstCode = ""
	let lastLayoutSerialized = ""
	let lastPageSettingsSerialized = ""
	let currentPdfBlob: Blob | null = null
	let pendingPdfDownload = false
	let compileTriggerTimeout: number | undefined
	let missingLayoutRetries = 0
	let unsubscribeAdapter: (() => void) | null = null
	let unsubscribeDoctype: (() => void) | null = null
	let compilationDisabled = false

	function scheduleCompile(reason = "hook", delay = 200) {
		if (compilationDisabled) {
			return
		}

		// Don't schedule compile if no sample document is selected
		if (!sampleDocSelected) {
			return
		}

		if (compileTriggerTimeout) {
			clearTimeout(compileTriggerTimeout)
		}
		compileTriggerTimeout = window.setTimeout(() => {
			compile()
		}, delay)
	}

	function triggerPdfDownload() {
		if (!currentPdfBlob) {
			return
		}
		const url = URL.createObjectURL(currentPdfBlob)
		const link = document.createElement("a")
		link.href = url
		link.download = `${printFormatName.replace(/\s+/g, "_")}_preview.pdf`
		link.click()
		URL.revokeObjectURL(url)
	}

	function initializeAdapter() {
		if (!adapter) {
			console.warn("[Typst Preview] No adapter provided")
			return
		}

		const doctype = adapter.getDoctype?.()
		const docname = adapter.getDocname?.()
		if (doctype && docname) {
			// typst-print mode: render a specific document without requiring sample selection
			setCurrentDoc(doctype, docname, { force: true })
		} else if (doctype) {
			setupSampleDocAutocomplete(doctype)
		} else {
			console.warn("[Typst Preview] No doctype found, skipping sample doc setup")
		}

		if (adapter.hookDoctypeChanges) {
			unsubscribeDoctype = adapter.hookDoctypeChanges((nextDoctype) => {
				if (nextDoctype && nextDoctype !== currentDoctype) {
					setupSampleDocAutocomplete(nextDoctype)
				}
			})
		}

		if (adapter.hookDataChanges) {
			unsubscribeAdapter = adapter.hookDataChanges(() => {
				scheduleCompile("adapter-change", 200)
			})
		}

		// Don't compile on initial adapter ready - wait for user to select a document
	}

	function getLayout() {
		if (!adapter) {
			console.warn("[Typst Preview] Adapter not available")
			return null
		}

		if (!adapter.getLayout) {
			console.error("[Typst Preview] Adapter does not have getLayout function")
			return null
		}

		return adapter.getLayout()
	}

	function serializeLayout(layout: CrispyLayout | null | undefined) {
		if (!layout) return ""
		try {
			return JSON.stringify(layout)
		} catch (e) {
			console.error("[Typst Preview] Failed to serialize layout:", e)
			return ""
		}
	}

	function compile() {
		if (compilationTimeout) {
			clearTimeout(compilationTimeout)
		}
		// Use shorter debounce and defer heavy work to next frame
		compilationTimeout = window.setTimeout(() => {
			// Split work across frames to avoid blocking
			requestAnimationFrame(() => {
				performCompilation()
			})
		}, 150)
	}

	function performCompilation() {
		clearPreview()

		// Allow compile if we already have document data, even if sampleDocSelected wasn't toggled
		if (!sampleDocData) {
			console.warn("[Typst Preview] No document data; skipping compile")
			if (statusEl) {
				statusEl.textContent = "select a document"
				statusEl.style.color = "#e67e22"
			}
			dispatchStatus("error", "no document")
			return
		}

		const layout = getLayout()

		if (!layout) {
			console.error("[Typst Preview] No layout found from adapter")
			if (statusEl) {
				statusEl.textContent = "waiting for layout..."
				statusEl.style.color = "#e67e22"
			}
			if (missingLayoutRetries < 5) {
				missingLayoutRetries += 1
				console.warn(`[Typst Preview] Retrying compile due to missing layout (attempt ${missingLayoutRetries}/5)`)
				scheduleCompile("retry-missing-layout", 500 * missingLayoutRetries)
			} else {
				console.error("[Typst Preview] Max retries (5) reached. Disabling compilation.")
				compilationDisabled = true
				if (statusEl) {
					statusEl.textContent = "no layout data"
					statusEl.style.color = "#e74c3c"
				}
			}
			return
		}
		missingLayoutRetries = 0

		const layoutSerialized = serializeLayout(layout)

		// Also check page settings for changes
		let pageSettingsSerialized = ""
		if (adapter && adapter.getPageSettings) {
			try {
				const pageSettings = adapter.getPageSettings()
				pageSettingsSerialized = pageSettings ? JSON.stringify(pageSettings) : ""
			} catch (e) {
				console.warn("[Typst Preview] Failed to serialize page settings:", e)
			}
		}

		// Always compile on trigger; skip unchanged guard to honor debounced triggers
		lastLayoutSerialized = layoutSerialized
		lastPageSettingsSerialized = pageSettingsSerialized

		// Extract fields actually used in the layout
		const usedFields = extractUsedFields(layout)

		// Filter document to only include used fields
		const filteredDoc = filterDocumentFields(sampleDocData, usedFields)

		// Apply Frappe-style formatting (Currency/Date/Percent/etc.) so Typst output matches Frappe preview.
		// We format *after* filtering to keep the payload small.
		try {
			applyFrappeFormatting(layout as any, currentDoctype, sampleDocData, filteredDoc)
		} catch (e) {
			console.warn("[Typst Preview] Failed to apply Frappe formatting:", e)
		}

		let typst: string
		try {
			let letterheadData: any = null
			if (adapter && typeof adapter.getLetterhead === "function") {
				letterheadData = adapter.getLetterhead()
			}

			// Get page settings to pass to translator
			let pageSettings: any = {}
			if (adapter && adapter.getPageSettings) {
				pageSettings = adapter.getPageSettings() || {}
			}

			const docHeader =
				adapter && typeof adapter.getDocHeader === "function" ? adapter.getDocHeader() || "" : ""

			// Use filtered document instead of full sampleDocData
			typst = translateJSONToTypst(layout as any, letterheadData, printFormatName, filteredDoc, {
				...pageSettings,
				docHeader,
			})

		} catch (e: any) {
			console.error("[Typst Preview] Translation error:", e)
			if (statusEl) {
				statusEl.textContent = "translation error"
				statusEl.style.color = "#e74c3c"
			}
			frappe?.show_alert({
				message: __("Translation failed: {0}", [e.message || e]),
				indicator: "red",
			})
			return
		}

		if (typst === lastTypstCode) {
			if (statusEl) {
				statusEl.textContent = "code unchanged"
				statusEl.style.color = "#95a5a6"
			}
			return
		}
		lastTypstCode = typst

		if (statusEl) {
			statusEl.textContent = "compiling…"
			statusEl.style.color = "#f39c12"
		}
		dispatchStatus("compiling")
		if (downloadBtn) downloadBtn.disabled = true
		currentPdfBlob = null

		let letterheadImage: string | null = null
		if (adapter && typeof adapter.getLetterhead === "function") {
			const letterhead = adapter.getLetterhead()
			if (letterhead && (letterhead as any).image) {
				letterheadImage = (letterhead as any).image
			}
		}

		worker.postMessage({
			typstSrc: typst,
			csrfToken: frappe?.csrf_token,
			outputFormat: previewOutputFormat,
			requestId: PREVIEW_REQUEST_ID,
			letterheadImage,
		})
	}

	worker.addEventListener("message", (e) => {
		const { type, ok, format, svgPages, pdfBytes, error, requestId, pageCount } = e.data || {}
		const isDownload = requestId === DOWNLOAD_REQUEST_ID
		const isViewPdf = requestId === "view-pdf"

		if (type === "init") {
			return
		}

		if (type === "compile" || !type) {
			if (!ok) {
				console.error("[Typst Preview] Compilation failed:", error)
				if (statusEl) {
					statusEl.textContent = isDownload || isViewPdf ? "pdf error" : "error"
					statusEl.style.color = "#e74c3c"
				}
				frappe?.show_alert({
					message: __("Typst compilation failed: {0}", [error?.message || error]),
					indicator: "red",
				})
				if (isDownload && downloadBtn) {
					downloadBtn.disabled = false
					pendingPdfDownload = false
				}
				if (isViewPdf) {
					if (viewPdfBtn) viewPdfBtn.disabled = false
					if (downloadBtn) downloadBtn.disabled = false
				}
				return
			}

			if (format === "svg") {
				if (!Array.isArray(svgPages) || svgPages.length === 0) {
					if (statusEl) {
						statusEl.textContent = "svg missing"
						statusEl.style.color = "#e67e22"
					}
					frappe?.show_alert({
						message: __("Typst compilation returned no SVG pages"),
						indicator: "orange",
					})
					if (downloadBtn) downloadBtn.disabled = false
					return
				}

				if (!isDownload) {
					svgContainer?.classList.remove("preview-hidden")
					if (previewPane) {
						renderTypstPages(previewPane, svgPages as string[])
						markHasPages()
					}
					if (statusEl) {
						statusEl.textContent = "compiled ✓"
						statusEl.style.color = "#27ae60"
					}
					dispatchStatus("ready")
				} else {
					console.warn("[Typst Preview] SVG response received for download request")
					pendingPdfDownload = false
				}

				if (downloadBtn) downloadBtn.disabled = false
				if (viewPdfBtn) viewPdfBtn.disabled = false
				return
			}

			const pdfArray = new Uint8Array(pdfBytes || [])

			if (!pdfArray.length) {
				if (statusEl) {
					statusEl.textContent = "empty pdf"
					statusEl.style.color = "#e67e22"
				}
				frappe?.show_alert({
					message: __("Typst compilation returned an empty PDF"),
					indicator: "orange",
				})
				pendingPdfDownload = false
				if (downloadBtn) downloadBtn.disabled = false
				return
			}

			currentPdfBlob = new Blob([pdfArray], { type: "application/pdf" })
			const shouldAutoDownload = isDownload && pendingPdfDownload
			pendingPdfDownload = false

			if (isViewPdf) {
				const url = URL.createObjectURL(currentPdfBlob)
				window.open(url, "_blank")
				setTimeout(() => URL.revokeObjectURL(url), 1000)

				if (statusEl) {
					statusEl.textContent = "pdf opened ✓"
					statusEl.style.color = "#27ae60"
				}
				if (viewPdfBtn) viewPdfBtn.disabled = false
				if (downloadBtn) downloadBtn.disabled = false
				return
			}

			if (isDownload) {
				if (statusEl) {
					statusEl.textContent = "pdf ready ✓"
					statusEl.style.color = "#27ae60"
				}
				if (downloadBtn) downloadBtn.disabled = false
				if (shouldAutoDownload) {
					triggerPdfDownload()
				}
				return
			} else {
				console.warn("[Typst Preview] PDF response received for preview request")
				if (statusEl) {
					statusEl.textContent = "unexpected pdf"
					statusEl.style.color = "#e67e22"
				}
			}
			if (downloadBtn) downloadBtn.disabled = false
			if (viewPdfBtn) viewPdfBtn.disabled = false
			return
		}
	})

	viewPdfBtn &&
		(viewPdfBtn.onclick = () => {
			if (currentPdfBlob) {
				const url = URL.createObjectURL(currentPdfBlob)
				window.open(url, "_blank")
				setTimeout(() => URL.revokeObjectURL(url), 1000)
				return
			}

			if (!lastTypstCode) {
				frappe?.show_alert({ message: __("Typst code not ready yet"), indicator: "orange" })
				return
			}

			if (statusEl) {
				statusEl.textContent = "generating pdf…"
				statusEl.style.color = "#3498db"
			}
			viewPdfBtn.disabled = true
			if (downloadBtn) downloadBtn.disabled = true

			let letterheadImage: string | null = null
			if (adapter && typeof adapter.getLetterhead === "function") {
				const letterhead = adapter.getLetterhead()
				if (letterhead && (letterhead as any).image) {
					letterheadImage = (letterhead as any).image
				}
			}

			const VIEW_PDF_REQUEST_ID = "view-pdf"
			worker.postMessage({
				typstSrc: lastTypstCode,
				csrfToken: frappe?.csrf_token,
				outputFormat: "pdf",
				requestId: VIEW_PDF_REQUEST_ID,
				letterheadImage,
			})
		})

	downloadBtn &&
		(downloadBtn.onclick = () => {
			if (currentPdfBlob) {
				pendingPdfDownload = false
				triggerPdfDownload()
				return
			}

			if (!lastTypstCode) {
				frappe?.show_alert({ message: __("Typst code not ready yet"), indicator: "orange" })
				return
			}

			if (statusEl) {
				statusEl.textContent = "generating pdf…"
				statusEl.style.color = "#3498db"
			}
			downloadBtn.disabled = true
			pendingPdfDownload = true

			let letterheadImage: string | null = null
			if (adapter && typeof adapter.getLetterhead === "function") {
				const letterhead = adapter.getLetterhead()
				if (letterhead && (letterhead as any).image) {
					letterheadImage = (letterhead as any).image
				}
			}

			worker.postMessage({
				typstSrc: lastTypstCode,
				csrfToken: frappe?.csrf_token,
				outputFormat: "pdf",
				requestId: DOWNLOAD_REQUEST_ID,
				letterheadImage,
			})
		})

	refreshBtn &&
		(refreshBtn.onclick = () => {
			if (statusEl) {
				statusEl.textContent = "refreshing..."
				statusEl.style.color = "#3498db"
			}
			lastLayoutSerialized = ""
			lastTypstCode = "" // Force recompilation by clearing cached code
			missingLayoutRetries = 0
			compilationDisabled = false
			scheduleCompile("manual-refresh", 0)
		})

	viewCodeBtn &&
		(viewCodeBtn.onclick = () => {
			const d = new frappe.ui.Dialog({
				title: "Typst Code",
				fields: [
					{
						fieldtype: "Code",
						fieldname: "typst_code",
						label: "Typst Source",
						options: "Rust",
						default: lastTypstCode,
					},
				],
				primary_action_label: "Save to Print Format",
				primary_action: (values: any) => {
					const typstCode = values.typst_code || d.get_value("typst_code")

					frappe.call({
						method: "frappe.client.set_value",
						args: {
							doctype: "Print Format",
							name: printFormatName,
							fieldname: "typst_code",
							value: typstCode,
						},
						callback: (r: any) => {
							if (!r.exc) {
								frappe.show_alert({
									message: __("Typst code saved to Print Format"),
									indicator: "green",
								})
								d.hide()
							}
						},
					})
				},
				secondary_action_label: "Copy to Clipboard",
				secondary_action: () => {
					const typstCode = d.get_value("typst_code")
					navigator.clipboard.writeText(typstCode)
					frappe.show_alert({ message: __("Typst code copied to clipboard"), indicator: "green" })
				},
			})
			d.show()
		})

	initializeAdapter()

	return () => {
		if (unsubscribeAdapter) {
			unsubscribeAdapter()
		}
		if (unsubscribeDoctype) {
			unsubscribeDoctype()
		}
		window.removeEventListener("crispy-preview:set-doc", handleSetDoc)
		window.removeEventListener("crispy-preview:refresh", handleRefresh)
		window.removeEventListener("crispy-preview:request-source", handleSourceRequest)
		window.removeEventListener("crispy-preview:request-pdf", handlePdfRequest)
		if (worker) {
			cleanup()
		}
	}
}

function applyFrappeFormatting(
	layout: CrispyLayout | null | undefined,
	doctype: string | null,
	fullDoc: Record<string, any> | null,
	filteredDoc: Record<string, any> | null
) {
	if (!layout || !doctype || !fullDoc || !filteredDoc) return
	if (typeof frappe === "undefined" || typeof frappe.format !== "function" || !frappe.meta) return

	const normalizeFieldtype = (df: any) => String(df?.fieldtype || "").replace(/\s+/g, "")
	const shouldFormatFieldtype = (fieldtype: string) =>
		[
			"Currency",
			"Int",
			"Float",
			"Percent",
			"Date",
			"Datetime",
			"Time",
		].includes(fieldtype)

	const stripHtml = (value: any) => {
		if (typeof value !== "string") return value
		if (typeof frappe !== "undefined" && frappe.utils && typeof frappe.utils.strip_html === "function") {
			return frappe.utils.strip_html(value)
		}
		// Fallback: basic tag stripping (keeps plain text)
		return value
			.replace(/<br\s*\/?>\s*\n/gi, "\n")
			.replace(/<br\s*\/?>/gi, "\n")
			.replace(/<[^>]+>/g, "")
	}

	const formatValue = (value: any, df: any) => {
		// `only_value` avoids HTML wrappers (right-align spans, etc.)
		return stripHtml(frappe.format(value, df, { only_value: 1 }, fullDoc))
	}

	const walkFields = (): LayoutField[] => {
		const out: LayoutField[] = []
		for (const section of layout.sections || []) {
			for (const col of (section as any).columns || []) {
				for (const field of (col as any).fields || []) {
					if (field && field.fieldname) out.push(field as LayoutField)
				}
			}
		}
		return out
	}

	for (const field of walkFields()) {
		if (!field.fieldname) continue

		// Table fields: format each selected column value per row.
		if (field.fieldtype === "Table") {
			const tableFieldname = field.fieldname
			const df = frappe.meta.get_docfield(doctype, tableFieldname)
			const childDoctype = df?.options || field.options
			if (!childDoctype) continue

			const rows = filteredDoc[tableFieldname]
			if (!Array.isArray(rows) || !rows.length) continue

			const columns = field.table_columns || []
			for (const row of rows) {
				if (!row || typeof row !== "object") continue
				for (const col of columns) {
					if (!col?.fieldname) continue
					const childDf = frappe.meta.get_docfield(childDoctype, col.fieldname)
					if (!childDf) continue
					if (!(col.fieldname in row)) continue
					const ft = normalizeFieldtype(childDf)
					if (!shouldFormatFieldtype(ft)) continue
					row[col.fieldname] = formatValue(row[col.fieldname], childDf)
				}
			}
			continue
		}

		// Non-table fields: format based on DocType docfield.
		const df = frappe.meta.get_docfield(doctype, field.fieldname)
		if (!df) continue
		if (!(field.fieldname in filteredDoc)) continue

		// Only run for types where Frappe formatting is meaningful/expected.
		// (Currency handles symbols/precision; Date/Datetime handles locale; Percent handles precision + %.)
		const ft = normalizeFieldtype(df)
		if (!shouldFormatFieldtype(ft)) continue
		filteredDoc[field.fieldname] = formatValue(filteredDoc[field.fieldname], df)
	}
}
