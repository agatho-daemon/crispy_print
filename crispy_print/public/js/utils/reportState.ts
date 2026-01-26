const SVG_NS = "http://www.w3.org/2000/svg";
const XLINK_NS = "http://www.w3.org/1999/xlink";

export type ReportState = {
	report: string;
	filters?: Record<string, any>;
	columns?: any[];
	chartSvg?: string;
};

function replaceRef(value: string, fromId: string, toId: string): string {
	return value.replaceAll(`url(#${fromId})`, `url(#${toId})`).replaceAll(`#${fromId}`, `#${toId}`);
}

function normalizeSvgIds(svg: SVGSVGElement) {
	const seen = new Map<string, number>();
	const all = svg.querySelectorAll("[id]");

	all.forEach((el) => {
		const id = el.getAttribute("id");
		if (!id) return;

		if (!seen.has(id)) {
			seen.set(id, 1);
			return;
		}

		const next = (seen.get(id) || 1) + 1;
		seen.set(id, next);
		const newId = `${id}__dup${next}`;
		el.setAttribute("id", newId);

		svg.querySelectorAll("*").forEach((node) => {
			Array.from(node.attributes || []).forEach((attr) => {
				const updated = replaceRef(attr.value, id, newId);
				if (updated !== attr.value) {
					node.setAttribute(attr.name, updated);
				}
			});
		});
	});
}

export function normalizeReportChartSvg(rawSvg: string): string {
	if (!rawSvg || typeof rawSvg !== "string") return "";
	const parser = new DOMParser();
	const doc = parser.parseFromString(rawSvg, "image/svg+xml");
	const svg = doc.querySelector("svg");
	if (!svg) return "";

	if (!svg.getAttribute("xmlns")) {
		svg.setAttribute("xmlns", SVG_NS);
	}
	if (!svg.getAttribute("xmlns:xlink")) {
		svg.setAttribute("xmlns:xlink", XLINK_NS);
	}

	const gridLines = svg.querySelectorAll(".line-horizontal, .line-vertical");
	gridLines.forEach((line) => {
		line.setAttribute("stroke", "#D1D5DB");
		line.setAttribute("stroke-width", "0.75");
		line.setAttribute("shape-rendering", "crispEdges");
	});

	normalizeSvgIds(svg);
	return new XMLSerializer().serializeToString(svg);
}

export function loadReportState(reportName: string): ReportState | null {
	if (!reportName || typeof window === "undefined") return null;
	const key = `crispy-print:report:${reportName}`;
	try {
		const raw = window.sessionStorage.getItem(key);
		if (!raw) return null;
		const parsed = JSON.parse(raw);
		if (parsed?.report && parsed.report !== reportName) return null;
		return parsed as ReportState;
	} catch (error) {
		console.warn("[CrispyPP] Failed to read report state:", error);
		return null;
	}
}
