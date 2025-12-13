// Typst Preview worker wiring for Crispy Print (Vue + Vite)

import { translateJSONToTypst } from "./JSONToTypst"
import { createTypstWorker } from "./createTypstWorker"
import { extractUsedFields, filterDocumentFields } from "../utils/layoutFieldExtractor"
import type { CrispyLayout } from "../utils/layout"

declare const Awesomplete: any
declare const frappe: any
declare const __: any

export interface TypstAdapter {
	getLayout: () => CrispyLayout | null | undefined
	getLetterhead?: () => any
	getDoctype?: () => string | null | undefined
	getPageSettings?: () => any
	hookDataChanges?: (callback: () => void) => () => void
	hookDoctypeChanges?: (callback: (doctype: string | null | undefined) => void) => () => void
}

export function setupWorker(printFormatName: string, previewPane: HTMLElement, adapter: TypstAdapter) {
	const { worker, cleanup } = createTypstWorker()
	console.log("[Typst Preview] Worker created from factory")

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
	let sampleDocSelected = false
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

	// Listen for direct document compilation (preview mode)
	const handlePreviewCompile = (event: any) => {
		const { doctype, docname, doc } = event.detail || {}
		if (!doc || !doctype || !docname) {
			console.warn("[Typst Preview] Invalid preview compile event", event.detail)
			return
		}

		console.log("[Typst Preview] Preview mode: Direct document compilation", docname)
		currentDoctype = doctype
		sampleDocData = doc
		sampleDocSelected = true
		clearPreview()
		lastLayoutSerialized = ""
		lastTypstCode = ""
		compile()

		frappe.show_alert({
			message: __("Preview loaded: {0}", [docname]),
			indicator: "green",
		})
	}

	window.addEventListener("crispy-compile-document", handlePreviewCompile)
	// Handle source request for PDF generation
	// Replace handleSourceRequest (around line 110)
	const handleSourceRequest = () => {
		if (lastTypstCode) {
			console.log("[Typst Preview] Source requested, responding with code length:", lastTypstCode.length)
			// Dispatch CustomEvent instead of postMessage
			window.dispatchEvent(
				new CustomEvent("crispy-source-response", {
					detail: { source: lastTypstCode }
				})
			)
		} else {
			console.warn("[Typst Preview] No Typst source available yet")
			window.dispatchEvent(
				new CustomEvent("crispy-source-response", {
					detail: { source: null, error: "No Typst source compiled yet" }
				})
			)
		}
	}
	window.addEventListener("crispy-request-source", handleSourceRequest)

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
		console.log("[Typst Preview] Setting up autocomplete for doctype:", doctype)

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
			console.log("[Typst Preview] Document selected:", selectedDoc)
			sampleDocSelected = false

			if (!selectedDoc || !currentDoctype) {
				console.warn("[Typst Preview] No document or doctype selected")
				return
			}

			statusEl && (statusEl.textContent = "fetching document...")
			if (statusEl) statusEl.style.color = "#3498db"

			frappe.call({
				method: "frappe.client.get",
				args: {
					doctype: currentDoctype,
					name: selectedDoc,
				},
				callback: (r: any) => {
					if (r.message) {
						sampleDocData = r.message
						sampleDocSelected = true
						clearPreview()
						console.log("[Typst Preview] Document data fetched:", sampleDocData)
						lastLayoutSerialized = ""
						lastTypstCode = ""
						compile()

						frappe.show_alert({
							message: __("Preview updated with {0}", [selectedDoc]),
							indicator: "green",
						})
					} else {
						console.error("[Typst Preview] Failed to fetch document")
						frappe.show_alert({
							message: __("Failed to fetch document data"),
							indicator: "red",
						})
					}
				},
			})
		})

		console.log("[Typst Preview] Autocomplete setup complete")
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
	let noDocSkipCount = 0

	function scheduleCompile(reason = "hook", delay = 200) {
		if (compilationDisabled) {
			console.log(`[Typst Preview] Compilation disabled, ignoring schedule request (${reason})`)
			return
		}

		// Don't schedule compile if no sample document is selected
		if (!sampleDocSelected) {
			// Only log first occurrence to reduce console noise
			if (noDocSkipCount === 0) {
				console.log(`[Typst Preview] No sample document selected, skipping schedule requests`)
			}
			noDocSkipCount++
			return
		}

		// Reset counter when document is selected
		noDocSkipCount = 0

		console.log(`[Typst Preview] Scheduling compile (${reason}) in`, delay, "ms")
		if (compileTriggerTimeout) {
			clearTimeout(compileTriggerTimeout)
		}
		compileTriggerTimeout = window.setTimeout(() => {
			console.log("[Typst Preview] Triggering compile via schedule:", reason)
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
		if (doctype) {
			console.log("[Typst Preview] Doctype from adapter:", doctype)
			setupSampleDocAutocomplete(doctype)
		} else {
			console.warn("[Typst Preview] No doctype found, skipping sample doc setup")
		}

		if (adapter.hookDoctypeChanges) {
			unsubscribeDoctype = adapter.hookDoctypeChanges((nextDoctype) => {
				if (nextDoctype && nextDoctype !== currentDoctype) {
					console.log("[Typst Preview] Doctype changed, reconfiguring autocomplete:", nextDoctype)
					setupSampleDocAutocomplete(nextDoctype)
				}
			})
		}

		if (adapter.hookDataChanges) {
			unsubscribeAdapter = adapter.hookDataChanges(() => {
				scheduleCompile("adapter-change", 800)
			})
		}

		// Don't compile on initial adapter ready - wait for user to select a document
		console.log("[Typst Preview] Adapter initialized, waiting for sample document selection")
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
		console.log("[Typst Preview] compile() called")
		if (compilationTimeout) {
			clearTimeout(compilationTimeout)
		}
		// Use shorter debounce and defer heavy work to next frame
		compilationTimeout = window.setTimeout(() => {
			console.log("[Typst Preview] Starting compilation after debounce...")
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

		console.log("[Typst Preview] Layout or page settings changed, translating to Typst...")
		console.log("[Typst Preview] Layout sections:", (layout as any)?.sections?.length || 0)

		// Extract fields actually used in the layout
		const usedFields = extractUsedFields(layout)
		console.log(
			`[Typst Preview] Layout uses ${usedFields.size} fields:`,
			Array.from(usedFields).sort()
		)

		// Filter document to only include used fields
		const filteredDoc = filterDocumentFields(sampleDocData, usedFields)
		console.log("[Typst Preview] Filtered document fields:", Object.keys(filteredDoc || {}).sort())

		let typst: string
		try {
			let letterheadData: any = null
			if (adapter && typeof adapter.getLetterhead === "function") {
				letterheadData = adapter.getLetterhead()
				console.log("[Typst Preview] Letterhead data:", letterheadData)
			}

			// Get page settings to pass to translator
			let pageSettings: any = {}
			if (adapter && adapter.getPageSettings) {
				pageSettings = adapter.getPageSettings() || {}
			}

			// Use filtered document instead of full sampleDocData
			typst = translateJSONToTypst(layout as any, letterheadData, printFormatName, filteredDoc, pageSettings)

			console.log("[Typst Preview] Translation successful, length:", typst.length)
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
			console.log("[Typst Preview] Typst code unchanged")
			if (statusEl) {
				statusEl.textContent = "code unchanged"
				statusEl.style.color = "#95a5a6"
			}
			return
		}
		lastTypstCode = typst

		console.log("[Typst Preview] Sending to worker for compilation")
		if (statusEl) {
			statusEl.textContent = "compiling…"
			statusEl.style.color = "#f39c12"
		}
		if (downloadBtn) downloadBtn.disabled = true
		currentPdfBlob = null

		let letterheadImage: string | null = null
		if (adapter && typeof adapter.getLetterhead === "function") {
			const letterhead = adapter.getLetterhead()
			if (letterhead && (letterhead as any).image) {
				letterheadImage = (letterhead as any).image
				console.log("[Typst Preview] Including letterhead:", letterheadImage)
			}
		}

		worker.postMessage({
			typstSrc: typst,
			csrfToken: frappe?.csrf_token,
			outputFormat: previewOutputFormat,
			requestId: PREVIEW_REQUEST_ID,
			letterheadImage,
		})
		console.log("[Typst Preview] Message sent to worker")
	}

	worker.addEventListener("message", (e) => {
		const { type, ok, format, svgPages, pdfBytes, error, requestId, pageCount } = e.data || {}
		const isDownload = requestId === DOWNLOAD_REQUEST_ID
		const isViewPdf = requestId === "view-pdf"

		if (type === "init") {
			console.log("[Typst Preview] Worker ready", e.data)
			return
		}

		if (type === "compile" || !type) {
			console.log("[Typst Preview] Received compilation result")

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

				console.log("[Typst Preview] SVG pages received:", svgPages.length, "pageCount:", pageCount)

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
				} else {
					console.warn("[Typst Preview] SVG response received for download request")
					pendingPdfDownload = false
				}

				if (downloadBtn) downloadBtn.disabled = false
				if (viewPdfBtn) viewPdfBtn.disabled = false
				return
			}

			const pdfArray = new Uint8Array(pdfBytes || [])
			console.log("[Typst Preview] PDF bytes length:", pdfArray.length)

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
			console.log("[Typst Preview] Refresh button clicked - forcing recompilation")
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
			console.log("[Typst Preview] Adapter unsubscribed")
		}
		if (unsubscribeDoctype) {
			unsubscribeDoctype()
			console.log("[Typst Preview] Doctype subscription removed")
		}
		window.removeEventListener("crispy-compile-document", handlePreviewCompile)
		window.removeEventListener("crispy-request-source", handleSourceRequest)
		console.log("[Typst Preview] Preview compile listener removed")
		if (worker) {
			cleanup()
			console.log("[Typst Preview] Worker terminated")
		}
	}
}
