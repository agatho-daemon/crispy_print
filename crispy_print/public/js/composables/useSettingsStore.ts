import type { Ref } from "vue";
import { getLogger } from "../logger";
import { resolveLetterheadDoc } from "../utils/formatLoader";

const logger = getLogger({ module: "SettingsStore" });

interface CreateSettingsStoreOptions {
  loading: Ref<boolean>;
  initializing: Ref<boolean>;
  dirty: Ref<boolean>;
  changeKey: Ref<number>;
  letterhead: Ref<any>;
  builderContext: Ref<Record<string, any>>;
}

export function createSettingsStore(options: CreateSettingsStoreOptions) {
  const { loading, initializing, dirty, changeKey, letterhead, builderContext } = options;
  let letterheadRequestSeq = 0;

  function markDirty() {
    if (loading.value || initializing.value) {
      return;
    }
    dirty.value = true;
    changeKey.value++;
  }

  async function fetchLetterhead(letterheadName: string) {
    const requestSeq = ++letterheadRequestSeq;
    if (typeof frappe === "undefined") {
      logger.warn("Cannot fetch letterhead - Frappe not available");
      return;
    }

    if (!letterheadName) {
      letterhead.value = null;
      changeKey.value++;
      return;
    }

    letterhead.value = null;
    try {
      const resolved = await resolveLetterheadDoc(letterheadName);
      if (requestSeq !== letterheadRequestSeq) return;
      letterhead.value = resolved;
      changeKey.value++;
    } catch (error) {
      if (requestSeq !== letterheadRequestSeq) return;
      logger.warn("Failed to resolve letterhead", { letterheadName, error });
      letterhead.value = null;
      changeKey.value++;
    }
  }

  function setBuilderContext(context: Record<string, any> = {}) {
    builderContext.value = context;
    logger.info("Builder context set", context);
  }

  function reset() {
    // Invalidate any in-flight letterhead fetches so their late responses
    // can't overwrite freshly loaded state.
    letterheadRequestSeq++;
    letterhead.value = null;
  }

  return {
    markDirty,
    fetchLetterhead,
    setBuilderContext,
    reset,
  };
}

