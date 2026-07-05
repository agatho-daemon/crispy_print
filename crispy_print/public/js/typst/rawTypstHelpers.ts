import { quoteTypstString } from "../utils/typstEscape"

const IMAGE_EXTENSIONS = new Set([
	"png",
	"jpg",
	"jpeg",
	"svg",
	"gif",
	"webp",
	"bmp",
	"tif",
	"tiff",
	"avif",
])

const CRISPY_IMAGE_RE = /crispy_image\(\s*"([^"\n]+)"/g
const CRISPY_BLOCK_RE = /crispy_block\(\s*"([^"\n]+)"/g

export interface RawTypstBlock {
	name?: string
	typst_code?: string
}

export function extractCrispyBlockIds(typstSource: string): Set<string> {
	const ids = new Set<string>()
	for (const match of String(typstSource || "").matchAll(CRISPY_BLOCK_RE)) {
		const id = String(match[1] || "").trim()
		if (id) ids.add(id)
	}
	return ids
}

export function buildRawTypstHelperBlock(blocks: RawTypstBlock[] = [], typstSource = ""): string {
	const referencedBlockIds = extractCrispyBlockIds(typstSource)
	const lines: string[] = []
	lines.push("// Crispy Raw Typst helpers")
	lines.push("#let crispy_image(filename, ..args) = image(filename, ..args)")
	lines.push("#let crispy_blocks = (")
	for (const block of blocks) {
		const name = String(block?.name || "").trim()
		const code = String(block?.typst_code || "").trim()
		if (referencedBlockIds.size && !referencedBlockIds.has(name)) continue
		if (!referencedBlockIds.size) continue
		if (!name || !code) continue
		lines.push(`  ${quoteTypstString(name)}: [`)
		lines.push(code)
		lines.push("  ],")
	}
	lines.push(")")
	lines.push("#let crispy_block(id) = {")
	lines.push("  let block = crispy_blocks.at(id, default: none)")
	lines.push("  if block == none { panic(\"Crispy Typst Block not found: \" + str(id)) }")
	lines.push("  block")
	lines.push("}")
	return lines.join("\n")
}

export function isPrivateCrispyImageFilename(value: string): boolean {
	const raw = String(value || "").trim()
	if (!raw) return false
	if (raw.includes("/") || raw.includes("\\") || raw.includes("..")) return false
	if (/^[a-z][a-z0-9+.-]*:/i.test(raw)) return false
	const ext = raw.split(".").pop()?.toLowerCase() || ""
	return IMAGE_EXTENSIONS.has(ext)
}

export function extractCrispyImageAssetFiles(typstSource: string, siteName?: string | null): string[] {
	const site = String(siteName || "").trim()
	if (!site) return []
	const assets: string[] = []
	const seen = new Set<string>()
	for (const match of typstSource.matchAll(CRISPY_IMAGE_RE)) {
		const filename = String(match[1] || "").trim()
		if (!isPrivateCrispyImageFilename(filename)) continue
		const asset = `/assets/${site}/private/files/${filename}`
		if (seen.has(asset)) continue
		seen.add(asset)
		assets.push(asset)
	}
	return assets
}
