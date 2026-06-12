export const PREVIEW_REQUEST_ID = "preview"
export const DOWNLOAD_REQUEST_ID = "download"
export const VIEW_PDF_REQUEST_ID = "view-pdf"

export type PdfAction = "view" | "download"

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
