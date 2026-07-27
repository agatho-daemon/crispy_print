// Typst Preview worker wiring for Crispy Print (Vue + Vite)

import { buildDocDictionary, translateJSONToTypst } from "./JSONToTypst"
import { createTypstWorker } from "./createTypstWorker"
import { extractUsedFields, filterDocumentFields } from "../utils/layoutFieldExtractor"
import { extractUsedFieldsFromTypstSource } from "../utils/typstFieldExtractor"
import { type CrispyLayout } from "../utils/layout"
import { resolveBrandingImage, resolveBrandingImages, resolveBrandingMode } from "./branding"
import {
	CrispyPreviewEvents,
	dispatchCrispyPreviewSource,
	dispatchCrispyPreviewStatus,
} from "../utils/events"
import { getLogger } from "../logger"
import { createSampleDocAutocomplete } from "./workerAutocomplete"
import {
	buildRawQrBlock,
	normalizeDocImageAssets,
	parseTypstError,
} from "./workerCompilation"
import { createDocumentLoader, sanitizeFilename } from "./workerDocuments"
import { buildCustomQrPayload } from "../utils/customQr"
import {
	DOWNLOAD_REQUEST_ID,
	PREVIEW_REQUEST_ID,
	VIEW_PDF_REQUEST_ID,
	downloadPdfBlob,
	openPdfBlob,
	printPdfBlob,
	postPdfCompile,
	type PdfAction,
} from "./workerPdf"
import {
	buildRawTypstHelperBlock,
	extractCrispyBlockIds,
	extractCrispyImageAssetFiles,
} from "./rawTypstHelpers"

const logger = getLogger({ module: "TypstPreview" })
export { parseTypstError } from "./workerCompilation"

export interface TypstAdapter {
	getLayout: () => CrispyLayout | null | undefined
	getDocHeader?: () => string | null | undefined
	getDocFooter?: () => string | null | undefined
	getTypstPreamble?: () => string | null | undefined
	getTypstCode?: () => string | null | undefined
	getPdfStandard?: () => string | null | undefined
	getRawTypst?: () => boolean
	getPrintBehavior?: () => Record<string, any> | null | undefined
	getQrEnabled?: () => boolean
	getLetterhead?: () => any
	getDoctype?: () => string | null | undefined
	getDocname?: () => string | null | undefined
	get_presentation_settings?: () => any
	getTypstBlocks?: () => any[] | null | undefined
	onPdfReady?: (context: TypstPdfReadyContext) => Promise<void> | void
	onPreviewPdfReady?: (bytes: Uint8Array) => Promise<void> | void
	hookDataChanges?: (callback: () => void) => () => void
	hookDoctypeChanges?: (callback: (doctype: string | null | undefined) => void) => () => void
}

export interface TypstPdfReadyContext {
	action: PdfAction
	typstSource: string
	pdfBlob: Blob
	pdfStandard?: string | null
}

function getCurrentSiteName(): string {
	const frappeAny = frappe as any
	return String(
		frappeAny?.boot?.sitename ||
			frappeAny?.boot?.site_name ||
			frappeAny?.boot?.site ||
			frappeAny?.site_name ||
			""
	).trim()
}

