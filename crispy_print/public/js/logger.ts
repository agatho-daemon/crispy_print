export type LogLevel = "debug" | "info" | "warn" | "error" | "silent";

export interface LoggerOptions {
	name: string; // e.g. "Crispy Print"
	level?: LogLevel; // default: "info"
	devOnly?: boolean; // if true, logs only in dev
}

export interface Logger {
	debug(msg: string, ctx?: unknown): void;
	info(msg: string, ctx?: unknown): void;
	warn(msg: string, ctx?: unknown): void;
	error(msg: string, ctx?: unknown): void;
	child(extra: Record<string, unknown>): Logger;
	setLevel(level: LogLevel): void;
}

function isDevMode(): boolean {
	if (typeof window === "undefined") return false;
	const boot = (window as any).frappe?.boot;
	return Boolean(boot?.developer_mode);
}

function hasProdOverride(): boolean {
	if (typeof window === "undefined") return false;
	const override = (window as any).CRISPY_DEBUG;
	return override === true || override === "true" || override === 1;
}

function levelRank(level: LogLevel): number {
	switch (level) {
		case "debug":
			return 10;
		case "info":
			return 20;
		case "warn":
			return 30;
		case "error":
			return 40;
		case "silent":
			return 100;
	}
}

export function createLogger(opts: LoggerOptions): Logger {
	const base = { ...opts };
	let currentLevel: LogLevel = base.level ?? "info";
	const devOnly = base.devOnly ?? true;
	const prefix = `[${base.name}]`;

	const shouldLog = (lvl: LogLevel): boolean => {
		if (devOnly && !isDevMode() && !hasProdOverride()) return false;
		return levelRank(lvl) >= levelRank(currentLevel);
	};

	const emit = (lvl: LogLevel, msg: string, ctx?: unknown): void => {
		if (!shouldLog(lvl)) return;

		const payload = ctx === undefined ? [] : [ctx];
		switch (lvl) {
			case "debug":
				console.debug(prefix, msg, ...payload);
				break;
			case "info":
				console.info(prefix, msg, ...payload);
				break;
			case "warn":
				console.warn(prefix, msg, ...payload);
				break;
			case "error":
				console.error(prefix, msg, ...payload);
				break;
			default:
				break;
		}
	};

	const child = (extra: Record<string, unknown>): Logger => {
		return {
			debug: (m, c) => emit("debug", m, { ...extra, ctx: c }),
			info: (m, c) => emit("info", m, { ...extra, ctx: c }),
			warn: (m, c) => emit("warn", m, { ...extra, ctx: c }),
			error: (m, c) => emit("error", m, { ...extra, ctx: c }),
			child: (more) => child({ ...extra, ...more }),
			setLevel: (lvl) => {
				currentLevel = lvl;
			},
		};
	};

	return {
		debug: (m, c) => emit("debug", m, c),
		info: (m, c) => emit("info", m, c),
		warn: (m, c) => emit("warn", m, c),
		error: (m, c) => emit("error", m, c),
		child,
		setLevel: (lvl) => {
			currentLevel = lvl;
		},
	};
}

const rootLogger = createLogger({ name: "Crispy Print", devOnly: true });

if (typeof window !== "undefined") {
	const existing = (window as any).CrispyPrintLogger;
	if (!existing) {
		(window as any).CrispyPrintLogger = rootLogger;
	}
}

export function getLogger(extra?: Record<string, unknown>): Logger {
	if (extra && Object.keys(extra).length) {
		return rootLogger.child(extra);
	}
	return rootLogger;
}

export { rootLogger };
