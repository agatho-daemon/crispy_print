// Tests for the Shared Utilities & Store audit (US1–US14) fixes.
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

// ───────────────────────────────────────────────────────────────────────────
// US1: typstEscape utility
// ───────────────────────────────────────────────────────────────────────────
describe("US1: escapeTypstString / quoteTypstString", () => {
	it("escapes backslashes before quotes so quotes do not become \\\\\"", async () => {
		const { escapeTypstString } = await import("../../utils/typstEscape")
		// Input ends with a backslash followed by a quote: `\"`
		// Correct order: `\\` → `\\\\`, then `"` → `\\"`, yielding `\\\\\\"`.
		expect(escapeTypstString('a\\"b')).toBe('a\\\\\\"b')
	})

	it("escapes CR / LF / TAB", async () => {
		const { escapeTypstString } = await import("../../utils/typstEscape")
		expect(escapeTypstString("a\nb\rc\td")).toBe("a\\nb\\rc\\td")
	})

	it("strips other ASCII control characters", async () => {
		const { escapeTypstString } = await import("../../utils/typstEscape")
		// \x00 NUL, \x07 BEL, \x1B ESC, \x7F DEL — all should be removed.
		expect(escapeTypstString("a\x00b\x07c\x1Bd\x7Fe")).toBe("abcde")
	})

	it("coerces non-string input safely", async () => {
		const { escapeTypstString, quoteTypstString } = await import(
			"../../utils/typstEscape"
		)
		expect(escapeTypstString(null)).toBe("")
		expect(escapeTypstString(undefined)).toBe("")
		expect(escapeTypstString(42)).toBe("42")
		expect(quoteTypstString("hi")).toBe('"hi"')
	})
})

// ───────────────────────────────────────────────────────────────────────────
// US2: reportBuilder uses the escape utility for font fields
// ───────────────────────────────────────────────────────────────────────────
describe("US2: report builder escapes caller-controlled font values", () => {
	it("escapes malicious font_family so it cannot break out of the string", async () => {
		const {
			buildReportTypstFromConfig,
			getDefaultReportBuilderConfig,
		} = await import("../../utils/reportBuilder")
		const config = getDefaultReportBuilderConfig()
		// Quote + newline + Typst-injection attempt.
		config.font_family = 'Arial"; #panic() //\n'
		const typst = buildReportTypstFromConfig(config)
		// The raw injection sequence must NOT appear unescaped.
		expect(typst).not.toContain('Arial"; #panic()')
		// The escaped form must appear at least once.
		expect(typst).toContain('\\"; #panic() //\\n')
	})
})

// ───────────────────────────────────────────────────────────────────────────
// US5: child-row field iteration uses tableFields, not parent directFields
// ───────────────────────────────────────────────────────────────────────────
describe("US5: filterDocumentFields child-row population", () => {
	it("only copies the child columns referenced in usedFields (not parent fields)", async () => {
		const { filterDocumentFields } = await import(
			"../../utils/layoutFieldExtractor"
		)
		const doc = {
			name: "SI-001",
			customer: "Acme",
			grand_total: 100,
			items: [
				{ item_code: "X", qty: 2, rate: 50, description: "desc", parent: "SI-001" },
			],
		}
		const used = new Set<string>(["customer", "items.item_code", "items.qty"])
		const out = filterDocumentFields(doc, used)
		// Parent fields: customer included, grand_total excluded.
		expect(out.customer).toBe("Acme")
		expect(out.grand_total).toBeUndefined()
		// Child row: only the two referenced columns + essential fields.
		expect(out.items[0].item_code).toBe("X")
		expect(out.items[0].qty).toBe(2)
		expect(out.items[0].rate).toBeUndefined()
		expect(out.items[0].description).toBeUndefined()
		// Previously, `customer` would have leaked into the child row.
		expect("customer" in out.items[0]).toBe(false)
		// Essential child fields preserved.
		expect(out.items[0].parent).toBe("SI-001")
	})

	it("includes all child fields when no child columns specified and the flag is on", async () => {
		const { filterDocumentFields } = await import(
			"../../utils/layoutFieldExtractor"
		)
		const doc = { items: [{ a: 1, b: 2, c: 3 }] }
		const used = new Set<string>(["items"])
		const out = filterDocumentFields(doc, used, {
			includeAllChildFieldsIfUnspecified: true,
		})
		expect(out.items[0]).toMatchObject({ a: 1, b: 2, c: 3 })
	})
})

// ───────────────────────────────────────────────────────────────────────────
// US6: letterheadCache LRU eviction
// ───────────────────────────────────────────────────────────────────────────
const letterheadFetchSpy = vi.fn(async (name: string) => ({ name, image: `/files/${name}.png` }))