export function setupWorker(
	printFormatName: string,
	previewPane: HTMLElement,
	adapter: TypstAdapter,
	opts?: { createWorker?: typeof createTypstWorker; instanceId?: string }
) {
	const createWorker = opts?.createWorker || createTypstWorker
	const { worker, cleanup } = createWorker()
	const instanceId =
		opts?.instanceId ||
		previewPane.dataset.typstPreviewInstanceId ||
		`typst-preview-${Math.random().toString(36).slice(2)}`
	previewPane.dataset.typstPreviewInstanceId = instanceId

	let disposed = false
	const handleWorkerError = (err: Event) => {
		logger.error("Worker error", err)
		if (statusEl) {
			statusEl.textContent = __("worker error")
			statusEl.style.color = "#e74c3c"
		}
		dispatchStatus("error", "worker error")
	}
	const handleWorkerMessageError = (err: MessageEvent) => {
		logger.error("Worker messageerror", err)
		if (statusEl) {
			statusEl.textContent = __("worker message error")
			statusEl.style.color = "#e74c3c"
		}
		dispatchStatus("error", "worker message error")
	}
	worker.addEventListener("error", handleWorkerError)
	worker.addEventListener("messageerror", handleWorkerMessageError)

	const statusEl = previewPane.querySelector<HTMLElement>("#typst-status")
	const previewContainer = previewPane.querySelector<HTMLElement>("#typst-pdf-container")
	const downloadBtn = previewPane.querySelector<HTMLButtonElement>("#typst-download")
	const viewPdfBtn = previewPane.querySelector<HTMLButtonElement>("#typst-view-pdf")
	const refreshBtn = previewPane.querySelector<HTMLButtonElement>("#typst-refresh")
	const viewCodeBtn = previewPane.querySelector<HTMLButtonElement>("#typst-view-code")

	let sampleDocData: Record<string, any> | null = null
	let currentDoctype: string | null = null
	let currentDocname: string | null = null
	let sampleDocSelected = false
	let qrEnabled = false
	let docNameForQr = ""
	let qrFilename = ""
	let stylesNoticeShown = false
	const documentLoader = createDocumentLoader()
	let documentLoadGeneration = 0

	function clearSelectedDocument() {
		sampleDocSelected = false
		sampleDocData = null
	}

	function dispatchStatus(status: "fetching" | "compiling" | "ready" | "error", message?: string) {
		dispatchCrispyPreviewStatus({ status, message, instanceId })
	}

	function shouldHandleEvent(event: any) {
		const targetInstanceId = event?.detail?.instanceId
		return !targetInstanceId || targetInstanceId === instanceId
	}

	function invalidatePendingResponses() {
		for (const requestId of [PREVIEW_REQUEST_ID, DOWNLOAD_REQUEST_ID, VIEW_PDF_REQUEST_ID]) {
			latestSeqByRequest[requestId] = ++seqCounter
		}
	}

	function resetCompilationLatch() {
		missingLayoutRetries = 0
		compilationDisabled = false
	}

	function clearPdfBlob() {
		currentPdfBlob = null
	}

	function resetCompiledArtifacts(clearTypstCode = true) {
		clearPdfBlob()
		invalidatePendingResponses()
		if (clearTypstCode) {
			lastTypstCode = ""
		}
	}

	function setCurrentDoc(doctype: string, docname: string, opts: { force?: boolean } = {}) {
		const capturedGeneration = ++documentLoadGeneration
		currentDoctype = doctype
		currentDocname = docname
		clearSelectedDocument()
		resetCompilationLatch()
		resetCompiledArtifacts(true)

		if (statusEl) {
			statusEl.textContent = __("fetching document…")
			statusEl.style.color = "#3498db"
		}
		dispatchStatus("fetching", docname)

		const qrSourceMode = getEffectiveQrSourceMode()
		documentLoader
			.fetchDoc(doctype, docname, {
				force: Boolean(opts.force),
				qrSourceMode,
				fields: getDocumentRequestFields(),
				allowDocumentCodePreview: qrSourceMode === "document_code_profile",
			})
			.then((doc) => {
			if (disposed || capturedGeneration !== documentLoadGeneration) {
				return
			}
			if (!doc) {
				logger.warn("Failed to fetch document", { doctype, docname })
				if (statusEl) {
					statusEl.textContent = __("document not found")
					statusEl.style.color = "#e74c3c"
				}
				dispatchStatus("error", "document not found")
				return
			}

			sampleDocData = doc
			sampleDocSelected = true
			window.dispatchEvent(
				new CustomEvent(CrispyPreviewEvents.Document, {
					detail: { doctype, docname, document: doc, instanceId },
				})
			)
			compile()

			frappe?.show_alert?.({
				message: __("Preview loaded: {0}", [docname]),
				indicator: "green",
			})
			})
	}

	// Unified preview events (single source of truth)
	const handleSetDoc = (event: any) => {
		if (!shouldHandleEvent(event)) return
		const { doctype, docname } = event?.detail || {}
		if (!doctype || !docname) {
			logger.warn("Invalid set-doc event", event?.detail)
			return
		}
		setCurrentDoc(doctype, docname, { force: true })
	}
	window.addEventListener(CrispyPreviewEvents.SetDoc, handleSetDoc)

	const handleRefresh = (event: any) => {
		if (!shouldHandleEvent(event)) return
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

	const handleSourceRequest = (event: any) => {
		if (!shouldHandleEvent(event)) return
		dispatchCrispyPreviewSource({ source: lastTypstCode || null, instanceId })
	}
	window.addEventListener(CrispyPreviewEvents.RequestSource, handleSourceRequest)
	const handleSourceUpdate = (event: any) => {
		if (!shouldHandleEvent(event)) return
		const source = event?.detail?.source
		if (typeof source === "string") {
			resetCompiledArtifacts(false)
			lastTypstCode = source
		}
	}
	window.addEventListener(CrispyPreviewEvents.Source, handleSourceUpdate)

	async function notifyPdfReady(action: PdfAction, pdfBlob: Blob) {
		if (typeof adapter.onPdfReady !== "function" || !lastTypstCode) {
			return
		}
		const pdfStandard =
			adapter && typeof adapter.getPdfStandard === "function"
				? adapter.getPdfStandard() || "PDF/A-2u"
				: "PDF/A-2u"
		await adapter.onPdfReady({
			action,
			typstSource: lastTypstCode,
			pdfBlob,
			pdfStandard,
		})
	}

	// PDF generation request (used by crispy-print toolbar and any other UI)
	const handlePdfRequest = async (event: any) => {
		if (!shouldHandleEvent(event)) return
		const action = (event?.detail?.action || "view") as PdfAction
		logger.info("PDF request received", {
			action,
			hasPdf: Boolean(currentPdfBlob),
			hasTypst: Boolean(lastTypstCode),
			docNameForQr,
		})

		if (currentPdfBlob) {
			if (action === "print") {
				const printOpened = printPdfBlob(currentPdfBlob, {
					onPrint: () => {
						frappe?.show_alert({
							message: __("Print dialog opened."),
							indicator: "green",
						})
					},
					onError: (error) => {
						logger.error("Document printing failed", error)
						frappe?.show_alert({
							message: __("Document printing failed."),
							indicator: "red",
						})
					},
				})
				if (!printOpened) {
					frappe?.show_alert({
						message: __("Document printing was blocked by the browser."),
						indicator: "orange",
					})
					return
				}
				try {
					await notifyPdfReady(action, currentPdfBlob)
				} catch (err) {
					logger.error("Failed to record issued document snapshot", err)
					frappe?.show_alert({
						message: __("Could not record issued document snapshot."),
						indicator: "red",
					})
				}
				return
			}
			try {
				await notifyPdfReady(action, currentPdfBlob)
			} catch (err) {
				logger.error("Failed to record issued document snapshot", err)
				frappe?.show_alert({
					message: __("Could not record issued document snapshot."),
					indicator: "red",
				})
				return
			}
			if (action === "download") {
				logger.info("Using cached PDF for download")
				triggerPdfDownload()
				return
			}

			openPdfBlob(currentPdfBlob)
			return
		}

		if (action === "print") {
			frappe?.show_alert({
				message: __("Document preview is not ready to print."),
				indicator: "orange",
			})
			return
		}

		if (!lastTypstCode) {
			logger.warn("No Typst code available for PDF request")
			frappe?.show_alert({ message: __("Typst code not ready yet"), indicator: "orange" })
			return
		}

		if (statusEl) {
			statusEl.textContent = __("generating pdf…")
			statusEl.style.color = "#3498db"
		}

		const presentation_settings =
			adapter && typeof adapter.get_presentation_settings === "function"
				? adapter.get_presentation_settings() || {}
				: {}
		const letterheadData =
			adapter && typeof adapter.getLetterhead === "function" ? adapter.getLetterhead() : null
		const brandingImage = resolveBrandingImage(presentation_settings, letterheadData)
		const brandingImages = resolveBrandingImages(presentation_settings, letterheadData)
		logger.info("PDF request context", {
			requestId: action === "download" ? DOWNLOAD_REQUEST_ID : VIEW_PDF_REQUEST_ID,
			presentation_settings,
			brandingImage,
			brandingImages,
		})

		const requestId = action === "download" ? DOWNLOAD_REQUEST_ID : VIEW_PDF_REQUEST_ID
		const pdfStandard =
			adapter && typeof adapter.getPdfStandard === "function"
				? adapter.getPdfStandard() || "PDF/A-2u"
				: "PDF/A-2u"
		logger.info("Posting PDF compile to worker", { requestId })
		try {
			postPdfCompile({
				worker,
				typstSrc: lastTypstCode,
				pdfStandard,
				requestId,
				seq: nextSeq(requestId),
				assetFiles: lastCompileAssetFiles,
				qrData: qrEnabled ? docNameForQr : null,
				qrFilename: qrEnabled ? qrFilename : null,
				barcodeOptions: qrEnabled ? getBarcodeOptions() : null,
			})
		} catch (err) {
			logger.error("Failed to post PDF compile", err)
			if (statusEl) {
				statusEl.textContent = __("pdf error")
				statusEl.style.color = "#e74c3c"
			}
			dispatchStatus("error", "failed to start pdf compile")
		}
	}
	window.addEventListener(CrispyPreviewEvents.RequestPdf, handlePdfRequest)

	const autocomplete = createSampleDocAutocomplete({
		previewPane,
		getInput: () => previewPane.querySelector<HTMLInputElement>("#typst-sample-doc-input"),
		getCurrentDoctype: () => currentDoctype,
		setCurrentDoctype: (doctype) => {
			currentDoctype = doctype
		},
		setCurrentDocname: (docname) => {
			currentDocname = docname
		},
		clearSelectedDocument,
		onSelect: (doctype, docname) => setCurrentDoc(doctype, docname, { force: true }),
		setFetchingStatus: () => {
			statusEl && (statusEl.textContent = __("fetching document..."))
			if (statusEl) statusEl.style.color = "#3498db"
		},
	})

	const previewOutputFormat = "pdf"
	previewContainer?.classList.remove("preview-hidden")

	let compilationTimeout: number | undefined
	let lastTypstCode = ""
	let lastCompileAssetFiles: string[] = []
	let lastQrPayload = ""
	let currentPdfBlob: Blob | null = null
	let compileTriggerTimeout: number | undefined
	let compilationFrame: number | undefined
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
			const layout = adapter?.getLayout?.()
			const rawTypst = adapter?.getRawTypst?.()
			if (layout || rawTypst) {
				resetCompilationLatch()
			} else {
				return
			}
		}

		if (disposed) {
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
		downloadPdfBlob(currentPdfBlob, `${printFormatName.replace(/\s+/g, "_")}_preview.pdf`)
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
		// Note: autocomplete is initialized by the doctype watcher.

		if (adapter.hookDoctypeChanges) {
			unsubscribeDoctype = adapter.hookDoctypeChanges((nextDoctype) => {
				if (nextDoctype) {
					if (nextDoctype !== currentDoctype) {
						// Reset and reinitialize for new doctype
						autocomplete.reset()
						autocomplete.setup(nextDoctype)
					} else {
						// Same doctype, ensure it's initialized (handles page navigation back)
						autocomplete.setup(nextDoctype)
					}
				}
			})
		}

		if (adapter.hookDataChanges) {
			unsubscribeAdapter = adapter.hookDataChanges(() => {
				resetCompiledArtifacts(false)
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
		if (disposed) {
			return
		}
		if (compilationTimeout) {
			clearTimeout(compilationTimeout)
		}
		if (compilationFrame) {
			cancelAnimationFrame(compilationFrame)
		}
		// Use shorter debounce and defer heavy work to next frame
		compilationTimeout = window.setTimeout(() => {
			// Split work across frames to avoid blocking
			compilationFrame = requestAnimationFrame(() => {
				compilationFrame = undefined
				performCompilation()
			})
		}, 150)
	}

	function getQrSettings() {
		if (!adapter || typeof adapter.get_presentation_settings !== "function") return {}
		const presentation_settings = adapter.get_presentation_settings() || {}
		return presentation_settings.qr || {}
	}

	function getEffectiveQrSourceMode() {
		const qrSettings = getQrSettings()
		const mode = String(qrSettings.sourceMode || "").trim()
		if (mode === "document_code_profile" || mode === "custom" || mode === "basic") {
			return mode
		}
		return ""
	}

	function getDocumentRequestFields() {
		const fields = new Set<string>(["name", "doctype", "docstatus", "modified"])
		const rawTypst =
			adapter && typeof adapter.getRawTypst === "function" ? adapter.getRawTypst() : false
		const layout = getLayout()

		if (rawTypst) {
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
			const typstBlocks =
				adapter && typeof adapter.getTypstBlocks === "function"
					? adapter.getTypstBlocks() || []
					: []
			const referencedBlockIds = extractCrispyBlockIds(typstCode)
			const typstBlockFieldSource = typstBlocks
				.filter((block: any) => referencedBlockIds.has(String(block?.name || "").trim()))
				.map((block: any) => block?.typst_code || "")
				.join("\n")
			const typstFieldSource = [
				docHeader,
				docFooter,
				typstPreamble,
				typstCode,
				typstBlockFieldSource,
			]
				.filter(Boolean)
				.join("\n")
			extractUsedFieldsFromTypstSource(typstFieldSource).forEach((field) => fields.add(field))
		} else if (layout) {
			extractUsedFields(layout).forEach((field) => fields.add(field))
		}

		const qrSettings = getQrSettings()
		const qrFields = Array.isArray(qrSettings.fields) ? qrSettings.fields : []
		if (
			adapter &&
			typeof adapter.getQrEnabled === "function" &&
			adapter.getQrEnabled() &&
			["custom", "basic"].includes(getEffectiveQrSourceMode())
		) {
			qrFields.forEach((field: any) => {
				const fieldname = String(field || "").trim()
				if (!fieldname) return
				if (fieldname === "timestamp") {
					fields.add("posting_date")
					fields.add("posting_time")
					return
				}
				fields.add(fieldname)
			})
		}

		return Array.from(fields)
	}

	function getBarcodeOptions(qrSettings: Record<string, any> = getQrSettings()) {
		return {
			symbology: qrSettings.symbology || qrSettings.code_symbology || "QR Code",
			error_correction: qrSettings.errorCorrection || qrSettings.error_correction || "Medium",
			quiet_zone: qrSettings.quietZone ?? qrSettings.quiet_zone ?? 1,
			module_size: qrSettings.moduleSize ?? qrSettings.module_size ?? 3,
			width: qrSettings.width ?? null,
			height: qrSettings.height ?? null,
			datamatrix_encodation:
				qrSettings.datamatrixEncodation || qrSettings.datamatrix_encodation || "",
			datamatrix_symbols: qrSettings.datamatrixSymbols || qrSettings.datamatrix_symbols || "",
		}
	}

	function buildQrPayload(doc: Record<string, any> | null, fields: string[]) {
		if (!doc) return ""
		const generatedCode = doc.__crispy_document_code
		if (
			getEffectiveQrSourceMode() === "document_code_profile" &&
			generatedCode &&
			typeof generatedCode === "object" &&
			typeof generatedCode.encoded_value === "string" &&
			generatedCode.encoded_value.trim()
		) {
			return generatedCode.encoded_value.trim()
		}
		if (getEffectiveQrSourceMode() === "custom") {
			return buildCustomQrPayload(doc, fields)
		}
		if (getEffectiveQrSourceMode() !== "basic") return ""
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
			barcodeOptions: getBarcodeOptions(qrSettings),
		}
	}

	function performCompilation() {
		if (disposed) {
			return
		}
		// Allow compile if we already have document data, even if sampleDocSelected wasn't toggled
		if (!sampleDocData) {
			logger.warn("No document data; skipping compile")
			if (statusEl) {
				statusEl.textContent = __("select a document")
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
				statusEl.textContent = __("waiting for layout...")
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
					statusEl.textContent = __("no layout data. Click Refresh to retry")
					statusEl.style.color = "#e74c3c"
				}
			}
			return
		}
		missingLayoutRetries = 0

		// Intentionally skip serialized layout diffing; always compile on trigger.

		let typst: string
		let assetFiles: string[] = []
		let qrPayloadChanged = false
		let qrPayload: ReturnType<typeof resolveQrPayload> | null = null
		try {
			const letterheadCandidate =
				adapter && typeof adapter.getLetterhead === "function" ? adapter.getLetterhead() : null

			// Get page settings to pass to translator
			let presentation_settings: any = {}
			if (adapter && adapter.get_presentation_settings) {
				presentation_settings = adapter.get_presentation_settings() || {}
			}
			const branding_mode = resolveBrandingMode(presentation_settings, letterheadCandidate)
			const letterheadData =
				branding_mode === "letterhead" || branding_mode === "logo_letterhead"
					? letterheadCandidate
					: null

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
			const printBehavior =
				adapter && typeof adapter.getPrintBehavior === "function"
					? adapter.getPrintBehavior() || {}
					: {}
			const typstBlocks =
				adapter && typeof adapter.getTypstBlocks === "function"
					? adapter.getTypstBlocks() || []
					: []
			const referencedBlockIds = rawTypst ? extractCrispyBlockIds(typstCode) : new Set<string>()
			const typstBlockFieldSource = rawTypst
				? typstBlocks
						.filter((block: any) => referencedBlockIds.has(String(block?.name || "").trim()))
						.map((block: any) => block?.typst_code || "")
						.join("\n")
				: ""
			const typstFieldSource = [
				docHeader,
				docFooter,
				typstPreamble,
				typstCode,
				typstBlockFieldSource,
			]
				.filter(Boolean)
				.join("\n")
			const usedFields = rawTypst
				? extractUsedFieldsFromTypstSource(typstFieldSource)
				: layout
					? extractUsedFields(layout)
					: new Set<string>()
			const filteredDoc = rawTypst
				? filterDocumentFields(sampleDocData, usedFields, {
						includeAllChildFieldsIfUnspecified: true,
					})
				: filterDocumentFields(sampleDocData, usedFields)
			const assetCollector = new Set<string>()
			const normalizedDoc = normalizeDocImageAssets(filteredDoc, assetCollector)
			assetFiles = Array.from(assetCollector)
			qrPayload = resolveQrPayload()
			qrEnabled = qrPayload.qrEnabled
			docNameForQr = qrPayload.qrData ? String(qrPayload.qrData) : ""
			qrFilename = qrPayload.qrFilename ? String(qrPayload.qrFilename) : ""
			const qrPayloadKey = qrPayload.qrData ? String(qrPayload.qrData) : ""
			qrPayloadChanged = qrPayloadKey !== lastQrPayload
			lastQrPayload = qrPayloadKey

			// Use filtered document instead of full sampleDocData
			if (rawTypst) {
				const parts: string[] = []
				parts.push(buildDocDictionary(normalizedDoc, printFormatName))
				parts.push(buildRawTypstHelperBlock(typstBlocks, typstCode))
				const rawQrBlock = buildRawQrBlock({
					qrEnabled,
					qrData: docNameForQr,
					qrFilename,
					qrSettings: qrPayload.qrSettings,
				})
				if (rawQrBlock) {
					parts.push(rawQrBlock)
				}
				if (typstCode && typstCode.trim()) {
					parts.push(typstCode.trim())
				}
				typst = parts.join("\n\n")
			} else {
				typst = translateJSONToTypst(layout as any, letterheadData, printFormatName, normalizedDoc, {
					...presentation_settings,
					docHeader,
					docFooter,
					typstPreamble,
					qrEnabled,
					qrData: docNameForQr,
					qrFilename,
					qrSettings: qrPayload.qrSettings,
					printBehavior,
				})
			}
		} catch (e: any) {
			logger.error("Translation error", e)
			const formattedError = parseTypstError(e)
			if (statusEl) {
				statusEl.textContent = __("translation error")
				statusEl.style.color = "#e74c3c"
			}
			dispatchStatus("error", formattedError)
			// Don't show frappe alert - error will be displayed in preview pane
			return
		}

		if (typst === lastTypstCode && !qrPayloadChanged) {
				if (statusEl) {
					statusEl.textContent = __("up to date")
					statusEl.style.color = "#95a5a6"
				}
			return
		}
		if (statusEl) {
			statusEl.textContent = __("compiling…")
			statusEl.style.color = "#f39c12"
		}
		dispatchStatus("compiling")
		if (downloadBtn) downloadBtn.disabled = true
		clearPdfBlob()

		const presentation_settings =
			adapter && typeof adapter.get_presentation_settings === "function"
				? adapter.get_presentation_settings() || {}
				: {}
		const letterheadData =
			adapter && typeof adapter.getLetterhead === "function" ? adapter.getLetterhead() : null
		if (!rawTypst) {
			assetFiles.push(...resolveBrandingImages(presentation_settings, letterheadData))
		}
		assetFiles.push(...extractCrispyImageAssetFiles(typst, getCurrentSiteName()))
		assetFiles = Array.from(new Set(assetFiles))
		lastCompileAssetFiles = assetFiles

		try {
			worker.postMessage({
				typstSrc: typst,
				csrfToken: frappe?.csrf_token,
				outputFormat: previewOutputFormat,
				pdfStandard: adapter.getPdfStandard?.() || null,
				requestId: PREVIEW_REQUEST_ID,
				seq: nextSeq(PREVIEW_REQUEST_ID),
				assetFiles,
				qrData: qrEnabled ? docNameForQr : null,
				qrFilename: qrEnabled ? qrFilename : null,
				barcodeOptions: qrEnabled ? qrPayload?.barcodeOptions || null : null,
			})
			lastTypstCode = typst
		} catch (err) {
			logger.error("Failed to post preview compile", err)
			if (statusEl) {
				statusEl.textContent = __("worker error")
				statusEl.style.color = "#e74c3c"
			}
			dispatchStatus("error", "failed to start preview compile")
		}
	}

	const handleWorkerMessage = async (e: MessageEvent) => {
		if (disposed) {
			return
		}
		const {
			type,
			ok,
			format,
			svgPages,
			pdfBytes,
			error,
			requestId,
			seq,
			tokenRequestId,
			cacheHit,
			renderMs,
			typstVersion,
			pdfStandard,
		} =
			e.data || {}
		if (type === "csrf-token-request") {
			worker.postMessage({
				type: "csrf-token-response",
				tokenRequestId,
				csrfToken: frappe?.csrf_token || "",
			})
			return
		}
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
					statusEl.textContent = isDownload || isViewPdf ? __("pdf error") : __("error")
					statusEl.style.color = "#e74c3c"
				}
				dispatchStatus("error", formattedError)
				// Don't show frappe alert - error will be displayed in preview pane
				if (isDownload && downloadBtn) {
					downloadBtn.disabled = false
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
						statusEl.textContent = __("svg missing")
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
					if (statusEl) {
						statusEl.textContent = __("compiled ✓")
						statusEl.style.color = "#27ae60"
					}
					dispatchCrispyPreviewStatus({
						status: "ready",
						instanceId,
						pageCount: Array.isArray(svgPages) ? svgPages.length : undefined,
						renderMs: typeof renderMs === "number" ? renderMs : null,
						cacheHit: typeof cacheHit === "boolean" ? cacheHit : null,
						typstVersion: typstVersion || null,
						pdfStandard: pdfStandard || null,
					})
				} else {
					logger.warn("SVG response received for download request")
				}

				if (downloadBtn) downloadBtn.disabled = false
				if (viewPdfBtn) viewPdfBtn.disabled = false
				return
			}

			const pdfArray = new Uint8Array(pdfBytes || [])

			if (!pdfArray.length) {
				if (statusEl) {
					statusEl.textContent = __("empty pdf")
					statusEl.style.color = "#e67e22"
				}
				frappe?.show_alert({
					message: __("Typst compilation returned an empty PDF"),
					indicator: "orange",
				})
				if (downloadBtn) downloadBtn.disabled = false
				return
			}

			clearPdfBlob()
			currentPdfBlob = new Blob([pdfArray], { type: "application/pdf" })

			if (requestId === PREVIEW_REQUEST_ID) {
				await adapter.onPreviewPdfReady?.(pdfArray)
				if (statusEl) {
					statusEl.textContent = __("compiled ✓")
					statusEl.style.color = "#27ae60"
				}
				dispatchCrispyPreviewStatus({
					status: "ready",
					instanceId,
					pageCount: e.data?.pageCount,
					renderMs: typeof renderMs === "number" ? renderMs : null,
					cacheHit: typeof cacheHit === "boolean" ? cacheHit : null,
					typstVersion: typstVersion || null,
					pdfStandard: pdfStandard || null,
				})
				if (downloadBtn) downloadBtn.disabled = false
				if (viewPdfBtn) viewPdfBtn.disabled = false
				return
			}

			if (isViewPdf) {
				try {
					await notifyPdfReady("view", currentPdfBlob)
				} catch (err) {
					logger.error("Failed to record issued document snapshot", err)
					frappe?.show_alert({
						message: __("Could not record issued document snapshot."),
						indicator: "red",
					})
					if (statusEl) {
						statusEl.textContent = __("snapshot error")
						statusEl.style.color = "#e74c3c"
					}
					if (viewPdfBtn) viewPdfBtn.disabled = false
					if (downloadBtn) downloadBtn.disabled = false
					return
				}
				openPdfBlob(currentPdfBlob)

				if (statusEl) {
					statusEl.textContent = __("pdf opened ✓")
					statusEl.style.color = "#27ae60"
				}
				if (viewPdfBtn) viewPdfBtn.disabled = false
				if (downloadBtn) downloadBtn.disabled = false
				return
			}

			if (isDownload) {
				try {
					await notifyPdfReady("download", currentPdfBlob)
				} catch (err) {
					logger.error("Failed to record issued document snapshot", err)
					frappe?.show_alert({
						message: __("Could not record issued document snapshot."),
						indicator: "red",
					})
					if (statusEl) {
						statusEl.textContent = __("snapshot error")
						statusEl.style.color = "#e74c3c"
					}
					if (downloadBtn) downloadBtn.disabled = false
					return
				}
				if (statusEl) {
					statusEl.textContent = __("pdf ready ✓")
					statusEl.style.color = "#27ae60"
				}
				if (downloadBtn) downloadBtn.disabled = false
				triggerPdfDownload()
				return
			} else {
				logger.warn("PDF response received for preview request")
				if (statusEl) {
					statusEl.textContent = __("unexpected pdf")
					statusEl.style.color = "#e67e22"
				}
			}
			if (downloadBtn) downloadBtn.disabled = false
			if (viewPdfBtn) viewPdfBtn.disabled = false
			return
		}
	}
	worker.addEventListener("message", handleWorkerMessage)

	viewPdfBtn &&
		(viewPdfBtn.onclick = async () => {
			if (currentPdfBlob) {
				try {
					await notifyPdfReady("view", currentPdfBlob)
				} catch (err) {
					logger.error("Failed to record issued document snapshot", err)
					frappe?.show_alert({
						message: __("Could not record issued document snapshot."),
						indicator: "red",
					})
					return
				}
				openPdfBlob(currentPdfBlob)
				return
			}

			if (!lastTypstCode) {
				frappe?.show_alert({ message: __("Typst code not ready yet"), indicator: "orange" })
				return
			}

			if (statusEl) {
				statusEl.textContent = __("generating pdf…")
				statusEl.style.color = "#3498db"
			}
			viewPdfBtn.disabled = true
			if (downloadBtn) downloadBtn.disabled = true

			const qrPayload = resolveQrPayload()
			try {
				postPdfCompile({
					worker,
					typstSrc: lastTypstCode,
					requestId: VIEW_PDF_REQUEST_ID,
					seq: nextSeq(VIEW_PDF_REQUEST_ID),
					assetFiles: lastCompileAssetFiles,
					qrData: qrPayload.qrData,
					qrFilename: qrPayload.qrFilename,
					barcodeOptions: qrPayload.barcodeOptions,
				})
			} catch (err) {
				logger.error("Failed to post PDF view compile", err)
				if (statusEl) {
					statusEl.textContent = __("pdf error")
					statusEl.style.color = "#e74c3c"
				}
				dispatchStatus("error", "failed to start pdf compile")
				viewPdfBtn.disabled = false
				if (downloadBtn) downloadBtn.disabled = false
			}
		})

	downloadBtn &&
		(downloadBtn.onclick = async () => {
			if (currentPdfBlob) {
				try {
					await notifyPdfReady("download", currentPdfBlob)
				} catch (err) {
					logger.error("Failed to record issued document snapshot", err)
					frappe?.show_alert({
						message: __("Could not record issued document snapshot."),
						indicator: "red",
					})
					return
				}
				triggerPdfDownload()
				return
			}

			if (!lastTypstCode) {
				frappe?.show_alert({ message: __("Typst code not ready yet"), indicator: "orange" })
				return
			}

			if (statusEl) {
				statusEl.textContent = __("generating pdf…")
				statusEl.style.color = "#3498db"
			}
			downloadBtn.disabled = true

			const qrPayload = resolveQrPayload()
			try {
				postPdfCompile({
					worker,
					typstSrc: lastTypstCode,
					requestId: DOWNLOAD_REQUEST_ID,
					seq: nextSeq(DOWNLOAD_REQUEST_ID),
					assetFiles: lastCompileAssetFiles,
					qrData: qrPayload.qrData,
					qrFilename: qrPayload.qrFilename,
					barcodeOptions: qrPayload.barcodeOptions,
				})
			} catch (err) {
				logger.error("Failed to post PDF download compile", err)
				if (statusEl) {
					statusEl.textContent = __("pdf error")
					statusEl.style.color = "#e74c3c"
				}
				dispatchStatus("error", "failed to start pdf compile")
				downloadBtn.disabled = false
			}
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
				statusEl.textContent = __("refreshing...")
				statusEl.style.color = "#3498db"
			}
			lastTypstCode = "" // Force recompilation by clearing cached code
			resetCompilationLatch()
			resetCompiledArtifacts(false)
			scheduleCompile(0)
		})

	viewCodeBtn &&
		(viewCodeBtn.onclick = () => {
			const d = new frappe.ui.Dialog({
				title: __("Typst Code"),
				fields: [
					{
						fieldtype: "Code",
						fieldname: "typst_code",
						label: __("Typst Source"),
						options: "Rust",
						default: lastTypstCode,
					},
				],
				primary_action_label: __("Save to Crispy Format"),
				primary_action: (values: any) => {
					const typstCode = values.typst_code || d.get_value("typst_code")
					if (String(typstCode || "").length > 512 * 1024) {
						frappe.show_alert({
							message: __("Typst code is too large to save"),
							indicator: "red",
						})
						return
					}
					const confirmed =
						typeof window.confirm === "function"
							? window.confirm(__("Save this Typst code to the Crispy Format?"))
							: true
					if (!confirmed) {
						return
					}

					frappe.call({
						method: "frappe.client.set_value",
						args: {
							doctype: "Crispy Format",
							name: printFormatName,
							fieldname: "typst_code",
							value: typstCode,
						},
						callback: (r: any) => {
							if (!r.exc) {
								frappe.show_alert({
									message: __("Typst code saved to Crispy Format"),
									indicator: "green",
								})
								d.hide()
							}
						},
					})
				},
				secondary_action_label: __("Copy to Clipboard"),
				secondary_action: async () => {
					const typstCode = d.get_value("typst_code")
					try {
						await navigator.clipboard.writeText(typstCode)
						frappe.show_alert({
							message: __("Typst code copied to clipboard"),
							indicator: "green",
						})
					} catch (err) {
						logger.warn("Failed to copy Typst code", err)
						frappe.show_alert({
							message: __("Could not copy Typst code"),
							indicator: "red",
						})
					}
				},
			})
			d.show()
		})

	initializeAdapter()

	return () => {
		disposed = true
		if (compilationTimeout) {
			clearTimeout(compilationTimeout)
		}
		if (compileTriggerTimeout) {
			clearTimeout(compileTriggerTimeout)
		}
		if (compilationFrame) {
			cancelAnimationFrame(compilationFrame)
		}
		documentLoadGeneration += 1
		resetCompiledArtifacts(true)
		if (unsubscribeAdapter) {
			unsubscribeAdapter()
		}
		if (unsubscribeDoctype) {
			unsubscribeDoctype()
		}
		window.removeEventListener(CrispyPreviewEvents.SetDoc, handleSetDoc)
		window.removeEventListener(CrispyPreviewEvents.Refresh, handleRefresh)
		window.removeEventListener(CrispyPreviewEvents.RequestSource, handleSourceRequest)
		window.removeEventListener(CrispyPreviewEvents.Source, handleSourceUpdate)
		window.removeEventListener(CrispyPreviewEvents.RequestPdf, handlePdfRequest)
		worker.removeEventListener("error", handleWorkerError)
		worker.removeEventListener("messageerror", handleWorkerMessageError)
		worker.removeEventListener("message", handleWorkerMessage)

		autocomplete.cleanup()

		if (worker) {
			cleanup()
		}
	}
}
