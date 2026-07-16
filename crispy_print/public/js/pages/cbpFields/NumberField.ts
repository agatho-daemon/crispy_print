import { defineComponent, h } from "vue";

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
    max: {
      type: Number,
      default: undefined,
    },
    step: {
      type: Number,
      default: 0.5,
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
          step: props.step,
          min: props.min,
          max: props.max,
          value: props.modelValue,
          onInput: (event: Event) =>
            emit(
              "update:modelValue",
              Number((event.target as HTMLInputElement).value),
            ),
        }),
      ]);
  },
});
