export function sanitizeFilename(value: string) {
	return String(value || "")
		.trim()
		.replace(/[\/\\?%*:|"<>]/g, "-")
		.replace(/\s+/g, "-")
}

export function createDocumentLoader(maxEntries = 50) {
	const docCache = new Map<string, Record<string, any>>()

	function cacheKey(doctype: string, docname: string) {
		return `${doctype}::${docname}`
	}

	function fetchDoc(
		doctype: string,
		docname: string,
		opts: { force?: boolean; qrSourceMode?: string } = {}
	): Promise<Record<string, any> | null> {
		const qrSourceMode = String(opts.qrSourceMode || "")
		const key = `${cacheKey(doctype, docname)}::${qrSourceMode}`
		const cached = docCache.get(key)
		if (!opts.force && cached) {
			docCache.delete(key)
			docCache.set(key, cached)
			return Promise.resolve(cached)
		}

		return new Promise((resolve) => {
			if (typeof frappe === "undefined" || typeof frappe.call !== "function") {
				resolve(null)
				return
			}

			frappe.call({
				method: "crispy_print.api.v1.get_formatted_doc",
				args: { doctype, name: docname, qr_source_mode: qrSourceMode || null },
				callback: (r: any) => {
					if (r?.message && typeof r.message === "object") {
						docCache.delete(key)
						docCache.set(key, r.message)
						while (docCache.size > maxEntries) {
							const oldestKey = docCache.keys().next().value
							if (!oldestKey) break
							docCache.delete(oldestKey)
						}
						resolve(r.message)
					} else {
						resolve(null)
					}
				},
				error: () => resolve(null),
			})
		})
	}

	return {
		fetchDoc,
		clear: () => docCache.clear(),
	}
}
