// Typed wrappers around common Frappe client-side APIs.
// Keeps app logic testable by centralizing Frappe touchpoints.

export type FrappeCallResponse<T> = {
	message?: T
	exc?: string
	exception?: string
}

function getFrappe(): any {
	return typeof frappe === "undefined" ? null : frappe
}

export function ensureFrappe(): any {
	const f = getFrappe()
	if (!f) {
		throw new Error("Frappe is not available")
	}
	return f
}

export async function call<T = any>(opts: Record<string, any>): Promise<FrappeCallResponse<T>> {
	const f = ensureFrappe()
	return (await f.call(opts)) as FrappeCallResponse<T>
}

export async function getDoc<T = any>(doctype: string, name: string): Promise<T> {
	const f = ensureFrappe()
	return (await f.db.get_doc(doctype, name)) as T
}

export async function getList<T = any>(doctype: string, args: Record<string, any>): Promise<T[]> {
	const f = ensureFrappe()
	return (await f.db.get_list(doctype, args)) as T[]
}

export async function setValue(
	doctype: string,
	name: string,
	values: Record<string, any>
): Promise<void> {
	await call({
		method: "frappe.client.set_value",
		args: {
			doctype,
			name,
			fieldname: values,
		},
	})
}

export async function withDoctype(doctype: string): Promise<void> {
	const f = ensureFrappe()
	await new Promise<void>((resolve) => {
		f.model.with_doctype(doctype, () => resolve())
	})
}

