export type ReportFormatsResponse = {
	custom_formats?: Array<{ name: string; modified?: string }>;
	generic_formats?: Array<{ name: string; generic_report_type?: string }>;
	default_format?: string | null;
};

export type ReportFormatOption = { label: string; value: string };

export type ReportColumn = { fieldname: string; label: string };

export function buildReportFormatOptions(formats: ReportFormatsResponse | null | undefined): {
	options: ReportFormatOption[];
	defaultValue: string | null;
} {
	const options: ReportFormatOption[] = [];
	let defaultValue = formats?.default_format || null;

	if (formats?.custom_formats?.length) {
		formats.custom_formats.forEach((fmt) => {
			options.push({ label: fmt.name, value: fmt.name });
		});
		if (!defaultValue) {
			defaultValue = formats.custom_formats[0].name;
		}
	}

	if (formats?.generic_formats?.length) {
		formats.generic_formats.forEach((fmt) => {
			options.push({ label: fmt.name, value: fmt.name });
		});
		if (!defaultValue) {
			defaultValue = formats.generic_formats[0].name;
		}
	}

	return { options, defaultValue };
}

export function normalizeReportColumns(columns: any[] | null | undefined): ReportColumn[] {
	if (!columns || !columns.length) {
		return [];
	}

	return columns.map((col) => {
		if (typeof col === "string") {
			return {
				fieldname: col,
				label: col.replace(/_/g, " ").replace(/\b\w/g, (m) => m.toUpperCase()),
			};
		}

		const fieldname = col.fieldname || col.id || "";
		const label = col.label || fieldname;
		return { fieldname, label };
	});
}
