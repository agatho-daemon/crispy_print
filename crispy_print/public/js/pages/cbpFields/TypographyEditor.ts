import { defineComponent, h } from "vue"

import { __ } from "../../utils/i18n"
import { styles, weights } from "../cbpBuilderSupport"
import ColorField from "./ColorField"
import NumberField from "./NumberField"

export default defineComponent({
	name: "CbpTypographyEditor",
	props: {
		title: {
			type: String,
			required: true,
		},
		family: {
			type: String,
			default: "Arial",
		},
		size: {
			type: Number,
			default: 10,
		},
		style: {
			type: String,
			default: "Normal",
		},
		weight: {
			type: String,
			default: "Regular",
		},
		color: {
			type: String,
			default: "#000000",
		},
	},
	emits: ["update:family", "update:size", "update:style", "update:weight", "update:color"],
	setup(props, { emit }) {
		return () =>
			h("div", { class: "cbp-typography" }, [
				h("div", { class: "cbp-subtitle" }, props.title),
				h("div", { class: "cbp-grid cbp-grid--two" }, [
					h("label", { class: "cbp-field" }, [
						h("span", __("Family")),
						h("input", {
							class: "form-control",
							type: "text",
							value: props.family,
							onInput: (event: Event) =>
								emit("update:family", (event.target as HTMLInputElement).value),
						}),
					]),
					h(NumberField, {
						label: __("Size (pt)"),
						modelValue: props.size,
						"onUpdate:modelValue": (value: number) => emit("update:size", value),
					}),
					h("label", { class: "cbp-field" }, [
						h("span", __("Style")),
						h(
							"select",
							{
								class: "form-control",
								value: props.style,
								onChange: (event: Event) =>
									emit("update:style", (event.target as HTMLSelectElement).value),
							},
							styles.map((style) => h("option", { value: style }, style))
						),
					]),
					h("label", { class: "cbp-field" }, [
						h("span", __("Weight")),
						h(
							"select",
							{
								class: "form-control",
								value: props.weight,
								onChange: (event: Event) =>
									emit("update:weight", (event.target as HTMLSelectElement).value),
							},
							weights.map((weight) => h("option", { value: weight }, weight))
						),
					]),
					h(ColorField, {
						label: __("Color"),
						modelValue: props.color,
						"onUpdate:modelValue": (value: string) => emit("update:color", value),
					}),
				]),
			])
	},
})
