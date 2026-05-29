import { defineComponent, h } from "vue"

export default defineComponent({
	name: "CbpColorField",
	props: {
		modelValue: {
			type: String,
			default: "#000000",
		},
		label: {
			type: String,
			required: true,
		},
	},
	emits: ["update:modelValue"],
	setup(props, { emit }) {
		const update = (event: Event) =>
			emit("update:modelValue", (event.target as HTMLInputElement).value)

		return () =>
			h("label", { class: "cbp-field cbp-field--color" }, [
				h("span", props.label),
				h("div", { class: "cbp-color-input" }, [
					h("input", {
						type: "color",
						value: props.modelValue || "#000000",
						onInput: update,
					}),
					h("input", {
						class: "form-control",
						type: "text",
						value: props.modelValue,
						onInput: update,
					}),
				]),
			])
	},
})
