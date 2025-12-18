// composables/useStore.ts
// State management for Crispy Print Format Builder

import { ref, computed, watch } from "vue"
import { createDefaultLayout, serializeLayout, deserializeLayout } from "../utils/layout"
import type { CrispyLayout, DocField } from "../utils/layout"
import { defaultPageSettings, mergePageSettings, type PageSettings } from "../utils/pageSettings"


let storeInstance: ReturnType<typeof buildStore> | null = null

interface CrispyFormat {
	name: string
	doc_type: string
	is_default: boolean
	doc_header?: string
	typst_preamble?: string
	typst_layout?: string
	layout_json?: string
	page_settings?: string
	__onload?: any
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

	const pageSettings = ref<PageSettings>({ ...defaultPageSettings })

	// Computed
	const formatName = computed(() => crispyFormat.value?.name || null)
	const docType = computed(() => crispyFormat.value?.doc_type || null)
	const docHeader = computed(() => crispyFormat.value?.doc_header || "")

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

			// Load DocType metadata
			if (doc.doc_type) {
				await new Promise<void>((resolve) => {
					frappe.model.with_doctype(doc.doc_type, () => {
						meta.value = frappe.get_meta(doc.doc_type)

						const skipTypes = ["Tab Break", "Section Break", "Column Break"]

						// Extract fields for the fields pane, matching builder behavior
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
							{ label: "DocType", fieldname: "doctype", fieldtype: "Data" },
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

						resolve()
					})
				})
			}

			// Load or create layout
			layout.value = getLayout()
			// console.log("[Store] Loaded layout:", layout.value)
			if (!layout.value || !layout.value.sections?.length) {
				layout.value = getDefaultLayout()
			}

			// Load page settings
			if (doc.page_settings) {
				try {
					pageSettings.value = mergePageSettings(defaultPageSettings, JSON.parse(doc.page_settings))
				} catch (e) {
					console.warn("[Store] Failed to parse page_settings:", e)
					pageSettings.value = { ...defaultPageSettings }
				}
			} else {
				pageSettings.value = { ...defaultPageSettings }
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

			// console.log("[Store] Saved changes successfully")
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

	/**
	 * Fetch letterhead when letterhead setting changes
	 */
	async function fetchLetterhead(letterheadName: string) {
		if (typeof frappe === "undefined") {
			console.warn("[Store] Cannot fetch letterhead - Frappe not available")
			return
		}

		if (!letterheadName) {
			letterhead.value = null
			// console.log("[Store] Letterhead cleared")
			return
		}

		try {
			letterhead.value = await frappe.db.get_doc("Letter Head", letterheadName)
			// console.log("[Store] Loaded letterhead:", letterheadName, letterhead.value)
		} catch (e) {
			console.error("[Store] Failed to load letterhead:", e)
			letterhead.value = null
		}
	}

	// Watch for letterhead changes in pageSettings
	watch(
		() => pageSettings.value.letterhead,
		(newLetterhead) => {
			fetchLetterhead(newLetterhead)
		}
	)

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
		docHeader,

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
