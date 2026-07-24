// Shared event names + helpers for Crispy Print.

export type CrispyPreviewStatus =
	| "idle"
	| "fetching"
	| "running-report"
	| "compiling"
	| "loading-pdf"
	| "rendering"
	| "ready"
	| "error"

export type CrispyPreviewStatusDetail = {
	status: CrispyPreviewStatus
	message?: string
	instanceId?: string
	pageCount?: number
	renderMs?: number | null
	cacheHit?: boolean | null
	typstVersion?: string | null
	pdfStandard?: string | null
}

export type CrispyPreviewSourceDetail = {
	source: string | null
	instanceId?: string
}

export type CrispyPreviewSetDocDetail = {
	doctype: string
	docname: string
	instanceId?: string
}

export type CrispyPreviewPdfAction = "view" | "download" | "print"
export type CrispyPreviewPdfRequestDetail = {
	action: CrispyPreviewPdfAction
	instanceId?: string
}

export const CrispyPreviewEvents = {
	Status: "crispy-preview:status",
	SetDoc: "crispy-preview:set-doc",
	Refresh: "crispy-preview:refresh",
	RequestSource: "crispy-preview:request-source",
	Source: "crispy-preview:source",
	RequestPdf: "crispy-preview:request-pdf",
} as const

export function dispatchCrispyPreviewStatus(detail: CrispyPreviewStatusDetail) {
	window.dispatchEvent(new CustomEvent(CrispyPreviewEvents.Status, { detail }))
}

export function dispatchCrispyPreviewSource(detail: CrispyPreviewSourceDetail) {
	window.dispatchEvent(new CustomEvent(CrispyPreviewEvents.Source, { detail }))
}
