export const PREVIEW_REQUEST_ID = "preview"
export const DOWNLOAD_REQUEST_ID = "download"
export const VIEW_PDF_REQUEST_ID = "view-pdf"

export type PdfAction = "view" | "download" | "print"

export type PrintPdfBlobOptions = {
	onPrint?: () => void
	onError?: (error: unknown) => void
}

export function openPdfBlob(blob: Blob) {
	const url = URL.createObjectURL(blob)
	window.open(url, "_blank", "noopener,noreferrer")
	setTimeout(() => URL.revokeObjectURL(url), 1000)
}

export function downloadPdfBlob(blob: Blob, filename: string) {
	const url = URL.createObjectURL(blob)
	const link = document.createElement("a")
	link.href = url
	link.download = filename
	link.style.display = "none"
	document.body.appendChild(link)
	link.click()
	setTimeout(() => {
		link.remove()
		URL.revokeObjectURL(url)
	}, 1000)
}

export function printPdfBlob(blob: Blob, options: PrintPdfBlobOptions = {}): boolean {
	const url = URL.createObjectURL(blob)
	const printWindow = window.open(url, "_blank")
	if (!printWindow) {
		URL.revokeObjectURL(url)
		return false
	}

	let cleanedUp = false
	const cleanup = () => {
		if (cleanedUp) return
		cleanedUp = true
		URL.revokeObjectURL(url)
	}
	let printRequested = false
	const requestPrint = () => {
		if (printRequested) return
		printRequested = true
		try {
			printWindow.addEventListener("afterprint", cleanup, { once: true })
			printWindow.focus()
			printWindow.print()
			options.onPrint?.()
		} catch (error) {
			cleanup()
			options.onError?.(error)
		}
	}

	printWindow.addEventListener("load", requestPrint, { once: true })
	// Chrome's built-in PDF viewer can finish loading before its top-level
	// load listener is attached.
	window.setTimeout(requestPrint, 1000)
	window.setTimeout(cleanup, 60_000)
	return true
}

export function postPdfCompile(options: {
	worker: Worker
	typstSrc: string
	pdfStandard?: string | null
	requestId: string
	seq: number
	assetFiles: string[]
	qrData?: string | null
	qrFilename?: string | null
	barcodeOptions?: Record<string, any> | null
}) {
	options.worker.postMessage({
		typstSrc: options.typstSrc,
		csrfToken: frappe?.csrf_token,
		outputFormat: "pdf",
		pdfStandard: options.pdfStandard || null,
		requestId: options.requestId,
		seq: options.seq,
		assetFiles: options.assetFiles,
		qrData: options.qrData || null,
		qrFilename: options.qrFilename || null,
		barcodeOptions: options.barcodeOptions || null,
	})
}
