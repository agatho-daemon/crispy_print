import { mount } from "@vue/test-utils";
import { describe, expect, it } from "vitest";
import ChartPaletteField from "../../pages/cbpFields/ChartPaletteField.vue";

describe("ChartPaletteField", () => {
  it("renders stored colors visually and serializes reordering", async () => {
    const wrapper = mount(ChartPaletteField, {
      props: { modelValue: "#112233, #445566, #778899" },
    });

    expect(wrapper.findAll(".chart-palette-field__color")).toHaveLength(3);
    expect(wrapper.find(".chart-palette-field__preview").exists()).toBe(false);

    await wrapper.findAll(".chart-palette-field__swatch")[1].trigger("click");
    await wrapper
      .findAll(".chart-palette-field__order-actions button")[0]
      .trigger("click");

    expect(wrapper.emitted("update:modelValue")?.slice(-1)[0]?.[0]).toBe(
      "#445566, #112233, #778899",
    );
  });

  it("adds, removes, and resets colors without exposing the storage string", async () => {
    const defaults = ["#AA0000", "#00AA00"];
    const wrapper = mount(ChartPaletteField, {
      props: { modelValue: "#AA0000", defaultPalette: defaults },
    });

    await wrapper.find(".chart-palette-field__add").trigger("click");
    expect(wrapper.emitted("update:modelValue")?.slice(-1)[0]?.[0]).toBe(
      "#AA0000, #00AA00",
    );

    await wrapper.find(".chart-palette-field__remove").trigger("click");
    expect(wrapper.emitted("update:modelValue")?.slice(-1)[0]?.[0]).toBe(
      "#AA0000",
    );

    await wrapper
      .find(".chart-palette-field__label-row button")
      .trigger("click");
    expect(wrapper.emitted("update:modelValue")?.slice(-1)[0]?.[0]).toBe(
      "#AA0000, #00AA00",
    );
  });

  it("rejects invalid hex text without changing the palette", async () => {
    const wrapper = mount(ChartPaletteField, {
      props: { modelValue: "#112233" },
    });
    const input = wrapper.find(
      '.chart-palette-field__color-input input[type="text"]',
    );
    await input.setValue("blue");
    await input.trigger("blur");

    expect(wrapper.text()).toContain("six-digit hex color");
    expect(wrapper.emitted("update:modelValue")).toBeUndefined();
  });
});
