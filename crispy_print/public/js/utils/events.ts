// Shared event names + helpers for Crispy Print.
// Keeps page JS and Vue components consistent and testable.

export type CrispyPreviewStatus = "fetching" | "compiling" | "ready" | "error"

export type CrispyPreviewStatusDetail = {
	status: CrispyPreviewStatus
	message?: string
}

export type CrispyPreviewSourceDetail = {
	source: string | null
}

export type CrispyPreviewSetDocDetail = {
	doctype: string
	docname: string
}

export type CrispyPreviewPdfAction = "view" | "download"
export type CrispyPreviewPdfRequestDetail = {
	action: CrispyPreviewPdfAction
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

