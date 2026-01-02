export function getDefaultAlignment(fieldtype?: string): "left" | "center" | "right" {
	const numericTypes = ["Int", "Float", "Currency", "Percent"]
	return numericTypes.includes(fieldtype || "") ? "right" : "left"
}
