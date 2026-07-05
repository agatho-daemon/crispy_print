// Shared presentation settings model and helpers.

import { deepClone } from "./json";
import {
  getDefaultReportBuilderConfig,
  normalizeReportBuilderConfig,
  type ReportBuilderConfig,
} from "./reportBuilder";

export interface TypographyStyle {
  fontFamily: string;
  fontSize: string;
  fontStyle: string;
  fontWeight: string;
  color: string;
}

export interface TypographySettings {
  fieldLabel: TypographyStyle;
  fieldValue: TypographyStyle;
  sectionLabel: TypographyStyle;
}

export interface TableTypographySettings {
  header: TypographyStyle;
  body: TypographyStyle;
}

export interface TableCellLabelSettings {
  enabled: boolean;
  fontSize: string;
  fontWeight: string;
  baselineShift: number;
  color: string;
}

export interface QrSettings {
  dx: number;
  dy: number;
  size: number;
  fields: string[];
  enabled?: boolean;
  sourceMode?: "" | "basic" | "document_code_profile";
  symbology?: "QR Code" | "DataMatrix";
  errorCorrection?: "Low" | "Medium" | "Quartile" | "High";
  quietZone?: number;
  moduleSize?: number;
  width?: number;
  height?: number;
  datamatrixEncodation?: string;
  datamatrixSymbols?: string;
}

export interface LogoSettings {
  company: string;
  image: string;
  size: number;
  dx: number;
  dy: number;
}

export interface TableSettings {
  inset: {
    top: number;
    right: number;
    bottom: number;
    left: number;
  };
  stroke: {
    width: number;
    color: string;
  };
  header: {
    backgroundColor: string;
  };
  stripe: {
    enabled: boolean;
    color: string;
  };
  cellLabel: TableCellLabelSettings;
  typography: TableTypographySettings;
}

export interface PagePresentationSettings {
  size: string;
  orientation: string;
  margins: {
    top: number;
    bottom: number;
    left: number;
    right: number;
  };
}

export interface BrandingPresentationSettings {
  profile?: string;
  company?: string;
  mode: "letterhead" | "logo" | "logo_letterhead" | "none";
  letterhead: string;
  letterhead_image?: string;
  letterheadData?: any;
  logo: LogoSettings;
}

export interface PresentationSettings {
  source: "" | "custom" | "branding_profile";
  page: PagePresentationSettings;
  branding: BrandingPresentationSettings;
  language: string;
  typography?: TypographySettings;
  table?: TableSettings;
  qr?: QrSettings;
  report?: ReportBuilderConfig;
}

export const defaultTypography: TypographySettings = {
  fieldLabel: {
    fontFamily: "Inter",
    fontSize: "8pt",
    fontStyle: "normal",
    fontWeight: "semibold",
    color: "#64748b",
  },
  fieldValue: {
    fontFamily: "Inter",
    fontSize: "10pt",
    fontStyle: "normal",
    fontWeight: "regular",
    color: "#0f172a",
  },
  sectionLabel: {
    fontFamily: "Inter",
    fontSize: "14pt",
    fontStyle: "normal",
    fontWeight: "bold",
    color: "#1e293b",
  },
};

export const defaultTableTypography: TableTypographySettings = {
  header: {
    fontFamily: "Inter",
    fontSize: "9pt",
    fontStyle: "normal",
    fontWeight: "semibold",
    color: "#0f172a",
  },
  body: {
    fontFamily: "Inter",
    fontSize: "9pt",
    fontStyle: "normal",
    fontWeight: "regular",
    color: "#0f172a",
  },
};

export const defaultTableSettings: TableSettings = {
  inset: { top: 2, right: 2, bottom: 2, left: 2 },
  stroke: { width: 0.5, color: "#e2e8f0" },
  header: { backgroundColor: "#f1f5f9" },
  stripe: { enabled: false, color: "#f8fafc" },
  cellLabel: {
    enabled: true,
    fontSize: "8pt",
    fontWeight: "regular",
    baselineShift: -2,
    color: "#475569",
  },
  typography: defaultTableTypography,
};

