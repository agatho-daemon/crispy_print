// Factory for Typst inline worker used across Crispy pages

import { getLogger } from "../logger"

const logger = getLogger({ module: "TypstWorker" })

export interface TypstWorkerHandle {
	worker: Worker
	cleanup: () => void
}

const STATIC_WORKER_PATH = "/assets/crispy_print/js/typst/typstCliWorker.js"

export function createTypstWorker(): TypstWorkerHandle {
	const baseUrl = window.location?.origin || ""
	const bootSiteUrl = (window as any).frappe?.boot?.site_url
	if (bootSiteUrl) {
		try {
			const expectedOrigin = new URL(bootSiteUrl, window.location.href).origin
			if (expectedOrigin && baseUrl && expectedOrigin !== baseUrl) {
				logger.warn("Typst worker origin differs from Frappe site URL", {
					workerOrigin: baseUrl,
					siteOrigin: expectedOrigin,
				})
			}
		} catch (err) {
			logger.warn("Unable to validate Typst worker origin", err)
		}
	}
	const worker = new Worker(STATIC_WORKER_PATH)

	return {
		worker,
		cleanup: () => {
			try {
				worker.terminate()
			} catch (err) {
				logger.warn("Failed to terminate worker", err)
			}
		},
	}
}
