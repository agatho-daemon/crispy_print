export type JsonParseOptions = {
	fallback?: any;
	logger?: { error?: (message: string, error?: unknown) => void };
	errorMessage?: string;
};

export function safeJsonParse<T>(raw: string, options: JsonParseOptions = {}): T {
	const fallback = options.fallback as T;
	try {
		return JSON.parse(raw) as T;
	} catch (error) {
		options.logger?.error?.(options.errorMessage || "Failed to parse JSON", error);
		return fallback;
	}
}

export function deepClone<T>(value: T): T {
	if (typeof structuredClone === "function") {
		try {
			return structuredClone(value);
		} catch {
			// Fall through to JSON clone.
		}
	}
	try {
		return JSON.parse(JSON.stringify(value)) as T;
	} catch {
		// Last resort: return original reference to avoid runtime crash.
		return value;
	}
}
