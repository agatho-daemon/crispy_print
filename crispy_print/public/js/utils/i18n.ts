type TranslateFn = (
  text: string,
  replacements?: unknown[] | null,
  context?: string,
) => string;

const interpolate: TranslateFn = (text, replacements) => {
  if (!Array.isArray(replacements) || replacements.length === 0) {
    return text;
  }

  return replacements.reduce<string>((output, value, index) => {
    const token = new RegExp(`\\{${index}\\}`, "g");
    return output.replace(token, String(value ?? ""));
  }, text);
};

export const __: TranslateFn = (text, replacements, context) => {
  const globalTranslate = (globalThis as any).__;
  if (typeof globalTranslate === "function") {
    return String(globalTranslate(text, replacements, context));
  }

  const frappeTranslate = (globalThis as any).frappe?.__;
  if (typeof frappeTranslate === "function") {
    return String(frappeTranslate(text, replacements, context));
  }

  return interpolate(text, replacements);
};
