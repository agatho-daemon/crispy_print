// Typst Preview worker wiring for Crispy Print (Vue + Vite)

import { buildDocDictionary, translateJSONToTypst } from "./JSONToTypst"
import { createTypstWorker } from "./createTypstWorker"
import { extractUsedFields, filterDocumentFields } from "../utils/layoutFieldExtractor"
import { extractUsedFieldsFromTypstSource } from "../utils/typstFieldExtractor"
import { type CrispyLayout } from "../utils/layout"
import { ensureTableSettings, ensureTypography } from "../utils/pageSettings"
import { deepClone } from "../utils/json"
import {
	buildForegroundPlacements,
	getLetterheadFilename,
	resolveBrandingImage,
	resolveBrandingMode,
} from "./branding"
import {
	CrispyPreviewEvents,
	dispatchCrispyPreviewSource,
	dispatchCrispyPreviewStatus,
} from "../utils/events"
import { getLogger } from "../logger"

const logger = getLogger({ module: "TypstPreview" })

/**
 * Parse and format Typst error messages from server responses
 * Handles nested JSON, escaped strings, and Unicode box drawing characters
 */
export function parseTypstError(error: any): string {
	try {
		let errorStr = String(error?.message || error || "Typst compilation failed")

		// Unescape the string - may be double or triple escaped from JSON
		// Replace escaped newlines with actual newlines
		errorStr = errorStr.replace(/\\n/g, "\n")

		// Replace escaped quotes
		errorStr = errorStr.replace(/\\"/g, '"')

		// Replace escaped backslashes (but do this after other replacements)
		errorStr = errorStr.replace(/\\\\/g, "\\")

		// Replace Unicode box drawing characters
		errorStr = errorStr.replace(/\\u250c/g, "┌")
		errorStr = errorStr.replace(/\\u2500/g, "─")
		errorStr = errorStr.replace(/\\u2502/g, "│")

		// Try to extract just the Typst error part, ignoring Python tracebacks
		const typstErrorMatch = errorStr.match(
			/Typst compilation failed:\s*(.+?)(?=\n\nDuring handling|$)/s
		)
		if (typstErrorMatch) {
			errorStr = typstErrorMatch[1].trim()
		}

		// Look for the actual error message
		const errorMatch = errorStr.match(/error:\s*(.+?)(?=\n|$)/)
		const errorMessage = errorMatch ? errorMatch[1].trim() : "Compilation error"

		// Extract file location and line number
		const locationMatch = errorStr.match(/document\.typ:(\d+):(\d+)/)
		const location = locationMatch ? `Line ${locationMatch[1]}, Column ${locationMatch[2]}` : ""

		// Try to extract the code snippet
		const snippetMatch = errorStr.match(/(\d+)\s*│\s*(.+?)(?=\n|$)/m)
		const snippet = snippetMatch ? snippetMatch[2].trim() : ""

		// Build formatted error message
		const parts: string[] = []

		parts.push(`Error: ${errorMessage}`)

		if (location) {
			parts.push(`Location: ${location}`)
		}

		if (snippet) {
			parts.push("")
			parts.push("Code:")
			parts.push(`  ${snippet}`)
		}

		return parts.join("\n")
	} catch (e) {
		// Fallback: return original error as string
		return String(error?.message || error || "Compilation failed")
	}
}

export interface TypstAdapter {
	getLayout: () => CrispyLayout | null | undefined
	getDocHeader?: () => string | null | undefined
	getDocFooter?: () => string | null | undefined
	getTypstPreamble?: () => string | null | undefined
	getTypstCode?: () => string | null | undefined
	getRawTypst?: () => boolean
	getQrEnabled?: () => boolean
	getLetterhead?: () => any
	getDoctype?: () => string | null | undefined
	getDocname?: () => string | null | undefined
	getPageSettings?: () => any
	hookDataChanges?: (callback: () => void) => () => void
	hookDoctypeChanges?: (callback: (doctype: string | null | undefined) => void) => () => void
}

export function setupWorker(
	printFormatName: string,
	previewPane: HTMLElement,
	adapter: TypstAdapter,
	opts?: { createWorker?: typeof createTypstWorker }
) {
	const createWorker = opts?.createWorker || createTypstWorker
	const { worker, cleanup } = createWorker()

	worker.addEventListener("error", (err) => {
		logger.error("Worker error", err)
	})
	worker.addEventListener("messageerror", (err) => {
		logger.error("Worker messageerror", err)
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
	let qrEnabled = false
	let docNameForQr = ""
	let qrFilename = ""
	let skipNextInput = false
	let autocompleteInitialized = false
	let stylesNoticeShown = false

	// Cleanup function exported for external use (e.g., component unmount)
	function cleanupAutocomplete() {
		if (awesomplete) {
			awesomplete.destroy()
			awesomplete = null
		}

		currentDoctype = null
		autocompleteInitialized = false
		skipNextInput = false
		sampleDocSelected = false
		sampleDocData = null
		currentDocname = null
	}

	function cacheKey(doctype: string, docname: string) {
		return `${doctype}::${docname}`
	}

	function sanitizeFilename(value: string) {
		return String(value || "")
			.trim()
			.replace(/[\/\\?%*:|"<>]/g, "-")
			.replace(/\s+/g, "-")
	}

	function fetchDoc(
		doctype: string,
		docname: string,
		opts: { force?: boolean } = {}
	): Promise<Record<string, any> | null> {
		const key = cacheKey(doctype, docname)
		const cached = docCache.get(key)
		if (!opts.force && cached) return Promise.resolve(cached)

		return new Promise((resolve) => {
			if (typeof frappe === "undefined" || typeof frappe.call !== "function") {
				resolve(null)
				return
			}

			frappe.call({
				method: "crispy_print.api.v1.get_formatted_doc",
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
		dispatchCrispyPreviewStatus({ status, message })
	}

	function fontWeightToNumber(weight: string) {
		const normalized = String(weight || "").toLowerCase()
		if (normalized === "bold") return 700
		if (normalized === "semibold" || normalized === "semi-bold") return 600
		if (normalized === "medium") return 500
		if (normalized === "light") return 300
		return 400
	}

	function buildDefaultStyleDefs(pageSettings: any) {
		const safePageSettings = pageSettings ? deepClone(pageSettings) : {}
		const typography = ensureTypography(safePageSettings)
		const fieldLabel = typography.fieldLabel
		const fieldValue = typography.fieldValue
		const sectionLabel = typography.sectionLabel
		const tableSettings = ensureTableSettings(safePageSettings)
		const tableHeader = tableSettings.typography.header
		const tableBody = tableSettings.typography.body
		const tableInset = tableSettings.inset
		const tableStrokeWidth = Number.isFinite(tableSettings.stroke.width)
			? tableSettings.stroke.width
			: 0
		const formatColor = (color: string, fallback = "none") => {
			const raw = String(color || "").trim()
			if (!raw) return fallback
			if (raw.startsWith("#")) {
				return `rgb("${raw.substring(1)}")`
			}
			return raw
		}
		const tableStrokeColor = formatColor(tableSettings.stroke.color, "black")
		const tableHeaderFill = formatColor(tableSettings.header.backgroundColor, "none")
		const tableStripeFill = formatColor(tableSettings.stripe.color, "none")
		const tableStripeEnabled = Boolean(tableSettings.stripe.enabled)

		const lines: string[] = []
		lines.push("// Typography styles (auto-injected for raw Typst)")
		lines.push("#let fieldLabelStyle = (")
		lines.push(`  font: "${fieldLabel.fontFamily}",`)
		lines.push(`  size: ${fieldLabel.fontSize},`)
		lines.push(`  style: "${fieldLabel.fontStyle}",`)
		lines.push(`  weight: ${fontWeightToNumber(fieldLabel.fontWeight)},`)
		lines.push(`  fill: rgb("${fieldLabel.color}")`)
		lines.push(")")
		lines.push("")
		lines.push("#let fieldValueStyle = (")
		lines.push(`  font: "${fieldValue.fontFamily}",`)
		lines.push(`  size: ${fieldValue.fontSize},`)
		lines.push(`  style: "${fieldValue.fontStyle}",`)
		lines.push(`  weight: ${fontWeightToNumber(fieldValue.fontWeight)},`)
		lines.push(`  fill: rgb("${fieldValue.color}")`)
		lines.push(")")
		lines.push("")
		lines.push("#let sectionLabelStyle = (")
		lines.push(`  font: "${sectionLabel.fontFamily}",`)
		lines.push(`  size: ${sectionLabel.fontSize},`)
		lines.push(`  style: "${sectionLabel.fontStyle}",`)
		lines.push(`  weight: ${fontWeightToNumber(sectionLabel.fontWeight)},`)
		lines.push(`  fill: rgb("${sectionLabel.color}")`)
		lines.push(")")
		lines.push("")
		lines.push("// Table styles (auto-injected for raw Typst)")
		lines.push("#let tableHeaderStyle = (")
		lines.push(`  font: "${tableHeader.fontFamily}",`)
		lines.push(`  size: ${tableHeader.fontSize},`)
		lines.push(`  style: "${tableHeader.fontStyle}",`)
		lines.push(`  weight: ${fontWeightToNumber(tableHeader.fontWeight)},`)
		lines.push(`  fill: rgb("${tableHeader.color}")`)
		lines.push(")")
		lines.push("")
		lines.push("#let tableBodyStyle = (")
		lines.push(`  font: "${tableBody.fontFamily}",`)
		lines.push(`  size: ${tableBody.fontSize},`)
		lines.push(`  style: "${tableBody.fontStyle}",`)
		lines.push(`  weight: ${fontWeightToNumber(tableBody.fontWeight)},`)
		lines.push(`  fill: rgb("${tableBody.color}")`)
		lines.push(")")
		lines.push("")
		lines.push(
			`#let tableCellInset = (top: ${tableInset.top}pt, right: ${tableInset.right}pt, bottom: ${tableInset.bottom}pt, left: ${tableInset.left}pt)`
		)
		lines.push(
			`#let tableStroke = ${
				tableStrokeWidth > 0
					? `${tableStrokeWidth}pt + ${tableStrokeColor}`
					: "none"
			}`
		)
		lines.push(`#let tableHeaderFill = ${tableHeaderFill}`)
		lines.push(`#let tableStripeFill = ${tableStripeFill}`)
		lines.push(`#let tableStripeEnabled = ${tableStripeEnabled ? "true" : "false"}`)
		lines.push("")
		return lines.join("\n")
	}

	function typstReferencesDefaultStyles(source: string) {
		if (!source) return false
		return (
			source.includes("fieldLabelStyle") ||
			source.includes("fieldValueStyle") ||
			source.includes("sectionLabelStyle") ||
			source.includes("tableHeaderStyle") ||
			source.includes("tableBodyStyle") ||
			source.includes("tableCellInset") ||
			source.includes("tableStroke") ||
			source.includes("tableHeaderFill") ||
			source.includes("tableStripeFill") ||
			source.includes("tableStripeEnabled")
		)
	}

	function typstDefinesDefaultStyles(source: string) {
		if (!source) return false
		return (
			/#let\s+fieldLabelStyle\b/.test(source) ||
			/#let\s+fieldValueStyle\b/.test(source) ||
			/#let\s+sectionLabelStyle\b/.test(source) ||
			/#let\s+tableHeaderStyle\b/.test(source) ||
			/#let\s+tableBodyStyle\b/.test(source) ||
			/#let\s+tableCellInset\b/.test(source) ||
			/#let\s+tableStroke\b/.test(source) ||
			/#let\s+tableHeaderFill\b/.test(source) ||
			/#let\s+tableStripeFill\b/.test(source) ||
			/#let\s+tableStripeEnabled\b/.test(source)
		)
	}

	function setCurrentDoc(doctype: string, docname: string, opts: { force?: boolean } = {}) {
		currentDoctype = doctype
		currentDocname = docname
		sampleDocSelected = false
		sampleDocData = null

		clearPreview()
		lastTypstCode = ""

		if (statusEl) {
			statusEl.textContent = "fetching document…"
			statusEl.style.color = "#3498db"
		}
		dispatchStatus("fetching", docname)

		fetchDoc(doctype, docname, { force: Boolean(opts.force) }).then((doc) => {
			if (!doc) {
				logger.warn("Failed to fetch document", { doctype, docname })
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
			page.style.boxShadow =
				"0 4px 12px rgba(148, 163, 184, 0.25), 0 2px 6px rgba(148, 163, 184, 0.2)"

			page.innerHTML = svg
			const svgEl = page.querySelector("svg")
			if (svgEl) {
				svgEl.style.width = "100%"
				svgEl.style.height = "auto"
				svgEl.removeAttribute("width") // let viewBox control sizing
				svgEl.removeAttribute("height")
			}

			container.appendChild(page)
		})
	}

	// Unified preview events (single source of truth)
	const handleSetDoc = (event: any) => {
		const { doctype, docname } = event?.detail || {}
		if (!doctype || !docname) {
			logger.warn("Invalid set-doc event", event?.detail)
			return
		}
		setCurrentDoc(doctype, docname, { force: true })
	}
	window.addEventListener(CrispyPreviewEvents.SetDoc, handleSetDoc)

	const handleRefresh = () => {
		if (!currentDoctype || !currentDocname) {
			// crispy-print mode: a specific document is provided by the page
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
	window.addEventListener(CrispyPreviewEvents.Refresh, handleRefresh)

	const handleSourceRequest = () => {
		dispatchCrispyPreviewSource({ source: lastTypstCode || null })
	}
	window.addEventListener(CrispyPreviewEvents.RequestSource, handleSourceRequest)

	// PDF generation request (used by crispy-print toolbar and any other UI)
	const handlePdfRequest = (event: any) => {
		const action = (event?.detail?.action || "view") as "view" | "download"
		logger.info("PDF request received", {
			action,
			hasPdf: Boolean(currentPdfBlob),
			hasTypst: Boolean(lastTypstCode),
			docNameForQr,
		})

		if (currentPdfBlob) {
			if (action === "download") {
				logger.info("Using cached PDF for download")
				triggerPdfDownload()
				return
			}

			const url = URL.createObjectURL(currentPdfBlob)
			window.open(url, "_blank")
			setTimeout(() => URL.revokeObjectURL(url), 1000)
			return
		}

		if (!lastTypstCode) {
			logger.warn("No Typst code available for PDF request")
			frappe?.show_alert({ message: __("Typst code not ready yet"), indicator: "orange" })
			return
		}

		if (statusEl) {
			statusEl.textContent = "generating pdf…"
			statusEl.style.color = "#3498db"
		}

		pendingPdfDownload = action === "download"

		const pageSettings =
			adapter && typeof adapter.getPageSettings === "function"
				? adapter.getPageSettings() || {}
				: {}
		const letterheadData =
			adapter && typeof adapter.getLetterhead === "function" ? adapter.getLetterhead() : null
		const brandingImage = resolveBrandingImage(pageSettings, letterheadData)
		logger.info("PDF request context", {
			requestId: pendingPdfDownload ? DOWNLOAD_REQUEST_ID : VIEW_PDF_REQUEST_ID,
			pageSettings,
			brandingImage,
		})

		const requestId = pendingPdfDownload ? DOWNLOAD_REQUEST_ID : VIEW_PDF_REQUEST_ID
		logger.info("Posting PDF compile to worker", { requestId })
		worker.postMessage({
			typstSrc: lastTypstCode,
			csrfToken: frappe?.csrf_token,
			outputFormat: "pdf",
			requestId,
			seq: nextSeq(requestId),
			letterheadImage: brandingImage,
			qrData: qrEnabled ? docNameForQr : null,
			qrFilename: qrEnabled ? qrFilename : null,
		})
	}
	window.addEventListener(CrispyPreviewEvents.RequestPdf, handlePdfRequest)

	function setupSampleDocAutocomplete(doctype: string) {
		if (!doctype) {
			logger.warn("Cannot setup autocomplete - missing doctype")
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

		// Guard: prevent duplicate initialization for same doctype
		if (currentDoctype === doctype && autocompleteInitialized) {
			return
		}

		// Clean up previous Awesomplete instance
		if (awesomplete) {
			awesomplete.destroy()
			awesomplete = null
		}

		// Remove old event listeners by cloning the input element
		if (autocompleteInitialized && sampleDocInput.parentNode) {
			const newInput = sampleDocInput.cloneNode(true) as HTMLInputElement
			sampleDocInput.parentNode.replaceChild(newInput, sampleDocInput)
			// Update reference to the new input
			const refreshedInput = previewPane.querySelector<HTMLInputElement>("#typst-sample-doc-input")
			if (!refreshedInput) {
				logger.error("Autocomplete failed to get refreshed input element")
				return
			}
			// Update the closure reference (this is a bit tricky, but we're in the same scope)
			// The parent function has sampleDocInput - we can't reassign it from here
			// So we'll work with refreshedInput for the rest of this function
			const workingInput = refreshedInput

			currentDoctype = doctype
			currentDocname = null
			autocompleteInitialized = true
			skipNextInput = false

			workingInput.placeholder = `Search ${doctype}...`
			workingInput.setAttribute("data-doctype", doctype)
			workingInput.value = ""
			sampleDocData = null
			sampleDocSelected = false

			awesomplete = new Awesomplete(workingInput, {
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
						if (!awesomplete || !workingInput?.isConnected) {
							return
						}
						if (r.message && r.message.length) {
							awesomplete.list = r.message.map((d: any) => ({
								label: d.value + (d.description ? " - " + __(d.description) : ""),
								value: d.value,
							}))
						} else {
							awesomplete.list = []
						}
					},
				})
			}

			workingInput.addEventListener("focus", () => {
				searchDocs(workingInput.value)
			})

			workingInput.addEventListener(
				"input",
				frappe.utils.debounce(() => {
					if (skipNextInput) {
						skipNextInput = false
						return
					}
					sampleDocSelected = false
					sampleDocData = null
					searchDocs(workingInput.value)
				}, 300)
			)

			workingInput.addEventListener("awesomplete-selectcomplete", () => {
				skipNextInput = true // Prevent input handler from re-triggering
				const selectedDoc = workingInput.value
				sampleDocSelected = false
				currentDocname = selectedDoc

				if (!selectedDoc || !currentDoctype) {
					logger.warn("No document or doctype selected")
					return
				}

				statusEl && (statusEl.textContent = "fetching document...")
				if (statusEl) statusEl.style.color = "#3498db"

				setCurrentDoc(currentDoctype, selectedDoc, { force: true })
			})
		} else {
			// First initialization
			currentDoctype = doctype
			currentDocname = null
			autocompleteInitialized = true
			skipNextInput = false

			if (!sampleDocInput) {
				logger.warn("Sample doc input not found")
				return
			}

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
			const awesompleteInstance = awesomplete

			function searchDocs(txt: string) {
				frappe.call({
					method: "frappe.desk.search.search_link",
					args: {
						doctype,
						txt: txt || "",
						page_length: 20,
					},
					callback: (r: any) => {
						if (
							!awesomplete ||
							awesomplete !== awesompleteInstance ||
							!sampleDocInput?.isConnected
						) {
							return
						}
						if (r.message && r.message.length) {
							awesomplete.list = r.message.slice(0, 20).map((d: any) => ({
								label: d.value + (d.description ? " - " + __(d.description) : ""),
								value: d.value,
							}))
						} else {
							awesomplete.list = []
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
					if (skipNextInput) {
						skipNextInput = false
						return
					}
					sampleDocSelected = false
					sampleDocData = null
					searchDocs(sampleDocInput.value)
				}, 300)
			)

			sampleDocInput.addEventListener("awesomplete-selectcomplete", () => {
				skipNextInput = true // Prevent input handler from re-triggering
				const selectedDoc = sampleDocInput.value
				sampleDocSelected = false
				currentDocname = selectedDoc

				if (!selectedDoc || !currentDoctype) {
					logger.warn("No document or doctype selected")
					return
				}

				statusEl && (statusEl.textContent = "fetching document...")
				if (statusEl) statusEl.style.color = "#3498db"

				setCurrentDoc(currentDoctype, selectedDoc, { force: true })
			})
		}
	}

	const PREVIEW_REQUEST_ID = "preview"
	const DOWNLOAD_REQUEST_ID = "download"
	const VIEW_PDF_REQUEST_ID = "view-pdf"
	const previewOutputFormat = "svg"
	svgContainer?.classList.remove("preview-hidden")

	let compilationTimeout: number | undefined
	let lastTypstCode = ""
	let lastQrPayload = ""
	let currentPdfBlob: Blob | null = null
	let pendingPdfDownload = false
	let compileTriggerTimeout: number | undefined
	let missingLayoutRetries = 0
	let unsubscribeAdapter: (() => void) | null = null
	let unsubscribeDoctype: (() => void) | null = null
	let compilationDisabled = false
	let seqCounter = 0
	const latestSeqByRequest: Record<string, number> = {}

	function nextSeq(requestId: string): number {
		const seq = ++seqCounter
		latestSeqByRequest[requestId] = seq
		return seq
	}

	function scheduleCompile(delay = 200) {
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
			logger.warn("No adapter provided")
			return
		}

		const doctype = adapter.getDoctype?.()
		const docname = adapter.getDocname?.()
		if (doctype && docname) {
			// crispy-print mode: render a specific document without requiring sample selection
			setCurrentDoc(doctype, docname, { force: true })
		}
		// Note: Don't call setupSampleDocAutocomplete here - let the watcher handle it

		if (adapter.hookDoctypeChanges) {
			unsubscribeDoctype = adapter.hookDoctypeChanges((nextDoctype) => {
				if (nextDoctype) {
					if (nextDoctype !== currentDoctype) {
						// Reset and reinitialize for new doctype
						autocompleteInitialized = false
						setupSampleDocAutocomplete(nextDoctype)
					} else {
						// Same doctype, ensure it's initialized (handles page navigation back)
						setupSampleDocAutocomplete(nextDoctype)
					}
				}
			})
		}

		if (adapter.hookDataChanges) {
			unsubscribeAdapter = adapter.hookDataChanges(() => {
				scheduleCompile(200)
			})
		}

		// Don't compile on initial adapter ready - wait for user to select a document
	}

	function getLayout() {
		if (!adapter) {
			logger.warn("Adapter not available")
			return null
		}

		if (!adapter.getLayout) {
			logger.error("Adapter does not have getLayout function")
			return null
		}

		return adapter.getLayout()
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

	function getQrSettings() {
		if (!adapter || typeof adapter.getPageSettings !== "function") return {}
		const pageSettings = adapter.getPageSettings() || {}
		return pageSettings.qr || {}
	}

	function buildQrPayload(doc: Record<string, any> | null, fields: string[]) {
		if (!doc) return ""
		if (!fields.length) return String(doc.name || "")
		const wantsTimestamp = fields.includes("timestamp")
		const lines: string[] = []

		if (wantsTimestamp) {
			const date = doc.posting_date || ""
			const time = doc.posting_time || "00:00:00"
			if (date) {
				lines.push(`timestamp: ${date}T${time}`)
			}
		}

		fields.forEach((fieldname) => {
			if (fieldname === "timestamp") return
			const value = doc[fieldname]
			lines.push(`${fieldname}: ${value ?? ""}`)
		})

		return lines.join("\n")
	}

	function resolveQrPayload() {
		const enabled =
			adapter && typeof adapter.getQrEnabled === "function"
				? Boolean(adapter.getQrEnabled())
				: false
		const docName = (sampleDocData as any)?.name || currentDocname || ""
		const filename = enabled && docName ? `${sanitizeFilename(docName)}-qr.svg` : ""
		const qrSettings = getQrSettings()
		const fieldList = Array.isArray(qrSettings.fields) ? qrSettings.fields : []
		const payload = buildQrPayload(sampleDocData, fieldList)

		return {
			qrEnabled: enabled,
			qrData: enabled ? payload : null,
			qrFilename: enabled ? filename : null,
			qrSettings,
		}
	}

	function buildPageSettingsBlock(options: {
		pageSettings?: Record<string, any> | null
		letterheadData?: Record<string, any> | null
		qrEnabled?: boolean
		qrFilename?: string | null
		qrSettings?: Record<string, any> | null
	}) {
		const lines: string[] = []
		const pageSettings = options.pageSettings || {}
		const margins = pageSettings.margins || {}
		const pageSize = String(pageSettings.pageSize || "A4").toLowerCase()
		const orientation = String(pageSettings.orientation || "portrait")
		const marginValue = (value: any, fallback: number) => {
			const num = Number(value)
			return Number.isFinite(num) ? num : fallback
		}
		const marginTop = marginValue(margins.top, 25)
		const marginBottom = marginValue(margins.bottom, 20)
		const marginLeft = marginValue(margins.left, 20)
		const marginRight = marginValue(margins.right, 20)
		const brandingMode = resolveBrandingMode(pageSettings, options.letterheadData)
		const letterheadFilename = getLetterheadFilename(pageSettings, options.letterheadData)
		const foregroundLines = buildForegroundPlacements({
			pageSettings,
			brandingMode,
			qrEnabled: options.qrEnabled,
			qrFilename: options.qrFilename,
			qrSettings: options.qrSettings,
		})

		lines.push("// Page settings (from Settings pane)")
		lines.push("#set page(")
		lines.push(`  paper: "${pageSize}",`)
		if (orientation === "landscape") {
			lines.push("  flipped: true,")
		}
		lines.push(
			`  margin: (top: ${marginTop}mm, bottom: ${marginBottom}mm, left: ${marginLeft}mm, right: ${marginRight}mm),`
		)
		lines.push("  header: header_block,")
		lines.push("  footer: footer_block,")
		if (letterheadFilename) {
			lines.push(`  background: image("${letterheadFilename}", width: 100%)`)
		}
		if (foregroundLines.length) {
			lines.push("  foreground: [")
			foregroundLines.forEach((line) => {
				lines.push(`    ${line}`)
			})
			lines.push("  ]")
		}
		lines.push(")")
		lines.push("")

		return lines.join("\n").trim()
	}

	function buildHeaderFooterBlock(options: { docHeader?: string; docFooter?: string }) {
		const lines: string[] = []

		lines.push("#let header_block = []")
		lines.push("#let footer_block = []")
		lines.push("")

		if (options.docHeader && options.docHeader.trim()) {
			lines.push("// Document Header")
			lines.push(options.docHeader.trim())
			lines.push("")
		}
		if (options.docFooter && options.docFooter.trim()) {
			lines.push("// Document Footer")
			lines.push(options.docFooter.trim())
			lines.push("")
		}
		return lines.join("\n").trim()
	}

	function performCompilation() {
		clearPreview()

		// Allow compile if we already have document data, even if sampleDocSelected wasn't toggled
		if (!sampleDocData) {
			logger.warn("No document data; skipping compile")
			if (statusEl) {
				statusEl.textContent = "select a document"
				statusEl.style.color = "#e67e22"
			}
			// Don't dispatch error - just waiting for user to select a document
			return
		}

		const rawTypst =
			adapter && typeof adapter.getRawTypst === "function" ? adapter.getRawTypst() : false
		const layout = getLayout()

		if (!layout && !rawTypst) {
			logger.error("No layout found from adapter")
			if (statusEl) {
				statusEl.textContent = "waiting for layout..."
				statusEl.style.color = "#e67e22"
			}
			if (missingLayoutRetries < 5) {
				missingLayoutRetries += 1
				logger.warn(
					`Retrying compile due to missing layout (attempt ${missingLayoutRetries}/5)`
				)
				scheduleCompile(500 * missingLayoutRetries)
			} else {
				logger.error("Max retries (5) reached. Disabling compilation.")
				compilationDisabled = true
				if (statusEl) {
					statusEl.textContent = "no layout data"
					statusEl.style.color = "#e74c3c"
				}
			}
			return
		}
		missingLayoutRetries = 0

		// Intentionally skip serialized layout diffing; always compile on trigger.

		let typst: string
		let qrPayloadChanged = false
		try {
			const letterheadCandidate =
				adapter && typeof adapter.getLetterhead === "function" ? adapter.getLetterhead() : null

			// Get page settings to pass to translator
			let pageSettings: any = {}
			if (adapter && adapter.getPageSettings) {
				pageSettings = adapter.getPageSettings() || {}
			}
			const brandingMode = resolveBrandingMode(pageSettings, letterheadCandidate)
			const letterheadData = brandingMode === "letterhead" ? letterheadCandidate : null

			const docHeader =
				adapter && typeof adapter.getDocHeader === "function" ? adapter.getDocHeader() || "" : ""
			const docFooter =
				adapter && typeof adapter.getDocFooter === "function" ? adapter.getDocFooter() || "" : ""
			const typstPreamble =
				adapter && typeof adapter.getTypstPreamble === "function"
					? adapter.getTypstPreamble() || ""
					: ""
			const typstCode =
				adapter && typeof adapter.getTypstCode === "function" ? adapter.getTypstCode() || "" : ""
			const typstFieldSource = [docHeader, docFooter, typstPreamble, typstCode]
				.filter(Boolean)
				.join("\n")
			const usedFields = rawTypst
				? extractUsedFieldsFromTypstSource(typstFieldSource)
				: extractUsedFields(layout)
			const filteredDoc = rawTypst
				? filterDocumentFields(sampleDocData, usedFields, {
						includeAllChildFieldsIfUnspecified: true,
					})
				: filterDocumentFields(sampleDocData, usedFields)
			const qrPayload = resolveQrPayload()
			qrEnabled = qrPayload.qrEnabled
			docNameForQr = qrPayload.qrData ? String(qrPayload.qrData) : ""
			qrFilename = qrPayload.qrFilename ? String(qrPayload.qrFilename) : ""
			const qrPayloadKey = qrPayload.qrData ? String(qrPayload.qrData) : ""
			qrPayloadChanged = qrPayloadKey !== lastQrPayload
			lastQrPayload = qrPayloadKey

			// Use filtered document instead of full sampleDocData
			if (rawTypst) {
				const parts: string[] = []
				parts.push(buildDocDictionary(filteredDoc, printFormatName))
				parts.push(buildDefaultStyleDefs(pageSettings))
				const headerFooterBlock = buildHeaderFooterBlock({ docHeader, docFooter })
				if (headerFooterBlock) {
					parts.push(headerFooterBlock)
				}
				const pageSettingsBlock = buildPageSettingsBlock({
					pageSettings,
					letterheadData,
					qrEnabled,
					qrFilename,
					qrSettings: qrPayload.qrSettings,
				})
				if (pageSettingsBlock) {
					parts.push(pageSettingsBlock)
				}
				if (typstPreamble && typstPreamble.trim()) {
					parts.push(typstPreamble.trim())
				}
				if (typstCode && typstCode.trim()) {
					parts.push(typstCode.trim())
				}
				typst = parts.join("\n\n")
			} else {
				typst = translateJSONToTypst(layout as any, letterheadData, printFormatName, filteredDoc, {
					...pageSettings,
					docHeader,
					docFooter,
					typstPreamble,
					qrEnabled,
					qrFilename,
					qrSettings: qrPayload.qrSettings,
				})
			}
		} catch (e: any) {
			logger.error("Translation error", e)
			const formattedError = parseTypstError(e)
			if (statusEl) {
				statusEl.textContent = "translation error"
				statusEl.style.color = "#e74c3c"
			}
			dispatchStatus("error", formattedError)
			// Don't show frappe alert - error will be displayed in preview pane
			return
		}

		if (typst === lastTypstCode && !qrPayloadChanged) {
				if (statusEl) {
					statusEl.textContent = "up to date"
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

		const pageSettings =
			adapter && typeof adapter.getPageSettings === "function"
				? adapter.getPageSettings() || {}
				: {}
		const letterheadData =
			adapter && typeof adapter.getLetterhead === "function" ? adapter.getLetterhead() : null
		const brandingImage = resolveBrandingImage(pageSettings, letterheadData)

		worker.postMessage({
			typstSrc: typst,
			csrfToken: frappe?.csrf_token,
			outputFormat: previewOutputFormat,
			requestId: PREVIEW_REQUEST_ID,
			seq: nextSeq(PREVIEW_REQUEST_ID),
			letterheadImage: brandingImage,
			qrData: qrEnabled ? docNameForQr : null,
			qrFilename: qrEnabled ? qrFilename : null,
		})
	}

	worker.addEventListener("message", (e) => {
		const { type, ok, format, svgPages, pdfBytes, error, requestId, seq } = e.data || {}
		if (requestId && typeof seq === "number") {
			const expected = latestSeqByRequest[requestId]
			if (typeof expected === "number" && seq !== expected) {
				return
			}
		}
		const isDownload = requestId === DOWNLOAD_REQUEST_ID
		const isViewPdf = requestId === VIEW_PDF_REQUEST_ID

		if (type === "init") {
			return
		}

		if (type === "compile" || !type) {
			if (requestId === VIEW_PDF_REQUEST_ID || requestId === DOWNLOAD_REQUEST_ID) {
				logger.info("PDF compile response", {
					ok,
					requestId,
					format,
					bytes: Array.isArray(pdfBytes) ? pdfBytes.length : 0,
				})
			}
			if (!ok) {
				logger.error("Compilation failed", error)
				const formattedError = parseTypstError(error)
				if (statusEl) {
					statusEl.textContent = isDownload || isViewPdf ? "pdf error" : "error"
					statusEl.style.color = "#e74c3c"
				}
				dispatchStatus("error", formattedError)
				// Don't show frappe alert - error will be displayed in preview pane
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
					logger.warn("SVG response received for download request")
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
				logger.warn("PDF response received for preview request")
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

			const pageSettings =
				adapter && typeof adapter.getPageSettings === "function"
					? adapter.getPageSettings() || {}
					: {}
			const letterheadData =
				adapter && typeof adapter.getLetterhead === "function" ? adapter.getLetterhead() : null
			const brandingImage = resolveBrandingImage(pageSettings, letterheadData)

			worker.postMessage({
				typstSrc: lastTypstCode,
				csrfToken: frappe?.csrf_token,
				outputFormat: "pdf",
				requestId: VIEW_PDF_REQUEST_ID,
				seq: nextSeq(VIEW_PDF_REQUEST_ID),
				letterheadImage: brandingImage,
				...resolveQrPayload(),
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

			const pageSettings =
				adapter && typeof adapter.getPageSettings === "function"
					? adapter.getPageSettings() || {}
					: {}
			const letterheadData =
				adapter && typeof adapter.getLetterhead === "function" ? adapter.getLetterhead() : null
			const brandingImage = resolveBrandingImage(pageSettings, letterheadData)

			worker.postMessage({
				typstSrc: lastTypstCode,
				csrfToken: frappe?.csrf_token,
				outputFormat: "pdf",
				requestId: DOWNLOAD_REQUEST_ID,
				seq: nextSeq(DOWNLOAD_REQUEST_ID),
				letterheadImage: brandingImage,
				...resolveQrPayload(),
			})
		})

	refreshBtn &&
		(refreshBtn.onclick = () => {
			// Report-mode builder preview compiles outside setupWorker (via store.compileReportPreview).
			// Avoid setting "refreshing..." when this worker has no document context.
			const adapterDoctype = adapter.getDoctype?.()
			const adapterDocname = adapter.getDocname?.()
			const canRefreshViaWorker = Boolean(
				sampleDocSelected || (currentDoctype && currentDocname) || (adapterDoctype && adapterDocname)
			)
			if (!canRefreshViaWorker) {
				return
			}
			if (statusEl) {
				statusEl.textContent = "refreshing..."
				statusEl.style.color = "#3498db"
			}
			lastTypstCode = "" // Force recompilation by clearing cached code
			missingLayoutRetries = 0
			compilationDisabled = false
			scheduleCompile(0)
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
		window.removeEventListener(CrispyPreviewEvents.SetDoc, handleSetDoc)
		window.removeEventListener(CrispyPreviewEvents.Refresh, handleRefresh)
		window.removeEventListener(CrispyPreviewEvents.RequestSource, handleSourceRequest)
		window.removeEventListener(CrispyPreviewEvents.RequestPdf, handlePdfRequest)

		// Cleanup autocomplete
		cleanupAutocomplete()

		if (worker) {
			cleanup()
		}
	}
}
