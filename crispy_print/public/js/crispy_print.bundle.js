import { createApp, watch } from "vue"
import CrispyPFB from "./pages/CrispyPFB.vue"
import { useStore } from "./composables/useStore"
// import "../css/crispy_print.bundle.css"

// Make Vue watch available to page JS
window.Vue = window.Vue || {}
window.Vue.watch = watch

window.mountCrispyPrint = (selector = "#crispy-print-root") => {
	const mountPoint = document.querySelector(selector)
	if (!mountPoint) {
		console.warn("[CrispyPrint] Mount point not found:", selector)
		return null
	}

	const app = createApp(CrispyPFB)
	const mountedComponent = app.mount(selector)

	// Get store instance
	const store = useStore()

	// Return both app and store for toolbar integration
	return {
		app,
		component: mountedComponent,
		store,
	}
}