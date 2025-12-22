// Tiny helpers for parsing Frappe routes used by Crispy pages.

export type FrappeRoute = Array<string | undefined | null>

export function getRouteSafe(): string[] {
	if (typeof frappe === "undefined" || typeof frappe.get_route !== "function") {
		return []
	}
	return (frappe.get_route() || []).map((p: any) => String(p || ""))
}

export function getCrispyBuilderFormatName(route: FrappeRoute = getRouteSafe()): string | null {
	const [page, format] = route
	if (page !== "crispy-print-builder") return null
	return format ? String(format) : null
}

