import { quoteTypstString } from "../utils/typstEscape";
import { getLanguageDirection } from "../utils/direction";

export type BrandingMode = "letterhead" | "logo" | "logo_letterhead" | "none";

export function resolveBrandingMode(
  presentation_settings?: Record<string, any> | null,
  letterheadData?: Record<string, any> | null,
): BrandingMode {
  const branding = presentation_settings?.branding || {};
  const raw = String(branding.mode || "").toLowerCase();
  if (
    raw === "letterhead" ||
    raw === "logo" ||
    raw === "logo_letterhead" ||
    raw === "none"
  ) {
    return raw;
  }
  if (branding.logo?.image || branding.logo?.company) {
    return "logo";
  }
  if (letterheadData && (letterheadData as any).image) {
    return "letterhead";
  }
  if (branding.letterhead) {
    return "letterhead";
  }
  return "none";
}

export function resolveBrandingImage(
  presentation_settings?: Record<string, any> | null,
  letterheadData?: Record<string, any> | null,
): string | null {
  const mode = resolveBrandingMode(presentation_settings, letterheadData);
  if (mode === "logo" || mode === "logo_letterhead") {
    const image = presentation_settings?.branding?.logo?.image;
    return image ? String(image) : null;
  }
  if (mode === "letterhead") {
    const image =
      (letterheadData as any)?.image ||
      presentation_settings?.branding?.letterhead_image;
    return image ? String(image) : null;
  }
  return null;
}

export function resolveBrandingImages(
  presentation_settings?: Record<string, any> | null,
  letterheadData?: Record<string, any> | null,
): string[] {
  const mode = resolveBrandingMode(presentation_settings, letterheadData);
  const images: string[] = [];
  if (mode === "letterhead" || mode === "logo_letterhead") {
    const image =
      (letterheadData as any)?.image ||
      presentation_settings?.branding?.letterhead_image;
    if (image) images.push(String(image));
  }
  if (mode === "logo" || mode === "logo_letterhead") {
    const image = presentation_settings?.branding?.logo?.image;
    if (image) images.push(String(image));
  }
  return images;
}

export function getLetterheadFilename(
  presentation_settings?: Record<string, any> | null,
  letterheadData?: Record<string, any> | null,
): string {
  const mode = resolveBrandingMode(presentation_settings, letterheadData);
  if (mode !== "letterhead" && mode !== "logo_letterhead") return "";
  const image =
    (letterheadData as any)?.image ||
    presentation_settings?.branding?.letterhead_image;
  if (!image) return "";
  return String(image).split("/").pop() || "";
}

export function buildForegroundPlacements(options: {
  presentation_settings?: Record<string, any> | null;
  branding_mode?: BrandingMode;
  qrEnabled?: boolean;
  qrData?: string | null;
  qrFilename?: string | null;
  qrSettings?: Record<string, any> | null;
}): string[] {
  const branding_mode =
    options.branding_mode ||
    resolveBrandingMode(options.presentation_settings || null, null);
  const presentation_settings = options.presentation_settings || {};
  const lines: string[] = [];
  const direction = getLanguageDirection(
    presentation_settings.language || "en",
  ).direction;
  const resolveAnchor = (value: unknown): "left" | "right" => {
    const anchor = String(value || "left");
    if (anchor === "right") return "right";
    if (anchor === "start") return direction === "rtl" ? "right" : "left";
    if (anchor === "end") return direction === "rtl" ? "left" : "right";
    return "left";
  };

  if (branding_mode === "logo" || branding_mode === "logo_letterhead") {
    const logo_settings = presentation_settings.branding?.logo || {};
    const logoImage = String(logo_settings.image || "");
    const logoFilename = logoImage ? logoImage.split("/").pop() : "";
    const logoSize = Number(logo_settings.size) || 25;
    const logoDx = Number(logo_settings.dx) || 0;
    const logoDy = Number(logo_settings.dy) || 0;
    const logoAnchor = resolveAnchor(logo_settings.anchor);
    if (logoFilename) {
      lines.push(
        `#place(top + ${logoAnchor}, dx: ${logoDx}mm, dy: ${logoDy}mm, image("${logoFilename}", width: ${logoSize}mm))`,
      );
    }
  }

  const qrSettings = options.qrSettings || {};
  const qrSize = Number(qrSettings.size) || 15;
  const qrDx = Number(qrSettings.dx) || 0;
  const qrDy = Number(qrSettings.dy) || 0;
  const qrAnchor = resolveAnchor(qrSettings.anchor);
  const qrData = String(options.qrData || "");
  if (options.qrEnabled && qrData) {
    const symbology = String(
      qrSettings.symbology || qrSettings.code_symbology || "QR Code",
    );
    const quietZone = Number(
      qrSettings.quietZone ?? qrSettings.quiet_zone ?? 1,
    );
    const moduleSize = Number(
      qrSettings.moduleSize ?? qrSettings.module_size ?? 3,
    );
    const zebraOptions =
      symbology === "DataMatrix"
        ? buildDataMatrixOptions(qrSettings)
        : buildQrOptions(qrSettings);
    const helper =
      symbology === "DataMatrix" ? "crispy-datamatrix" : "crispy-qrcode";
    lines.push(
      `#{
  import "@local/crispy-print:0.1.0": ${helper}
  place(bottom + ${qrAnchor}, dx: ${qrDx}mm, dy: ${qrDy}mm, ${helper}(${quoteTypstString(qrData)}, options: ${zebraOptions}, quiet-zone: ${quietZone}, module-size: ${moduleSize}pt, width: ${qrSize}mm))
}`,
    );
  } else if (options.qrEnabled && options.qrFilename) {
    lines.push(
      `#place(bottom + ${qrAnchor}, dx: ${qrDx}mm, dy: ${qrDy}mm, image("${options.qrFilename}", width: ${qrSize}mm))`,
    );
  }

  return lines;
}

function buildQrOptions(qrSettings: Record<string, any>): string {
  const ec = qrErrorCorrection(
    qrSettings.errorCorrection || qrSettings.error_correction || "Medium",
  );
  return `(ec-level: "${ec}")`;
}

function buildDataMatrixOptions(qrSettings: Record<string, any>): string {
  const entries: string[] = [];
  const encodation = String(
    qrSettings.datamatrixEncodation || qrSettings.datamatrix_encodation || "",
  ).trim();
  const symbols = String(
    qrSettings.datamatrixSymbols || qrSettings.datamatrix_symbols || "",
  ).trim();
  if (encodation) entries.push(`encodation-type: "${encodation}"`);
  if (symbols) entries.push(`symbols: "${symbols}"`);
  return entries.length ? `(${entries.join(", ")})` : `(:)`;
}

function qrErrorCorrection(value: unknown): string {
  const raw = String(value || "Medium")
    .trim()
    .toLowerCase();
  return (
    (
      {
        low: "l",
        l: "l",
        medium: "m",
        m: "m",
        quartile: "q",
        q: "q",
        high: "h",
        h: "h",
      } as Record<string, string>
    )[raw] || "m"
  );
}
