import { getBrandingProfilePresentationSettings } from "../api/crispy";
import { getLogger } from "../logger";
import {
  default_presentation_settings,
  merge_presentation_settings,
  type PresentationSettings,
} from "./presentation_settings";

const logger = getLogger({ module: "EffectivePresentationSettings" });
const inflightBrandingProfileRequests = new Map<
  string,
  Promise<Partial<PresentationSettings>>
>();

export async function resolve_effective_presentation_settings(
  presentation_settings: PresentationSettings,
  effective_company?: string | null,
  apply_format_overrides = true,
): Promise<PresentationSettings> {
  const source = presentation_settings?.source || "";
  const profile = String(presentation_settings?.branding?.profile || "").trim();
  const expectedCompany = String(
    effective_company || presentation_settings?.branding?.company || "",
  ).trim();

  if (source !== "branding_profile" || !profile) {
    return merge_presentation_settings(
      default_presentation_settings,
      presentation_settings || {},
    );
  }

  try {
    let profile_settings_request = inflightBrandingProfileRequests.get(profile);
    if (!profile_settings_request) {
      profile_settings_request =
        getBrandingProfilePresentationSettings(profile);
      inflightBrandingProfileRequests.set(profile, profile_settings_request);
    }
    const profile_settings = await profile_settings_request.finally(() => {
      inflightBrandingProfileRequests.delete(profile);
    });
    const profileCompany = String(
      profile_settings?.branding?.company ||
        profile_settings?.branding?.logo?.company ||
        "",
    ).trim();
    if (
      expectedCompany &&
      profileCompany &&
      profileCompany !== expectedCompany
    ) {
      logger.warn(
        "Crispy Branding Profile company does not match render company; using format settings",
        {
          profile,
          profileCompany,
          expectedCompany,
        },
      );
      const fallback = merge_presentation_settings(
        default_presentation_settings,
        presentation_settings || {},
      );
      fallback.source = "custom";
      fallback.branding.profile = "";
      fallback.branding.company = expectedCompany;
      fallback.branding.logo.company = expectedCompany;
      return fallback;
    }

    let effective = merge_presentation_settings(
      default_presentation_settings,
      profile_settings || {},
    );
    effective = merge_presentation_settings(
      effective,
      getRendererPresentationDefaults(presentation_settings.report?.renderer),
    );
    if (apply_format_overrides) {
      effective = merge_presentation_settings(
        effective,
        presentation_settings.overrides || {},
      );
    }
    effective.source = "branding_profile";
    effective.branding.profile = profile;
    if (expectedCompany) {
      effective.branding.company = expectedCompany;
      effective.branding.logo.company = expectedCompany;
    }
    effective.language = presentation_settings.language || effective.language;
    if (presentation_settings.report) {
      effective.report = presentation_settings.report;
    }
    return effective;
  } catch (error) {
    logger.warn(
      "Failed to resolve Crispy Branding Profile; using format settings",
      error,
    );
    return merge_presentation_settings(
      default_presentation_settings,
      presentation_settings || {},
    );
  }
}

function getRendererPresentationDefaults(
  renderer?: string,
): Partial<PresentationSettings> {
  if (
    renderer === "receivable_payable" ||
    renderer === "financial_statement" ||
    renderer === "general_ledger" ||
    renderer === "bank_reconciliation"
  ) {
    return {
      page: { orientation: "landscape" },
    } as Partial<PresentationSettings>;
  }
  return {};
}
