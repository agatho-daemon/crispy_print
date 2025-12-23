// Factory for Typst inline worker used across Crispy pages

export interface TypstWorkerHandle {
	worker: Worker
	cleanup: () => void
}

export function createTypstWorker(): TypstWorkerHandle {
	const baseUrl = window.location?.origin || ""
	const workerCode = `
const ENABLE_WORKER_LOGS = false;
const log = (...args) => { if (ENABLE_WORKER_LOGS) console.log('[Typst Worker]', ...args) };
const warn = (...args) => console.warn('[Typst Worker]', ...args);
const BASE_URL = ${JSON.stringify(baseUrl)};

async function compileWithCLI(typstSrc, csrfToken, outputFormat = 'svg', letterheadImage = null) {
  const apiUrl = BASE_URL + '/api/method/crispy_print.api.compile_typst';
  const body = {
    typst_source: typstSrc,
    output_format: outputFormat
  };

  if (letterheadImage) {
    body.letterhead_image = letterheadImage;
  }

  const response = await fetch(apiUrl, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'X-Frappe-CSRF-Token': csrfToken || ''
    },
    credentials: 'include',
    body: JSON.stringify(body)
  });

  if (!response.ok) {
    const text = await response.text();
    throw new Error(\`Server returned \${response.status}: \${text}\`);
  }

  const data = await response.json();
  if (data.exc || data.exception) {
    throw new Error(data.message || data.exc || 'Server compilation failed');
  }

  const payload = data.message || data;
  const format = (payload?.format || outputFormat || 'svg').toLowerCase();

  if (format === 'svg') {
    const pages = payload?.svg_pages;
    if (!Array.isArray(pages) || pages.length === 0) {
      throw new Error('No svg_pages in server response');
    }
    return {
      format: 'svg',
      svgPages: pages,
      pageCount: payload?.page_count || pages.length
    };
  }

  const base64 = payload?.pdf_data;
  if (!base64) {
    throw new Error('No pdf_data in server response');
  }

  const binary = atob(base64);
  const bytes = new Uint8Array(binary.length);
  for (let i = 0; i < binary.length; i++) {
    bytes[i] = binary.charCodeAt(i);
  }
  return {
    format: 'pdf',
    pdfBytes: bytes
  };
}

self.postMessage({ type: 'init', ok: true, wasmReady: false });

self.addEventListener('message', async (event) => {
  const { typstSrc, csrfToken, outputFormat, requestId, letterheadImage, seq } = event.data || {};
  const desiredFormat = (outputFormat || 'svg').toLowerCase();

  if (!typstSrc || !typstSrc.trim()) {
    self.postMessage({
      type: 'compile',
      ok: false,
      error: { message: 'No Typst source provided' },
      requestId,
      seq
    });
    return;
  }

  try {
    log(\`Requesting \${desiredFormat.toUpperCase()} from server CLI...\`);
    if (letterheadImage) {
      log(\`Including letterhead image: \${letterheadImage}\`);
    }
    const result = await compileWithCLI(typstSrc, csrfToken, desiredFormat, letterheadImage);
    const message = {
      type: 'compile',
      ok: true,
      format: result.format,
      requestId,
      seq
    };

    if (result.format === 'svg') {
      message.svgPages = result.svgPages;
      message.pageCount = result.pageCount;
    } else {
      message.pdfBytes = Array.from(result.pdfBytes || []);
    }

    self.postMessage(message);
  } catch (err) {
    warn('Compilation error', err);
    self.postMessage({
      type: 'compile',
      ok: false,
      requestId,
      seq,
      error: {
        message: err?.message || String(err),
        stack: err?.stack || null
      }
    });
  }
});

log('Typst worker loaded (server-side CLI bridge)');
`;

	const blob = new Blob([workerCode], { type: "application/javascript" })
	const workerUrl = URL.createObjectURL(blob)
	const worker = new Worker(workerUrl)

	return {
		worker,
		cleanup: () => {
			try {
				worker.terminate()
			} catch (err) {
				console.warn("[Typst Worker] Failed to terminate worker", err)
			}
			URL.revokeObjectURL(workerUrl)
		},
	}
}
