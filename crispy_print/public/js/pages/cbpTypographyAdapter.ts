import { computed, type WritableComputedRef } from "vue";

import type { CrispyBrandingProfileDoc } from "../api/crispy";
import type { TypographyStyle } from "../utils/presentation_settings";
import { num } from "./cbpBuilderSupport";

export interface CbpTypographySpecimen {
  family: string;
  size_pt: number;
  style: string;
  weight: string;
  color: string;
}

export function cbpTypographySpecimen(
  model: CrispyBrandingProfileDoc,
  prefix: string,
): CbpTypographySpecimen {
  return {
    family: String((model as any)[`${prefix}_font_family`] || "Arial"),
    size_pt: num((model as any)[`${prefix}_font_size_pt`]),
    style: String((model as any)[`${prefix}_font_style`] || "normal"),
    weight: String((model as any)[`${prefix}_font_weight`] || "regular"),
    color: String((model as any)[`${prefix}_font_color`] || "#000000"),
  };
}

export function cbpTypographyStyle(
  model: CrispyBrandingProfileDoc,
  prefix: string,
): TypographyStyle {
  const typography = cbpTypographySpecimen(model, prefix);
  const style = String(typography.style || "normal").toLowerCase();
  return {
    fontFamily: typography.family,
    fontSize: `${typography.size_pt}pt`,
    fontStyle: style === "italic" || style === "oblique" ? style : "normal",
    fontWeight: String(typography.weight || "regular").toLowerCase(),
    color: typography.color,
  };
}

export function cbpTypographyModel(
  model: CrispyBrandingProfileDoc,
  prefix: string,
): WritableComputedRef<TypographyStyle> {
  return computed<TypographyStyle>({
    get: () => cbpTypographyStyle(model, prefix),
    set: (value) => {
      const target = model as any;
      target[`${prefix}_font_family`] = value.fontFamily;
      target[`${prefix}_font_size_pt`] = Number.parseFloat(value.fontSize) || 0;
      target[`${prefix}_font_style`] = value.fontStyle;
      target[`${prefix}_font_weight`] = value.fontWeight;
      target[`${prefix}_font_color`] = value.color;
    },
  });
}
