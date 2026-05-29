import { defineComponent, h } from "vue"

export default defineComponent({
	name: "CbpNumberField",
	props: {
		modelValue: {
			type: Number,
			default: 0,
		},
		label: {
			type: String,
			required: true,
		},
		min: {
			type: Number,
			default: undefined,
		},
	},
	emits: ["update:modelValue"],
	setup(props, { emit }) {
		return () =>
			h("label", { class: "cbp-field" }, [
				h("span", props.label),
				h("input", {
					class: "form-control",
					type: "number",
					step: "0.5",
					min: props.min,
					value: props.modelValue,
					onInput: (event: Event) =>
						emit("update:modelValue", Number((event.target as HTMLInputElement).value)),
				}),
			])
	},
})
