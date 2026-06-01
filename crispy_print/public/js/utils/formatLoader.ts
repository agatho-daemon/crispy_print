// utils/formatLoader.ts
// Modular utilities for loading and managing Crispy Format data

import {
  default_presentation_settings,
  merge_presentation_settings,
  type PresentationSettings,
} from "./presentation_settings";
import { deserializeLayout, type CrispyLayout } from "./layout";
import { safeJsonParse } from "./json";
import {
  getCrispyFormat,
  getCrispyFormatsForDoctype,
  getDefaultCrispyFormatForDoctype,
  getLetterheadDoc,
  getLetterheads as apiGetLetterheads,
} from "../api/crispy";
import { getLogger } from "../logger";

let letterheadCache: Map<string, any> | null = null;
const MAX_LETTERHEAD_CACHE_ENTRIES = 20;
const logger = getLogger({ module: "FormatLoader" });

export interface FormatInfo {
  name: string;
  doc_type: string;
  is_default?: number;
}

export interface FormatData {
  name: string;
  doc_type?: string;
  crispy_format_type?: string;
  report?: string;
  contract?: string;
  layout_json?: string;
  presentation_settings?: string;
  doc_header?: string;
  doc_footer?: string;
  typst_preamble?: string;
  pdf_standard?: string;
  typst_code?: string;
  raw_typst?: number;
  is_default?: number;
}

export function parseCrispyFormatDoc(doc: FormatData): {
  layout: CrispyLayout | null;
  presentation_settings: PresentationSettings;
  docHeader: string;
  formatDoc: FormatData;
} {
  let layout: CrispyLayout | null = null;
  let presentation_settings: PresentationSettings = merge_presentation_settings(
    default_presentation_settings,
    {},
  );

  // Parse layout JSON (normalize section ids, etc.)
  if (doc.layout_json) {
    layout = deserializeLayout(doc.layout_json);
  }

  // Parse canonical presentation settings.
  if (doc.presentation_settings) {
    const settings = safeJsonParse<Record<string, any>>(
      doc.presentation_settings,
      {
        fallback: {},
        logger,
        errorMessage: "Failed to parse presentation_settings",
      },
    );
    if (settings && settings.source === undefined) {
      settings.source = "custom";
    }
    presentation_settings = merge_presentation_settings(
      default_presentation_settings,
      settings,
    );
  }

  const docHeader = doc.doc_header || "";

  return { layout, presentation_settings, docHeader, formatDoc: doc };
}

/**
 * Get all Crispy Formats for a specific DocType
 */
export async function getFormatsForDoctype(
  doctype: string,
): Promise<FormatInfo[]> {
  try {
    return await getCrispyFormatsForDoctype(doctype);
  } catch (error) {
    logger.error("Error fetching formats", error);
    return [];
  }
}

/**
 * Get the default format for a DocType
 */
export async function getDefaultFormat(
  doctype: string,
): Promise<string | null> {
  try {
    return await getDefaultCrispyFormatForDoctype(doctype);
  } catch (error) {
    logger.error("Error fetching default format", error);
    return null;
  }
}

/**
 * Load complete format data including layout and page settings
 */
export async function loadFormatData(formatName: string): Promise<{
  layout: any;
  presentation_settings: PresentationSettings;
  formatDoc: FormatData;
} | null> {
  try {
    const doc = await getCrispyFormat(formatName);
    const parsed = parseCrispyFormatDoc(doc);
    await hydrateLayoutTypstBlocks(parsed.layout, doc.doc_type || "");
    return {
      layout: parsed.layout,
      presentation_settings: parsed.presentation_settings,
      formatDoc: parsed.formatDoc,
    };
  } catch (error) {
    logger.error("Error loading format data", error);
    return null;
  }
}

async function hydrateLayoutTypstBlocks(
  layout: CrispyLayout | null,
  doctype: string,
): Promise<void> {
  if (!layout || !doctype) return;
  const fields = getTypstBlockLayoutFields(layout);
  if (!fields.length) return;

  try {
    const api = await import("../api/crispy");
    if (typeof api.getApplicableTypstBlocks !== "function") return;
    const blocks = await api.getApplicableTypstBlocks({ doctype });
    const byKey = new Map(blocks.map((block) => [block.block_key, block]));
    fields.forEach((field: any) => {
      const key = String(field.crispy_typst_block || "").trim();
      if (!key) {
        delete field.crispy_typst_block_code;
        return;
      }
      const block = byKey.get(key);
      if (!block) {
        delete field.crispy_typst_block_code;
        return;
      }
      field.crispy_typst_block_name = block.block_name;
      field.crispy_typst_block_code = block.typst_code || "";
    });
  } catch (error) {
    logger.warn("Failed to hydrate Crispy Typst Blocks", error);
  }
}

function getTypstBlockLayoutFields(layout: CrispyLayout): any[] {
  const fields: any[] = [];
  (layout.sections || []).forEach((section) => {
    (section.columns || []).forEach((column) => {
      (column.fields || []).forEach((field: any) => {
        if (field?.fieldtype === "Crispy Typst Block") {
          fields.push(field);
        }
      });
    });
  });
  return fields;
}

/**
 * Get all available Letter Heads
 */
export async function getLetterheads(): Promise<string[]> {
  try {
    return await apiGetLetterheads();
  } catch (error) {
    logger.error("Error fetching letterheads", error);
    return [];
  }
}

export async function loadLetterheadDoc(
  letterheadName: string,
): Promise<any | null> {
  if (!letterheadName) return null;

  try {
    if (!letterheadCache) {
      letterheadCache = new Map();
    }

    if (letterheadCache.has(letterheadName)) {
      // Refresh LRU position: delete + re-insert moves to most-recent end.
      const cached = letterheadCache.get(letterheadName) || null;
      letterheadCache.delete(letterheadName);
      letterheadCache.set(letterheadName, cached);
      return cached;
    }

    const doc = await getLetterheadDoc(letterheadName);
    letterheadCache.set(letterheadName, doc);
    // Evict oldest entries when over capacity.
    while (letterheadCache.size > MAX_LETTERHEAD_CACHE_ENTRIES) {
      const oldestKey = letterheadCache.keys().next().value;
      if (oldestKey === undefined) break;
      letterheadCache.delete(oldestKey);
    }
    return doc;
  } catch (error) {
    logger.error("Error fetching letterhead data", error);
    return null;
  }
}

export async function resolveLetterheadDoc(
  letterheadName?: string | null,
): Promise<any | null> {
  if (!letterheadName) return null;
  return loadLetterheadDoc(letterheadName);
}

export function clearLetterheadCache(letterheadName?: string) {
  if (!letterheadCache) return;
  if (!letterheadName) {
    letterheadCache.clear();
    return;
  }
  letterheadCache.delete(letterheadName);
}

/**
 * Get full Letter Head document with image
 */
export async function getLetterheadData(
  letterheadName: string,
): Promise<any | null> {
  return loadLetterheadDoc(letterheadName);
}
