import { createApp } from "vue"
import CrispyPP from "./pages/CrispyPP.vue"
import { setupWorker } from "./typst/setupWorker"

if (typeof __VUE_OPTIONS_API__ === "undefined") {
	globalThis.__VUE_OPTIONS_API__ = true
}
if (typeof __VUE_PROD_DEVTOOLS__ === "undefined") {
	globalThis.__VUE_PROD_DEVTOOLS__ = false
}
if (typeof __VUE_PROD_HYDRATION_MISMATCH_DETAILS__ === "undefined") {
	globalThis.__VUE_PROD_HYDRATION_MISMATCH_DETAILS__ = false
}

// Expose setupWorker globally for crispy_print.js
window.setupWorker = setupWorker

window.mountCrispyPreview = (selector = "#crispy-preview-root", props = {}) => {
	const mountPoint = document.querySelector(selector)
	if (!mountPoint) {
		console.warn("[CrispyPreview] Mount point not found:", selector)
		return null
	}

	const app = createApp(CrispyPP, props)
	const mountedComponent = app.mount(selector)

	return {
		app,
		component: mountedComponent,
	}
}
