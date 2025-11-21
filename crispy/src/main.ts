import { createApp } from "vue"
import CrispyPFB from "@/pages/CrispyPFB.vue"
import "./index.css"

// Export mount function for Frappe integration
declare global {
	interface Window {
		mountCrispyPrint: (selector?: string) => any
	}
}

window.mountCrispyPrint = (selector = "#crispy-print-root") => {
	const mountPoint = document.querySelector(selector)
	if (!mountPoint) {
		console.warn("[CrispyPrint] Mount point not found:", selector)
		return null
	}

	const app = createApp(CrispyPFB)
	app.mount(selector)

	return app
}

// Auto-mount in dev mode (standalone)
if (import.meta.env.DEV) {
    document.addEventListener("DOMContentLoaded", () => {
        window.mountCrispyPrint()
    })
}