vi.mock("../../api/crispy", () => ({
	getLetterheadDoc: (name: string) => letterheadFetchSpy(name),
	getLetterheads: async () => [],
	getCrispyFormat: async () => ({ name: "Test", doc_type: "X", layout_json: "{}", presentation_settings: "{}" }),
	getCrispyFormatsForDoctype: async () => [],
	getDefaultCrispyFormatForDoctype: async () => null,
	getApplicableTypstBlocks: async () => [],
	saveCrispyFormat: async () => {},
}))

describe("US6: letterhead cache is LRU-bounded", () => {
	beforeEach(() => {
		letterheadFetchSpy.mockClear()
	})

	it("evicts the oldest entry when exceeding capacity (20)", async () => {
		const { loadLetterheadDoc, clearLetterheadCache } = await import(
			"../../utils/formatLoader"
		)
		clearLetterheadCache()

		// Fill cache with 20 entries — all should be cached.
		for (let i = 0; i < 20; i++) {
			await loadLetterheadDoc(`LH-${i}`)
		}
		expect(letterheadFetchSpy).toHaveBeenCalledTimes(20)

		// Hitting an existing one should NOT trigger another fetch.
		await loadLetterheadDoc("LH-5")
		expect(letterheadFetchSpy).toHaveBeenCalledTimes(20)

		// Add a 21st entry → evicts the oldest (LH-0, since LH-5 was just refreshed).
		await loadLetterheadDoc("LH-20")
		expect(letterheadFetchSpy).toHaveBeenCalledTimes(21)

		// LH-0 was evicted → re-loading triggers another fetch.
		await loadLetterheadDoc("LH-0")
		expect(letterheadFetchSpy).toHaveBeenCalledTimes(22)

		// LH-5 was kept (refreshed before the eviction).
		await loadLetterheadDoc("LH-5")
		expect(letterheadFetchSpy).toHaveBeenCalledTimes(22)
	})
})

// ───────────────────────────────────────────────────────────────────────────
// US10: normalizeLayout size caps & font_size_pt clamp
// ───────────────────────────────────────────────────────────────────────────
describe("US10: defensive caps", () => {
	it("clamps font_size_pt to [4, 96] in normalizeReportBuilderConfig", async () => {
		const { normalizeReportBuilderConfig } = await import(
			"../../utils/reportBuilder"
		)
		expect(normalizeReportBuilderConfig({ font_size_pt: 0 }).font_size_pt).toBe(4)
		expect(normalizeReportBuilderConfig({ font_size_pt: 3 }).font_size_pt).toBe(4)
		expect(normalizeReportBuilderConfig({ font_size_pt: 9 }).font_size_pt).toBe(9)
		expect(normalizeReportBuilderConfig({ font_size_pt: 200 }).font_size_pt).toBe(96)
	})

	it("caps section / column / field / table_columns counts in normalizeLayout", async () => {
		const { normalizeLayout } = await import("../../utils/layout")

		// 250 sections → expect 200.
		const manySections = {
			sections: Array.from({ length: 250 }, (_, i) => ({
				id: `s${i}`,
				label: "",
				columns: [],
			})),
		}
		expect(normalizeLayout(manySections as any).sections.length).toBe(200)

		// 60 columns in a section → expect 50.
		const manyColumns = {
			sections: [
				{
					id: "s",
					label: "",
					columns: Array.from({ length: 60 }, (_, i) => ({
						id: `c${i}`,
						label: "",
						fields: [],
					})),
				},
			],
		}
		expect(normalizeLayout(manyColumns as any).sections[0].columns.length).toBe(50)

		// 600 fields in a column → expect 500.
		const manyFields = {
			sections: [
				{
					id: "s",
					label: "",
					columns: [
						{
							id: "c",
							label: "",
							fields: Array.from({ length: 600 }, (_, i) => ({
								id: `f${i}`,
								fieldname: `f${i}`,
								fieldtype: "Data",
								label: "",
							})),
						},
					],
				},
			],
		}
		expect(
			normalizeLayout(manyFields as any).sections[0].columns[0].fields.length
		).toBe(500)

		// 250 table_columns on a Table field → expect 200.
		const manyTableCols = {
			sections: [
				{
					id: "s",
					label: "",
					columns: [
						{
							id: "c",
							label: "",
							fields: [
								{
									id: "f",
									fieldname: "items",
									fieldtype: "Table",
									label: "Items",
									table_columns: Array.from({ length: 250 }, (_, i) => ({
										fieldname: `col${i}`,
										label: `Col ${i}`,
									})),
								},
							],
						},
					],
				},
			],
		}
		const normalized = normalizeLayout(manyTableCols as any)
		expect(
			(normalized.sections[0].columns[0].fields[0] as any).table_columns.length
		).toBe(200)
	})
})

// ───────────────────────────────────────────────────────────────────────────
// US3 + US7 + US4 + US8 + US14: store behavior
// ───────────────────────────────────────────────────────────────────────────
vi.mock("../../api/frappe", () => ({
	withDoctype: async () => {},
}))

