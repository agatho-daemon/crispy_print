export type BrandingMode = "letterhead" | "logo" | "none"

export function resolveBrandingMode(
	pageSettings?: Record<string, any> | null,
	letterheadData?: Record<string, any> | null
): BrandingMode {
	const raw = String(pageSettings?.brandingMode || "").toLowerCase()
	if (raw === "letterhead" || raw === "logo" || raw === "none") {
		return raw
	}
	if (pageSettings?.logo?.image || pageSettings?.logo?.company) {
		return "logo"
	}
	if (letterheadData && (letterheadData as any).image) {
		return "letterhead"
	}
	if (pageSettings?.letterhead) {
		return "letterhead"
	}
	return "none"
}

export function resolveBrandingImage(
	pageSettings?: Record<string, any> | null,
	letterheadData?: Record<string, any> | null
): string | null {
	const mode = resolveBrandingMode(pageSettings, letterheadData)
	if (mode === "logo") {
		const image = pageSettings?.logo?.image
		return image ? String(image) : null
	}
	if (mode === "letterhead") {
		const image = (letterheadData as any)?.image
		return image ? String(image) : null
	}
	return null
}

export function getLetterheadFilename(
	pageSettings?: Record<string, any> | null,
	letterheadData?: Record<string, any> | null
): string {
	const mode = resolveBrandingMode(pageSettings, letterheadData)
	if (mode !== "letterhead") return ""
	const image = (letterheadData as any)?.image
	if (!image) return ""
	return String(image).split("/").pop() || ""
}

export function buildForegroundPlacements(options: {
	pageSettings?: Record<string, any> | null
	brandingMode?: BrandingMode
	qrEnabled?: boolean
	qrFilename?: string | null
	qrSettings?: Record<string, any> | null
}): string[] {
	const brandingMode =
		options.brandingMode || resolveBrandingMode(options.pageSettings || null, null)
	const pageSettings = options.pageSettings || {}
	const lines: string[] = []

	if (brandingMode === "logo") {
		const logoSettings = pageSettings.logo || {}
		const logoImage = String(logoSettings.image || "")
		const logoFilename = logoImage ? logoImage.split("/").pop() : ""
		const logoSize = Number(logoSettings.size) || 25
		const logoDx = Number(logoSettings.dx) || 0
		const logoDy = Number(logoSettings.dy) || 0
		if (logoFilename) {
			lines.push(
				`#place(top + left, dx: ${logoDx}mm, dy: ${logoDy}mm, image("${logoFilename}", width: ${logoSize}mm))`
			)
		}
	}

	const qrSettings = options.qrSettings || {}
	const qrSize = Number(qrSettings.size) || 15
	const qrDx = Number(qrSettings.dx) || 0
	const qrDy = Number(qrSettings.dy) || 0
	if (options.qrEnabled && options.qrFilename) {
		lines.push(
			`#place(bottom + left, dx: ${qrDx}mm, dy: ${qrDy}mm, image("${options.qrFilename}", width: ${qrSize}mm))`
		)
	}

	return lines
}
