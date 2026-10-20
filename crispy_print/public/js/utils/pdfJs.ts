import type * as PdfJsModule from "pdfjs-dist/legacy/build/pdf.mjs";

const PDFJS_MODULE_URL = "/assets/crispy_print/vendor/pdfjs/pdf-6.1.200.min.js";
const PDFJS_WORKER_URL = "/assets/crispy_print/vendor/pdfjs/pdf.worker-6.1.200.min.js";

let modulePromise: Promise<typeof PdfJsModule> | null = null;

export function loadPdfJs(): Promise<typeof PdfJsModule> {
	if (!modulePromise) {
		modulePromise = import(/* @vite-ignore */ PDFJS_MODULE_URL).then((pdfjs) => {
			pdfjs.GlobalWorkerOptions.workerSrc = PDFJS_WORKER_URL;
			return pdfjs as typeof PdfJsModule;
		}).catch(() => {
			modulePromise = null;
			throw new Error(__("The PDF viewer could not be loaded. Check that its JavaScript assets are available and served with a JavaScript content type."));
		});
	}
	return modulePromise;
}
