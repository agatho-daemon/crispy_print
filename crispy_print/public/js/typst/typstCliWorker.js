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

async function compileWithCLI(
	typstSrc,
	csrfToken,
	outputFormat = "svg",
	pdfStandard = null,
	assetFiles = null,
	qrData = null,
	qrFilename = null
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

	let response = await postCompileRequest(apiUrl, body, csrfToken);
	if (response.status === 403) {
		const refreshedToken = await requestFreshCsrfToken();
		if (refreshedToken && refreshedToken !== csrfToken) {
			response = await postCompileRequest(apiUrl, body, refreshedToken);
		}
	}

	if (!response.ok) {
		const text = await response.text();
		throw new Error(`Server returned ${response.status}: ${text}`);
	}

	const data = await response.json();
	if (data.exc || data.exception) {
		throw new Error(data.message || data.exc || "Server compilation failed");
	}

	const payload = data.message || data;
	const format = (payload?.format || outputFormat || "svg").toLowerCase();

	if (format === "svg") {
		const pages = payload?.svg_pages;
		if (!Array.isArray(pages) || pages.length === 0) {
			throw new Error("No svg_pages in server response");
		}
		return {
			format: "svg",
			svgPages: pages,
			pageCount: payload?.page_count || pages.length,
		};
	}

	const base64 = payload?.pdf_data;
	if (!base64) {
		throw new Error("No pdf_data in server response");
	}

	const binary = atob(base64);
	const bytes = new Uint8Array(binary.length);
	for (let i = 0; i < binary.length; i++) {
		bytes[i] = binary.charCodeAt(i);
	}
	return {
		format: "pdf",
		pdfBytes: bytes,
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
			qrFilename
		);
		const message = {
			type: "compile",
			ok: true,
			format: result.format,
			requestId,
			seq,
		};

		if (result.format === "svg") {
			message.svgPages = result.svgPages;
			message.pageCount = result.pageCount;
		} else {
			message.pdfBytes = Array.from(result.pdfBytes || []);
		}

		self.postMessage(message);
	} catch (err) {
		warn("Compilation error", err);
		self.postMessage({
			type: "compile",
			ok: false,
			requestId,
			seq,
			error: {
				message: err?.message || String(err),
				stack: err?.stack || null,
			},
		});
	}
});

log("Typst worker loaded (server-side CLI bridge)");
