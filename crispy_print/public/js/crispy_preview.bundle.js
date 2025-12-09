import { createApp } from "vue"
import CrispyPP from "./pages/CrispyPP.vue"
import { setupWorker } from "./typst/setupWorker"

// Expose setupWorker globally for typst_print.js
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