export const default_presentation_settings: PresentationSettings = {
  source: "",
  page: {
    size: "A4",
    orientation: "portrait",
    margins: { top: 25, bottom: 20, left: 20, right: 20 },
  },
  branding: {
    profile: "",
    company: "",
    mode: "letterhead",
    letterhead: "",
    letterhead_image: "",
    logo: { company: "", image: "", size: 25, dx: 0, dy: 0 },
  },
  typography: undefined,
  table: undefined,
  language: "en",
  qr: {
    dx: 0,
    dy: 0,
    size: 15,
    fields: [],
    enabled: false,
    sourceMode: "",
    symbology: "QR Code",
    errorCorrection: "Medium",
    quietZone: 1,
    moduleSize: 3,
  },
  report: getDefaultReportBuilderConfig(),
};

function ensure_presentation_shape(settings: any): PresentationSettings {
  if (!settings.page || !settings.branding) {
    const normalized = merge_presentation_settings(
      default_presentation_settings,
      settings || {},
    );
    Object.assign(settings, normalized);
  }
  return settings as PresentationSettings;
}

export function ensure_typography(
  settings: PresentationSettings,
): TypographySettings {
  settings = ensure_presentation_shape(settings);
  if (!settings.typography) {
    settings.typography = deepClone(defaultTypography);
    return settings.typography;
  }
  settings.typography = {
    fieldLabel: {
      ...defaultTypography.fieldLabel,
      ...(settings.typography.fieldLabel || {}),
    },
    fieldValue: {
      ...defaultTypography.fieldValue,
      ...(settings.typography.fieldValue || {}),
    },
    sectionLabel: {
      ...defaultTypography.sectionLabel,
      ...(settings.typography.sectionLabel || {}),
    },
  };
  return settings.typography;
}

export function ensure_table_settings(
  settings: PresentationSettings,
): TableSettings {
  settings = ensure_presentation_shape(settings);
  if (!settings.table) {
    settings.table = deepClone(defaultTableSettings);
    return settings.table;
  }
  settings.table.inset = {
    ...defaultTableSettings.inset,
    ...(settings.table.inset || {}),
  };
  settings.table.stroke = {
    ...defaultTableSettings.stroke,
    ...(settings.table.stroke || {}),
  };
  settings.table.header = {
    ...defaultTableSettings.header,
    ...(settings.table.header || {}),
  };
  settings.table.stripe = {
    ...defaultTableSettings.stripe,
    ...(settings.table.stripe || {}),
  };
  settings.table.cellLabel = {
    ...defaultTableSettings.cellLabel,
    ...(settings.table.cellLabel || {}),
  };
  settings.table.typography = {
    header: {
      ...defaultTableTypography.header,
      ...(settings.table.typography?.header || {}),
    },
    body: {
      ...defaultTableTypography.body,
      ...(settings.table.typography?.body || {}),
    },
  };
  return settings.table;
}

export function ensure_qr_settings(settings: PresentationSettings): QrSettings {
  settings = ensure_presentation_shape(settings);
  if (!settings.qr) {
    settings.qr = {
      dx: 0,
      dy: 0,
      size: 15,
      fields: [],
      enabled: false,
      sourceMode: "",
    };
  }
  if (!Array.isArray(settings.qr.fields)) {
    settings.qr.fields = [];
  }
  if (typeof settings.qr.enabled !== "boolean") {
    settings.qr.enabled = false;
  }
  if (typeof settings.qr.sourceMode !== "string") {
    settings.qr.sourceMode = "";
  }
  if (!settings.qr.symbology) {
    settings.qr.symbology = "QR Code";
  }
  if (!settings.qr.errorCorrection) {
    settings.qr.errorCorrection = "Medium";
  }
  if (typeof settings.qr.quietZone !== "number") {
    settings.qr.quietZone = 1;
  }
  if (typeof settings.qr.moduleSize !== "number") {
    settings.qr.moduleSize = 3;
  }
  return settings.qr;
}

