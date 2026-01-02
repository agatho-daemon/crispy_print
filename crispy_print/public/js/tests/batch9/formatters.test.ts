import { describe, expect, it, vi } from "vitest"
import { applyFrappeFormattingToDoc } from "../../utils/formatters"

describe("applyFrappeFormattingToDoc", () => {
	it("formats numeric fields and strips html", () => {
		const layout = {
			sections: [
				{
					label: "Main",
					columns: [
						{
							label: "",
							fields: [
								{ fieldname: "total", fieldtype: "Currency", label: "Total" },
								{
									fieldname: "notes",
									fieldtype: "Data",
									label: "Notes",
								},
							],
						},
					],
				},
			],
		}

		const env = {
			format: vi.fn((value: any) => `<span>${value}</span>`),
			getDocfield: vi.fn((_doctype: string, fieldname: string) => {
				return { fieldtype: fieldname === "total" ? "Currency" : "Data" }
			}),
		}

		const fullDoc = { total: 100, notes: "Keep" }
		const filteredDoc = { ...fullDoc }

		applyFrappeFormattingToDoc({
			layout: layout as any,
			doctype: "Invoice",
			fullDoc,
			filteredDoc,
			env: env as any,
		})

		expect(filteredDoc.total).toBe("100")
		expect(filteredDoc.notes).toBe("Keep")
	})

	it("formats table column values", () => {
		const layout = {
			sections: [
				{
					label: "Table",
					columns: [
						{
							label: "",
							fields: [
								{
									fieldname: "items",
									fieldtype: "Table",
									label: "Items",
									table_columns: [{ fieldname: "qty", label: "Qty", fieldtype: "Int" }],
								},
							],
						},
					],
				},
			],
		}

		const env = {
			format: vi.fn((value: any) => `<span>${value}</span>`),
			getDocfield: vi.fn((doctype: string, fieldname: string) => {
				if (doctype === "Item" && fieldname === "qty") {
					return { fieldtype: "Int" }
				}
				if (doctype === "Invoice" && fieldname === "items") {
					return { fieldtype: "Table", options: "Item" }
				}
				return { fieldtype: "Data" }
			}),
		}

		const fullDoc = { items: [{ qty: 2 }, { qty: 3 }] }
		const filteredDoc = { items: [{ qty: 2 }, { qty: 3 }] }

		applyFrappeFormattingToDoc({
			layout: layout as any,
			doctype: "Invoice",
			fullDoc,
			filteredDoc,
			env: env as any,
		})

		expect(filteredDoc.items[0].qty).toBe("2")
		expect(filteredDoc.items[1].qty).toBe("3")
	})
})
