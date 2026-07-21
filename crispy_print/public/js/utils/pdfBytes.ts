export function decodePdfData(value: string | null | undefined): Uint8Array {
	const encoded = String(value || "").trim()
	if (!encoded) return new Uint8Array()

	const binary = atob(encoded)
	const bytes = new Uint8Array(binary.length)
	for (let index = 0; index < binary.length; index += 1) {
		bytes[index] = binary.charCodeAt(index)
	}
	return bytes
}