describe("US3 + US7 + US4 + US8 + US14: useStore behavior", () => {
	beforeEach(() => {
		vi.resetModules()
		;(globalThis as any).__ = (msg: string): string => msg
		;(globalThis as any).frappe = {
			call: vi.fn(async () => ({ message: {} })),
			get_meta: vi.fn(() => ({ fields: [] as unknown[] })),
			show_alert: vi.fn(),
			throw: vi.fn((m: string) => {
				throw new Error(m)
			}),
		}
		vi.useFakeTimers()
	})

	afterEach(() => {
		vi.useRealTimers()
	})

	it("US3+US7: throttles history snapshots; bursts collapse to leading + trailing", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		// Ensure history starts clean.
		store.resetHistory(true)
		const startPast = store.historyPast.value.length

		// First mutation is captured immediately (leading edge).
		store.layout.value = { sections: [{ id: "a", label: "A", columns: [] }] } as any
		store.markDirty()
		expect(store.historyPast.value.length).toBe(startPast + 1)

		// Subsequent rapid mutations within the cooldown window do NOT each
		// create a checkpoint — they coalesce into one trailing capture.
		store.layout.value = { sections: [{ id: "b", label: "B", columns: [] }] } as any
		store.markDirty()
		store.layout.value = { sections: [{ id: "c", label: "C", columns: [] }] } as any
		store.markDirty()
		// No new entry yet — trailing capture is still pending.
		expect(store.historyPast.value.length).toBe(startPast + 1)
		// canUndo must already reflect the pending trailing capture so the UI
		// enables the Undo button immediately.
		expect(store.canUndo.value).toBe(true)

		// Advance past the cooldown — exactly ONE trailing capture is added
		// (snapshot of the final state), not two.
		vi.advanceTimersByTime(300)
		expect(store.historyPast.value.length).toBe(startPast + 2)
	})

	it("US3+US7: undo flushes pending checkpoint before walking history", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		store.layout.value = { sections: [] } as any
		store.resetHistory(true)

		// Leading-edge capture for the first mutation.
		store.layout.value = {
			sections: [{ id: "s1", label: "x", columns: [] }],
		} as any
		store.markDirty()
		// Second mutation in the same cooldown window — trailing capture pending.
		store.layout.value = {
			sections: [
				{ id: "s1", label: "x", columns: [] },
				{ id: "s2", label: "y", columns: [] },
			],
		} as any
		store.markDirty()

		// Trailing capture has NOT fired yet, but undo() must flush it so the
		// most recent state is on the history stack before walking back.
		expect(store.canUndo.value).toBe(true)
		store.undo()
		// After undo, we should be back at the leading-edge snapshot (1 section),
		// not the empty starting state — proving the trailing was flushed first.
		expect(store.layout.value?.sections.length).toBe(1)
	})

	it("US14: assigning reportBuilderConfig into presentation_settings.report is shallow-copied", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()
		// Trigger the watch by mutating reportBuilderConfig.
		store.reportBuilderConfig.value.font_family = "Times New Roman"
		// Flush the deep watcher.
		await Promise.resolve()
		await Promise.resolve()

		// presentation_settings.value.report must be a distinct object reference.
		expect(store.presentation_settings.value.report).not.toBe(
			store.reportBuilderConfig.value,
		)
		// But the values are equal.
		expect(store.presentation_settings.value.report?.font_family).toBe(
			"Times New Roman",
		)
	})

	it("US4+US8: reset() clears per-format state", async () => {
		const { useStore } = await import("../../composables/useStore")
		const store = useStore()

		store.layout.value = {
			sections: [{ id: "s", label: "x", columns: [] }],
		} as any
		store.markDirty()
		vi.advanceTimersByTime(300) // flush debounce
		expect(store.dirty.value).toBe(true)

		store.reset()

		expect(store.layout.value).toBeNull()
		expect(store.crispyFormat.value).toBeNull()
		expect(store.fields.value).toEqual([])
		expect(store.historyPast.value).toEqual([])
		expect(store.historyFuture.value).toEqual([])
		expect(store.dirty.value).toBe(false)
	})
})

// ───────────────────────────────────────────────────────────────────────────
// US9: parseSize reports invalid input
// ───────────────────────────────────────────────────────────────────────────
describe("US9: parseSize reports invalid input via `valid`", () => {
	it("returns valid:false for non-matching input", async () => {
		const { parseSize } = await import("../../utils/typstTypography")
		expect(parseSize("not a size").valid).toBe(false)
		expect(parseSize("").valid).toBe(false)
	})

	it("returns valid:true for well-formed input", async () => {
		const { parseSize } = await import("../../utils/typstTypography")
		expect(parseSize("12pt").valid).toBe(true)
		expect(parseSize("1.5em").valid).toBe(true)
	})
})
