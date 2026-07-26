import { afterEach, describe, expect, it, vi } from "vitest";
import { __ } from "../../utils/i18n";

describe("Crispy Print translation context", () => {
  afterEach(() => {
    delete (globalThis as any).__;
    delete (globalThis as any).frappe;
  });

  it("passes gettext context to the global Frappe translator", () => {
    const translate = vi.fn(
      (text: string, _replacements: unknown[] | null, context?: string) =>
        context === "Crispy Print UI" ? "سازنده" : text,
    );
    (globalThis as any).__ = translate;

    expect(__("Builder", null, "Crispy Print UI")).toBe("سازنده");
    expect(translate).toHaveBeenCalledWith("Builder", null, "Crispy Print UI");
  });
});
