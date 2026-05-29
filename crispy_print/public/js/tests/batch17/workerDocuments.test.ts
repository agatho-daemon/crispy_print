import { afterEach, describe, expect, it, vi } from "vitest";
import { createDocumentLoader } from "../../typst/workerDocuments";

function installFrappeDocResponder(docs: Record<string, Record<string, any>>) {
	const call = vi.fn((opts: any) => {
		const name = opts.args.name;
		opts.callback({ message: docs[name] || null });
	});
	(globalThis as any).frappe = { call };
	return call;
}

describe("createDocumentLoader", () => {
	afterEach(() => {
		delete (globalThis as any).frappe;
	});

	it("uses cached documents unless forced", async () => {
		const call = installFrappeDocResponder({
			"INV-1": { name: "INV-1", value: 1 },
		});
		const loader = createDocumentLoader(2);

		await expect(loader.fetchDoc("Sales Invoice", "INV-1")).resolves.toMatchObject({
			name: "INV-1",
		});
		await expect(loader.fetchDoc("Sales Invoice", "INV-1")).resolves.toMatchObject({
			name: "INV-1",
		});
		await expect(loader.fetchDoc("Sales Invoice", "INV-1", { force: true })).resolves.toMatchObject({
			name: "INV-1",
		});

		expect(call).toHaveBeenCalledTimes(2);
	});

	it("evicts least recently used entries after the cache cap", async () => {
		const call = installFrappeDocResponder({
			A: { name: "A" },
			B: { name: "B" },
			C: { name: "C" },
		});
		const loader = createDocumentLoader(2);

		await loader.fetchDoc("DocType", "A");
		await loader.fetchDoc("DocType", "B");
		await loader.fetchDoc("DocType", "A");
		await loader.fetchDoc("DocType", "C");
		await loader.fetchDoc("DocType", "B");

		expect(call.mock.calls.map((callArgs) => callArgs[0].args.name)).toEqual([
			"A",
			"B",
			"C",
			"B",
		]);
	});

	it("separates cache entries by qr source mode", async () => {
		const call = installFrappeDocResponder({
			"INV-1": { name: "INV-1" },
		});
		const loader = createDocumentLoader(2);

		await loader.fetchDoc("Sales Invoice", "INV-1", { qrSourceMode: "basic" });
		await loader.fetchDoc("Sales Invoice", "INV-1", { qrSourceMode: "basic" });
		await loader.fetchDoc("Sales Invoice", "INV-1", { qrSourceMode: "document_code_profile" });

		expect(call).toHaveBeenCalledTimes(2);
		expect(call.mock.calls[0][0].args.qr_source_mode).toBe("basic");
		expect(call.mock.calls[1][0].args.qr_source_mode).toBe("document_code_profile");
	});
});
