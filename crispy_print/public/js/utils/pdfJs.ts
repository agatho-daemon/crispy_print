import type * as PdfJsModule from "pdfjs-dist/legacy/build/pdf.mjs";

const PDFJS_MODULE_URL = "/assets/crispy_print/vendor/pdfjs/pdf.min.mjs";
const PDFJS_WORKER_URL = "/assets/crispy_print/vendor/pdfjs/pdf.worker.min.mjs";

let modulePromise: Promise<typeof PdfJsModule> | null = null;

export function loadPdfJs(): Promise<typeof PdfJsModule> {
	if (!modulePromise) {
		modulePromise = import(/* @vite-ignore */ PDFJS_MODULE_URL).then((pdfjs) => {
			pdfjs.GlobalWorkerOptions.workerSrc = PDFJS_WORKER_URL;
			return pdfjs as typeof PdfJsModule;
		});
	}
	return modulePromise;
}
