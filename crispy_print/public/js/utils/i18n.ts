type TranslateFn = (text: string, replacements?: unknown[]) => string;

const interpolate: TranslateFn = (text, replacements) => {
	if (!Array.isArray(replacements) || replacements.length === 0) {
		return text;
	}

	return replacements.reduce((output, value, index) => {
		const token = new RegExp(`\\{${index}\\}`, "g");
		return output.replace(token, String(value ?? ""));
	}, text);
};

export const __: TranslateFn = (text, replacements) => {
	const globalTranslate = (globalThis as any).__;
	if (typeof globalTranslate === "function") {
		return globalTranslate(text, replacements);
	}

	const frappeTranslate = (globalThis as any).frappe?.__;
	if (typeof frappeTranslate === "function") {
		return frappeTranslate(text, replacements);
	}

	return interpolate(text, replacements);
};