export function ensure_logo_settings(
  settings: PresentationSettings,
): LogoSettings {
  settings = ensure_presentation_shape(settings);
  if (!settings.branding) {
    settings.branding = deepClone(default_presentation_settings.branding);
  }
  if (!settings.branding.logo) {
    settings.branding.logo = { company: "", image: "", size: 25, dx: 0, dy: 0 };
  }
  settings.branding.logo.company = settings.branding.logo.company || "";
  settings.branding.logo.image = settings.branding.logo.image || "";
  settings.branding.logo.size = Number.isFinite(settings.branding.logo.size)
    ? settings.branding.logo.size
    : 25;
  settings.branding.logo.dx = Number.isFinite(settings.branding.logo.dx)
    ? settings.branding.logo.dx
    : 0;
  settings.branding.logo.dy = Number.isFinite(settings.branding.logo.dy)
    ? settings.branding.logo.dy
    : 0;
  return settings.branding.logo;
}

export function merge_presentation_settings(
  base: PresentationSettings = default_presentation_settings,
  overrides: Partial<PresentationSettings> = {},
): PresentationSettings {
  const {
    fontFamily: _ignoredFontFamily,
    fontSize: _ignoredFontSize,
    ...safeOverrides
  } = overrides as any;

  const merged: PresentationSettings = {
    ...base,
    ...safeOverrides,
    source: safeOverrides.source ?? base.source,
    page: {
      ...base.page,
      ...(safeOverrides.page || {}),
      margins: {
        ...base.page.margins,
        ...(safeOverrides.page?.margins || {}),
      },
    },
    branding: {
      ...base.branding,
      ...(safeOverrides.branding || {}),
      logo: {
        ...base.branding.logo,
        ...(safeOverrides.branding?.logo || {}),
      },
    },
    typography: safeOverrides.typography ?? base.typography,
    table: {
      ...(base.table || defaultTableSettings),
      ...(safeOverrides.table || {}),
      inset: {
        ...(base.table?.inset || defaultTableSettings.inset),
        ...(safeOverrides.table?.inset || {}),
      },
      stroke: {
        ...(base.table?.stroke || defaultTableSettings.stroke),
        ...(safeOverrides.table?.stroke || {}),
      },
      header: {
        ...(base.table?.header || defaultTableSettings.header),
        ...(safeOverrides.table?.header || {}),
      },
      stripe: {
        ...(base.table?.stripe || defaultTableSettings.stripe),
        ...(safeOverrides.table?.stripe || {}),
      },
      cellLabel: {
        ...(base.table?.cellLabel || defaultTableSettings.cellLabel),
        ...(safeOverrides.table?.cellLabel || {}),
      },
      typography: {
        header: {
          ...(base.table?.typography?.header || defaultTableTypography.header),
          ...(safeOverrides.table?.typography?.header || {}),
        },
        body: {
          ...(base.table?.typography?.body || defaultTableTypography.body),
          ...(safeOverrides.table?.typography?.body || {}),
        },
      },
    },
    qr: {
      ...(base.qr || { dx: 0, dy: 0, size: 15, fields: [] }),
      ...(safeOverrides.qr || {}),
      sourceMode:
        safeOverrides.qr?.sourceMode === undefined ||
        safeOverrides.qr?.sourceMode === ""
          ? base.qr?.sourceMode || ""
          : safeOverrides.qr?.sourceMode,
    },
    report: normalizeReportBuilderConfig(
      safeOverrides.report || base.report || {},
      safeOverrides.generic_report_type || (base as any)?.generic_report_type,
    ),
  };

  return merged;
}
