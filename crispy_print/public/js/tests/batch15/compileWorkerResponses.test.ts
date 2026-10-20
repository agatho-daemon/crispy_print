import { describe, expect, it, vi } from "vitest"
import { readFileSync } from "node:fs"
import { fileURLToPath } from "node:url"
import { dirname, resolve } from "node:path"
import { runInNewContext } from "node:vm"

const source = readFileSync(resolve(dirname(fileURLToPath(import.meta.url)), "../../typst/typstCliWorker.js"), "utf8")
const compileMessage = { type: "compile", typstSrc: "Hello", csrfToken: "old", outputFormat: "svg", requestId: "test", seq: 1 }

async function run(responses: Array<{ status: number; body: unknown; raw?: boolean }>, outputFormat = "svg") {
	let handler: any
	const messages: any[] = []
	const fetch = vi.fn(async (_url: string, _options: any) => {
		const response = responses.shift()!
		return {
			status: response.status,
			ok: response.status >= 200 && response.status < 300,
			text: async () => response.raw ? response.body : JSON.stringify(response.body),
		}
	})
	const self = {
		location: { origin: "https://fdev16.local" },
		addEventListener: (_type: string, callback: any) => { handler = callback },
		postMessage: (message: any) => {
			messages.push(message)
			if (message.type === "csrf-token-request") {
				queueMicrotask(() => handler({ data: { type: "csrf-token-response", tokenRequestId: message.tokenRequestId, csrfToken: "fresh" } }))
			}
		},
	}
	runInNewContext(source, { self, fetch, AbortController, setTimeout, clearTimeout, Uint8Array, ArrayBuffer, atob })
	await handler({ data: { ...compileMessage, outputFormat } })
	return { result: messages.find((m) => m.type === "compile"), fetch }
}

const valid = { message: { success: true, format: "svg", svg_pages: ["<svg/>"], page_count: 1 } }

describe("compile worker response handling", () => {
	it("keeps the useful message from a real Frappe 417 response and discards developer details", async () => {
		const { result } = await run([{ status: 417, body: {
			exc_type: "ValidationError", exc: '["Traceback secret-path"]', exception: "ValidationError: internal details",
			_server_messages: JSON.stringify([JSON.stringify({ message: "Typst compilation failed. Check the server error log for details." })]),
		} }])
		expect(result.ok).toBe(false)
		expect(result.error.kind).toBe("application")
		expect(result.error.message).toBe("Typst compilation failed. Check the server error log for details.")
		expect(JSON.stringify(result)).not.toMatch(/Traceback|secret-path|internal details|stack/)
	})

	it.each([413, 500, 502, 503, 504])("classifies HTTP %s without showing the HTML body", async (status) => {
		const { result } = await run([{ status, body: "<html>private proxy details</html>", raw: true }])
		expect(result.error).toMatchObject({ kind: "request", status })
		expect(JSON.stringify(result)).not.toContain("private proxy details")
	})

	it.each(["not JSON", "<html>login page</html>", "null", "[]", "{}", '{"message":{}}', '{"message":{"success":true,"format":"svg","svg_pages":[]}}'])
	("rejects an invalid HTTP 200 response: %s", async (body) => {
		const { result } = await run([{ status: 200, body, raw: true }])
		expect(result.error.kind).toBe("response")
		expect(result.error.message).toBe("The server returned an invalid compilation response.")
	})

	it("ignores malformed nested messages and unsafe exception fallbacks", async () => {
		const { result } = await run([{ status: 500, body: { _server_messages: '["broken"]', exception: "DatabaseError: secret", exc: "Traceback" } }])
		expect(result.error.kind).toBe("request")
		expect(JSON.stringify(result)).not.toMatch(/secret|Traceback/)
	})

	it("accepts JSON messages even when there is no error status", async () => {
		const { result } = await run([{ status: 200, body: { exc_type: "ValidationError", _server_messages: JSON.stringify([{ message: "Please select a format." }]) } }])
		expect(result.error).toMatchObject({ kind: "application", message: "Please select a format." })
	})

	it("retains the 403 token refresh and retries once with the fresh token", async () => {
		const { result, fetch } = await run([{ status: 403, body: {} }, { status: 200, body: valid }])
		expect(fetch).toHaveBeenCalledTimes(2)
		expect(fetch.mock.calls[1][1].headers["X-Frappe-CSRF-Token"]).toBe("fresh")
		expect(result.ok).toBe(true)
		expect(result.svgPages).toEqual(["<svg/>"])
	})

	it("surfaces the second 403 without an unlimited retry", async () => {
		const { result, fetch } = await run([{ status: 403, body: {} }, { status: 403, body: {} }])
		expect(fetch).toHaveBeenCalledTimes(2)
		expect(result.error).toMatchObject({ kind: "request", status: 403 })
	})
})


describe("PDF compile response validation", () => {
	it("transfers decoded PDF bytes on success", async () => {
		const { result } = await run([{ status: 200, body: { message: { success: true, format: "pdf", pdf_data: btoa("%PDF-1.7 test") } } }], "pdf")
		expect(result.ok).toBe(true)
		expect(result.format).toBe("pdf")
		expect(Array.from(new Uint8Array(result.pdfBytes))).toEqual(Array.from(new TextEncoder().encode("%PDF-1.7 test")))
	})

	it.each([null, "", "%%%"])("rejects missing or malformed PDF data: %s", async (pdf_data) => {
		const { result } = await run([{ status: 200, body: { message: { success: true, format: "pdf", pdf_data } } }], "pdf")
		expect(result.error.kind).toBe("response")
		expect(result.error.message).toBe("The server returned an invalid compilation response.")
	})
})
