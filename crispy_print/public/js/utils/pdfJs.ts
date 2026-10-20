import type * as PdfJsModule from "pdfjs-dist/legacy/build/pdf.mjs";

import { dependencies } from "../package.json";

const version = dependencies["pdfjs-dist"];
export const PDFJS_MODULE_URL = `/assets/crispy_print/vendor/pdfjs/pdf-${version}.min.js`;
export const PDFJS_WORKER_URL = `/assets/crispy_print/vendor/pdfjs/pdf.worker-${version}.min.js`;

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
