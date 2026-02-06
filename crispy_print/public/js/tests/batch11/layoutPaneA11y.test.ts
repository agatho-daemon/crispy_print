import { mount } from "@vue/test-utils"
import { describe, expect, it, beforeEach, vi } from "vitest"
import { defineComponent, h, nextTick, ref } from "vue"
import LayoutPane from "../../components/LayoutPane.vue"

const DraggableStub = defineComponent({
	name: "DraggableStub",
	props: {
		modelValue: {
			type: Array,
			default: () => [],
		},
	},
	setup(props, { slots }) {
		return () =>
			h(
				"div",
				{ class: "draggable-stub" },
				(props.modelValue || []).map((element, index) =>
					slots.item ? slots.item({ element, index }) : null
				)
			)
	},
})

vi.mock("../../composables/useStore", () => {
	const layout = ref({
		sections: [
			{
				id: "section-1",
				label: "Section",
				columns: [
					{
						id: "col-1",
						label: "",
						fields: [
							{
								id: "field-1",
								fieldname: "customer",
								label: "Customer",
								fieldtype: "Data",
							},
						],
					},
				],
			},
		],
	})

	return {
		useStore: () => ({
			layout,
			meta: ref({}),
			getDefaultLayout: vi.fn(),
			markDirty: vi.fn(),
		}),
	}
})

describe("LayoutPane accessibility", () => {
	beforeEach(() => {
		;(globalThis as any).frappe = { msgprint: vi.fn() }
	})

	it("opens section menu and supports keyboard navigation", async () => {
		const wrapper = mount(LayoutPane, {
			attachTo: document.body,
			global: {
				stubs: {
					draggable: DraggableStub,
					TableColumnsDialog: true,
				},
			},
		})

		const menuBtn = wrapper.find(".section-card__menu-btn")
		expect(menuBtn.exists()).toBe(true)

		await menuBtn.trigger("click")
		await nextTick()
		await nextTick()

		const menu = document.querySelector(".section-card__menu") as HTMLElement | null
		expect(menu).toBeTruthy()
		expect(menu?.getAttribute("role")).toBe("menu")

		const firstItem = document.activeElement as HTMLElement | null
		expect(firstItem?.textContent || "").toContain("Add section above")

		menu?.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowDown" }))
		await nextTick()
		const nextItem = document.activeElement as HTMLElement | null
		expect(nextItem?.textContent || "").toContain("Add section below")

		menu?.dispatchEvent(new KeyboardEvent("keydown", { key: "Escape" }))
		await nextTick()
		expect(document.querySelector(".section-card__menu")).toBeNull()
		wrapper.unmount()
	})

	it("opens field menu and alignment submenu via keyboard", async () => {
		const wrapper = mount(LayoutPane, {
			attachTo: document.body,
			global: {
				stubs: {
					draggable: DraggableStub,
					TableColumnsDialog: true,
				},
			},
		})

		const fieldMenuBtn = wrapper.find(".field-card__menu-btn")
		expect(fieldMenuBtn.exists()).toBe(true)

		await fieldMenuBtn.trigger("click")
		await nextTick()
		await nextTick()

		const menu = document.querySelector(".field-card__menu") as HTMLElement | null
		expect(menu).toBeTruthy()
		expect(menu?.getAttribute("role")).toBe("menu")

		menu?.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight" }))
		await nextTick()

		const submenu = document.querySelector(".field-card__submenu") as HTMLElement | null
		expect(submenu).toBeTruthy()
		expect(submenu?.getAttribute("role")).toBe("menu")

		const focused = document.activeElement as HTMLElement | null
		expect(focused?.textContent || "").toContain("Left")
		wrapper.unmount()
	})
})
