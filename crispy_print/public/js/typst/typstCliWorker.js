const ENABLE_WORKER_LOGS = false;
const FETCH_TIMEOUT_MS = 45000;
let csrfTokenRequestSeq = 0;
const pendingCsrfTokenRequests = new Map();

const emit = (level, ...args) => {
	if (!ENABLE_WORKER_LOGS) return;
	const c = self && self.console;
	if (c && typeof c[level] === "function") {
		c[level]("[Typst Worker]", ...args);
	}
};
const log = (...args) => emit("log", ...args);
const warn = (...args) => emit("warn", ...args);

function requestFreshCsrfToken() {
	const tokenRequestId = ++csrfTokenRequestSeq;
	return new Promise((resolve) => {
		const timeoutId = setTimeout(() => {
			pendingCsrfTokenRequests.delete(tokenRequestId);
			resolve("");
		}, 1000);
		pendingCsrfTokenRequests.set(tokenRequestId, (token) => {
			clearTimeout(timeoutId);
			resolve(token || "");
		});
		self.postMessage({ type: "csrf-token-request", tokenRequestId });
	});
}

async function postCompileRequest(apiUrl, body, csrfToken) {
	const controller = new AbortController();
	const timeoutId = setTimeout(() => controller.abort(), FETCH_TIMEOUT_MS);
	try {
		return await fetch(apiUrl, {
			method: "POST",
			headers: {
				"Content-Type": "application/json",
				"X-Frappe-CSRF-Token": csrfToken || "",
			},
			credentials: "include",
			body: JSON.stringify(body),
			signal: controller.signal,
		});
	} finally {
		clearTimeout(timeoutId);
	}
}

// Frappe v1 serializes _server_messages as an array of JSON strings.
function applicationMessage(data) {
	let entries = data?._server_messages;
	try {
		if (typeof entries === "string") entries = JSON.parse(entries);
	} catch {
		entries = [];
	}
	const candidates = [];
	for (let entry of Array.isArray(entries) ? entries : []) {
		try {
			if (typeof entry === "string") entry = JSON.parse(entry);
			if (typeof entry?.message === "string") candidates.push(entry.message);
		} catch {
			// Ignore malformed message entries and continue to other messages.
		}
	}
	candidates.push(data?._error_message, data?.message);
	for (const candidate of candidates) {
		if (typeof candidate !== "string") continue;
		const text = candidate.trim();
		if (!text || text.length > 2000 || /Traceback|File ".+", line \d|\n\s*at /i.test(text)) continue;
		return text;
	}
	// `exception` can expose internals. Only use known compile messages.
	const exception = data?.exception;
	if (typeof exception === "string") {
		const known = exception.match(/^(?:frappe\.exceptions\.)?ValidationError: (Typst compilation failed\. Check the server error log for details\.|Compilation timed out\. The document may be too complex\.)$/);
		if (known) return known[1];
	}
	return "";
}

function compileResponseError(kind, status, message) {
	return Object.assign(new Error(message), { kind, status });
}

async function readCompileResponse(response) {
	const text = await response.text();
	let data;
	try {
		data = JSON.parse(text);
	} catch {
		// HTML and malformed JSON are not compiler diagnostics.
	}
	const isObject = data && typeof data === "object" && !Array.isArray(data);
	if (!response.ok || (isObject && (data.exc || data.exception || data.exc_type))) {
		const message = isObject ? applicationMessage(data) : "";
		if (message) throw compileResponseError("application", response.status, message);
		throw compileResponseError("request", response.status, "The server request failed without a usable application error.");
	}
	if (!isObject) {
		throw compileResponseError("response", response.status, "The server returned an invalid compilation response.");
	}
	return data;
}

