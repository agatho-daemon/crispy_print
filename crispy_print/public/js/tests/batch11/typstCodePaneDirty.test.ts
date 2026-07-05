import { mount } from "@vue/test-utils"
import { describe, expect, it, vi } from "vitest"
import { ref } from "vue"
import TypstCodePane from "../../components/TypstCodePane.vue"

const typstCode = ref("")
const setTypstCode = vi.fn((value: string) => {
	typstCode.value = value
})

vi.mock("../../composables/useStore", () => ({
	useStore: () => ({
		typstCode,
		setTypstCode,
	}),
}))

describe("TypstCodePane dirty behavior", () => {
	it("marks code dirty without using preview invalidation", async () => {
		typstCode.value = ""
		setTypstCode.mockClear()

		const wrapper = mount(TypstCodePane)
		await wrapper.find("textarea").setValue("#text[changed]")

		expect(typstCode.value).toBe("#text[changed]")
		expect(setTypstCode).toHaveBeenCalledWith("#text[changed]")
	})
})
