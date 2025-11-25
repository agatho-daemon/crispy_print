// composables/useStore.ts
// State management for Crispy Print Format Builder

import { ref, computed } from "vue"
import { createDefaultLayout, serializeLayout, deserializeLayout } from "@/utils/layout"
import type { CrispyLayout, DocField } from "@/utils/layout"

declare const frappe: any
declare const __: any

let storeInstance: ReturnType<typeof buildStore> | null = null

interface CrispyFormat {
	name: string
	doc_type: string
	typst_preamble?: string
	typst_layout?: string
	layout_json?: string
	page_settings?: string
	__onload?: any
}

interface PageSettings {
	pageSize: string
	orientation: string
	margins: {
		top: number
		bottom: number
		left: number
		right: number
	}
	fontFamily: string
	fontSize: number
	letterhead: string
}

function buildStore() {
	// State
	const crispyFormat = ref<CrispyFormat | null>(null)
	const layout = ref<CrispyLayout | null>(null)
	const meta = ref<any>(null)
	const fields = ref<DocField[]>([])
	const letterhead = ref<any>(null)
	const dirty = ref(false)
	const loading = ref(false)

	const pageSettings = ref<PageSettings>({
		pageSize: "A4",
		orientation: "portrait",
		margins: {
			top: 20,
			bottom: 20,
			left: 20,
			right: 20,
		},
		fontFamily: "Arial",
		fontSize: 11,
		letterhead: "",
	})

	// Computed
	const formatName = computed(() => crispyFormat.value?.name || null)
	const docType = computed(() => crispyFormat.value?.doc_type || null)

	/**
	 * Fetch Crispy Format document and load DocType metadata
	 */
	async function fetch(formatName: string) {
		if (typeof frappe === "undefined") {
			console.warn("[Store] Frappe not available - running in dev mode")
			return
		}

		loading.value = true

		try {
			// Fetch the Crispy Format document
			const doc = await frappe.db.get_doc("Crispy Format", formatName)
			crispyFormat.value = doc

			console.log("[Store] Loaded Crispy Format:", doc)

			// Load DocType metadata
			if (doc.doc_type) {
				await new Promise<void>((resolve) => {
					frappe.model.with_doctype(doc.doc_type, () => {
						meta.value = frappe.get_meta(doc.doc_type)

						const skipTypes = ["Section Break", "Column Break"]

							// Extract fields for the fields pane, matching beta builder behavior
							const baseFields: DocField[] = meta.value.fields
								.filter(
									(f: DocField) =>
										f.fieldname &&
										!skipTypes.includes(f.fieldtype || "")
								)
								.map((f: DocField) => ({
									fieldname: f.fieldname,
									label: f.label || f.fieldname,
									fieldtype: f.fieldtype,
								options: f.options,
								print_hide: f.print_hide,
							}))

						const extras: DocField[] = [
							{ label: "Custom HTML", fieldname: "custom_html", fieldtype: "HTML" },
							{ label: "ID (name)", fieldname: "name", fieldtype: "Data" },
							{ label: "Spacer", fieldname: "spacer", fieldtype: "Spacer" },
							{ label: "Divider", fieldname: "divider", fieldtype: "Divider" },
						]

						const templateFields: DocField[] =
							typeof frappe === "undefined" ||
							!crispyFormat.value?.__onload?.print_templates
								? []
								: crispyFormat.value.__onload.print_templates
										.map((template: any) => {
											let df: any
											if (template.field) {
												df = frappe.meta.get_docfield(meta.value.name, template.field)
											} else {
												const scrub =
													typeof frappe.scrub === "function"
														? frappe.scrub(template.name)
														: template.name.toLowerCase().replace(/\s+/g, "_")
												df = {
													label: template.name,
													fieldname: scrub,
												}
											}

											if (!df?.fieldname) return null

											return {
												label: `${df.label} (Field Template)`,
												fieldname: `${df.fieldname}_template`,
												fieldtype: "Field Template",
												options: template.name,
											} as DocField
										})
										.filter(Boolean)

						fields.value = [...extras, ...templateFields, ...baseFields]

						console.log("[Store] Loaded DocType meta:", meta.value.name)
						console.log("[Store] Available fields:", fields.value.length)

						resolve()
					})
				})
			}

			// Load or create layout
			layout.value = getLayout()
			if (!layout.value || !layout.value.sections?.length) {
				layout.value = getDefaultLayout()
			}

			// Load page settings
			if (doc.page_settings) {
				try {
					pageSettings.value = JSON.parse(doc.page_settings)
				} catch (e) {
					console.warn("[Store] Failed to parse page_settings:", e)
				}
			}

			// Load letterhead if specified
			if (pageSettings.value.letterhead) {
				try {
					letterhead.value = await frappe.db.get_doc(
						"Letter Head",
						pageSettings.value.letterhead
					)
				} catch (e) {
					console.warn("[Store] Failed to load letterhead:", e)
				}
			}

			dirty.value = false
		} catch (error) {
			console.error("[Store] Failed to fetch Crispy Format:", error)
			frappe.throw(__("Failed to load Crispy Format"))
		} finally {
			loading.value = false
		}
	}

	/**
	 * Get layout from Crispy Format or create default
	 */
	function getLayout(): CrispyLayout {
		if (!crispyFormat.value) {
			return { sections: [] }
		}

		// Try to parse existing layout_json
		if (crispyFormat.value.layout_json) {
			const parsed = deserializeLayout(crispyFormat.value.layout_json)
			if (parsed) {
				return parsed
			}
		}

		// Create default layout from DocType meta
		return getDefaultLayout()
	}

	/**
	 * Create default layout from DocType metadata
	 */
	function getDefaultLayout(): CrispyLayout {
		if (!meta.value) {
			return { sections: [] }
		}

		return createDefaultLayout(meta.value, crispyFormat.value)
	}

	/**
	 * Save changes to backend
	 */
	async function saveChanges() {
		if (typeof frappe === "undefined") {
			console.warn("[Store] Cannot save - Frappe not available")
			return
		}

		if (!crispyFormat.value || !layout.value) {
			console.warn("[Store] Nothing to save")
			return
		}

		loading.value = true

		try {
			// Serialize layout to JSON
			const layoutJson = serializeLayout(layout.value)

			// TODO: Generate Typst markup from layout
			// For now, just store the JSON
			const typstLayout = `// Generated Typst layout\n// TODO: Implement layout to Typst conversion`

			// Prepare update data
			const updateData = {
				layout_json: layoutJson,
				typst_layout: typstLayout,
				page_settings: JSON.stringify(pageSettings.value),
			}

			// Save to backend
			await frappe.call({
				method: "frappe.client.set_value",
				args: {
					doctype: "Crispy Format",
					name: crispyFormat.value.name,
					fieldname: updateData,
				},
			})

			console.log("[Store] Saved changes successfully")
			frappe.show_alert({
				message: __("Crispy Format saved"),
				indicator: "green",
			})

			dirty.value = false
		} catch (error) {
			console.error("[Store] Failed to save changes:", error)
			frappe.show_alert({
				message: __("Failed to save changes"),
				indicator: "red",
			})
		} finally {
			loading.value = false
		}
	}

	/**
	 * Mark as dirty when layout changes
	 */
	function markDirty() {
		dirty.value = true
	}

	/**
	 * Reset layout to default
	 */
	function resetLayout() {
		layout.value = getDefaultLayout()
		dirty.value = true
	}

	const store = {
		// State
		crispyFormat,
		layout,
		meta,
		fields,
		letterhead,
		pageSettings,
		dirty,
		loading,

		// Computed
		formatName,
		docType,

		// Methods
		fetch,
		saveChanges,
		markDirty,
		resetLayout,
		getDefaultLayout,
	}
	return store
}

export function useStore() {
	if (storeInstance) {
		return storeInstance
	}
	storeInstance = buildStore()
	return storeInstance
}
