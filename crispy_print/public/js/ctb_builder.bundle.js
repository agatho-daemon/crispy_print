import { createApp, watch } from "vue";
import CtbBuilder from "./pages/CtbBuilder.vue";

if (typeof __VUE_OPTIONS_API__ === "undefined") {
	globalThis.__VUE_OPTIONS_API__ = true;
}
if (typeof __VUE_PROD_DEVTOOLS__ === "undefined") {
	globalThis.__VUE_PROD_DEVTOOLS__ = false;
}
if (typeof __VUE_PROD_HYDRATION_MISMATCH_DETAILS__ === "undefined") {
	globalThis.__VUE_PROD_HYDRATION_MISMATCH_DETAILS__ = false;
}

window.Vue = window.Vue || {};
window.Vue.watch = watch;

const getLogger = (scope = {}) => {
	const base = window?.CrispyPrintLogger;
	if (base && typeof base.child === "function") {
		return base.child(scope);
	}
	const noop = {
		debug: () => {},
		info: () => {},
		warn: () => {},
		error: () => {},
		child: () => noop,
		setLevel: () => {},
	};
	return noop;
};
const logger = getLogger({ module: "CtbBuilderMount" });

window.mountCtbBuilder = (selector = "#ctb-builder-root", props = {}) => {
	const mountPoint = document.querySelector(selector);
	if (!mountPoint) {
		logger.warn("Mount point not found", { selector });
		return null;
	}

	const app = createApp(CtbBuilder, props);
	const mountedComponent = app.mount(selector);

	return {
		app,
		component: mountedComponent,
	};
};