async function compileWithCLI(
	typstSrc,
	csrfToken,
	outputFormat = "svg",
	pdfStandard = null,
	assetFiles = null,
	qrData = null,
	qrFilename = null,
	barcodeOptions = null
) {
	const apiUrl = self.location.origin + "/api/method/crispy_print.api.v1.compile_typst";
	if (!csrfToken) {
		warn("Missing CSRF token for compile request");
	}
	const body = {
		typst_source: typstSrc,
		output_format: outputFormat,
	};
	if (pdfStandard) {
		body.pdf_standard = pdfStandard;
	}

	if (Array.isArray(assetFiles) && assetFiles.length) {
		body.asset_files = assetFiles;
	}
	if (qrData && qrFilename) {
		body.qr_data = qrData;
		body.qr_filename = qrFilename;
	}
	if (barcodeOptions) {
		body.barcode_options = barcodeOptions;
	}

	let response = await postCompileRequest(apiUrl, body, csrfToken);
	if (response.status === 403) {
		const refreshedToken = await requestFreshCsrfToken();
		if (refreshedToken && refreshedToken !== csrfToken) {
			response = await postCompileRequest(apiUrl, body, refreshedToken);
		}
	}

	const data = await readCompileResponse(response);

	const payload = data.message || data;
	const format = payload?.format;
	if (payload?.success !== true || !["svg", "pdf"].includes(format) || format !== outputFormat) {
		throw compileResponseError("response", response.status, "The server returned an invalid compilation response.");
	}

	if (format === "svg") {
		const pages = payload?.svg_pages;
		if (!Array.isArray(pages) || pages.length === 0 || pages.some((page) => typeof page !== "string" || !page.trim())) {
			throw compileResponseError("response", response.status, "The server returned an invalid compilation response.");
		}
		return {
			format: "svg",
			svgPages: pages,
			pageCount: payload?.page_count || pages.length,
			cacheHit: payload?.cache_hit,
			renderMs: payload?.render_ms,
			typstVersion: payload?.typst_version,
			pdfStandard: payload?.pdf_standard,
		};
	}

	const base64 = payload?.pdf_data;
	if (typeof base64 !== "string" || !base64) {
		throw compileResponseError("response", response.status, "The server returned an invalid compilation response.");
	}

	let binary;
	try {
		binary = atob(base64);
	} catch {
		throw compileResponseError("response", response.status, "The server returned an invalid compilation response.");
	}
	const bytes = new Uint8Array(binary.length);
	for (let i = 0; i < binary.length; i++) {
		bytes[i] = binary.charCodeAt(i);
	}
	return {
		format: "pdf",
		pdfBytes: bytes,
		cacheHit: payload?.cache_hit,
		renderMs: payload?.render_ms,
		typstVersion: payload?.typst_version,
		pdfStandard: payload?.pdf_standard,
	};
}

self.postMessage({ type: "init", ok: true, wasmReady: false });

self.addEventListener("message", async (event) => {
	if (event.data?.type === "csrf-token-response") {
		const resolver = pendingCsrfTokenRequests.get(event.data.tokenRequestId);
		if (resolver) {
			pendingCsrfTokenRequests.delete(event.data.tokenRequestId);
			resolver(event.data.csrfToken || "");
		}
		return;
	}

	const {
		typstSrc,
		csrfToken,
		outputFormat,
		pdfStandard,
		requestId,
		assetFiles,
		qrData,
		qrFilename,
		barcodeOptions,
		seq,
	} = event.data || {};
	const desiredFormat = (outputFormat || "svg").toLowerCase();

	if (!typstSrc || !typstSrc.trim()) {
		self.postMessage({
			type: "compile",
			ok: false,
			error: { message: "No Typst source provided" },
			requestId,
			seq,
		});
		return;
	}

	try {
		log(`Requesting ${desiredFormat.toUpperCase()} from server CLI...`);
		if (Array.isArray(assetFiles) && assetFiles.length) {
			log(`Including extra asset files: ${assetFiles.length}`);
		}
		const result = await compileWithCLI(
			typstSrc,
			csrfToken,
			desiredFormat,
			pdfStandard,
			assetFiles,
			qrData,
			qrFilename,
			barcodeOptions
		);
		const message = {
			type: "compile",
			ok: true,
			format: result.format,
			requestId,
			seq,
			cacheHit: result.cacheHit,
			renderMs: result.renderMs,
			typstVersion: result.typstVersion,
			pdfStandard: result.pdfStandard,
		};

		if (result.format === "svg") {
			message.svgPages = result.svgPages;
			message.pageCount = result.pageCount;
		} else {
			message.pdfBytes = (result.pdfBytes || new Uint8Array()).buffer;
			message.pageCount = result.pageCount;
		}

		if (message.pdfBytes instanceof ArrayBuffer) {
			self.postMessage(message, [message.pdfBytes]);
		} else {
			self.postMessage(message);
		}
	} catch (err) {
		warn("Compilation error", err);
		self.postMessage({
			type: "compile",
			ok: false,
			requestId,
			seq,
			error: {
				message: err?.message || String(err),
				kind: err?.kind || "request",
				status: err?.status || 0,
			},
		});
	}
});

log("Typst worker loaded (server-side CLI bridge)");
