// composables/useStore.ts
// State management for Crispy Print Format Builder

import { ref, computed, watch } from "vue"
import { createDefaultLayout, serializeLayout } from "../utils/layout"
import type { CrispyLayout, DocField } from "../utils/layout"
import { defaultPageSettings, type PageSettings } from "../utils/pageSettings"
import { parseCrispyFormatDoc, resolveLetterheadDoc } from "../utils/formatLoader"
import { getCrispyFormat, saveCrispyFormat } from "../api/crispy"
import { withDoctype } from "../api/frappe"

let storeInstance: ReturnType<typeof buildStore> | null = null

interface CrispyFormat {
	name: string
	doc_type: string
	is_default?: number
	doc_header?: string
	doc_footer?: string
	qrcode?: number
	raw_typst?: number
	typst_preamble?: string
	typst_code?: string
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
	const changeKey = ref(0)
	const removeQr = ref(false)
	const rawTypst = ref(false)
	const typstCode = ref("")

	const pageSettings = ref<PageSettings>({ ...defaultPageSettings })

	// Computed
	const formatName = computed(() => crispyFormat.value?.name || null)
	const docType = computed(() => crispyFormat.value?.doc_type || null)
	const docHeader = computed(() => crispyFormat.value?.doc_header || "")
	const docFooter = computed(() => crispyFormat.value?.doc_footer || "")
	const qrEnabled = computed(() => Boolean(crispyFormat.value?.qrcode))
	const typstPreamble = computed(() => crispyFormat.value?.typst_preamble || "")

	/**
	 * Fetch Crispy Format document and load DocType metadata
	 */
	async function fetch(formatName: string) {
		loading.value = true
		changeKey.value = 0
		removeQr.value = false

		try {
			// Fetch the Crispy Format document
			const doc = await getCrispyFormat(formatName)
			crispyFormat.value = doc
			rawTypst.value = Boolean(doc.raw_typst)
			typstCode.value = doc.typst_code || ""

			// Load DocType metadata
			if (doc.doc_type) {
				await withDoctype(doc.doc_type)
				meta.value = frappe.get_meta(doc.doc_type)

				const skipTypes = ["Tab Break", "Section Break", "Column Break"]

				// Extract fields for the fields pane, matching builder behavior
				const baseFields: DocField[] = meta.value.fields
					.filter((f: DocField) => f.fieldname && !skipTypes.includes(f.fieldtype || ""))
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
					{ label: "Custom Typst", fieldname: "custom_typst", fieldtype: "Typst" },
					{ label: "Spacer", fieldname: "spacer", fieldtype: "Spacer" },
					{ label: "Divider", fieldname: "divider", fieldtype: "Divider" },
				]

				const templateFields: DocField[] = !crispyFormat.value?.__onload?.print_templates
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
			}

			// Parse + normalize persisted state (shared with crispy-print)
			const parsed = parseCrispyFormatDoc(doc)

			// Load or create layout
			layout.value = parsed.layout || getDefaultLayout()

			// Load page settings (already merged with defaults by parser)
			pageSettings.value = parsed.pageSettings || { ...defaultPageSettings }

			// Load letterhead if specified
			if (pageSettings.value.letterhead) {
				letterhead.value = await resolveLetterheadDoc(pageSettings.value.letterhead)
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
		if (!crispyFormat.value || (!layout.value && !rawTypst.value)) {
			console.warn("[Store] Nothing to save")
			return
		}

		loading.value = true

		try {
			// Serialize layout to JSON
			const layoutJson = layout.value ? serializeLayout(layout.value) : ""

			// Prepare update data
			const updateData = {
				layout_json: layoutJson,
				typst_code: typstCode.value,
				page_settings: JSON.stringify(pageSettings.value),
				raw_typst: rawTypst.value ? 1 : 0,
			}

			await saveCrispyFormat(crispyFormat.value.name, updateData)

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
		changeKey.value++
	}

	/**
	 * Reset layout to default
	 */
	function resetLayout() {
		layout.value = getDefaultLayout()
		markDirty()
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
			return
		}

		letterhead.value = await resolveLetterheadDoc(letterheadName)
	}

	// Watch for letterhead changes in pageSettings
	watch(
		() => pageSettings.value.letterhead,
		(newLetterhead) => {
			fetchLetterhead(newLetterhead)
		}
	)

	watch(removeQr, () => {
		changeKey.value++
	})

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
		changeKey,

		// Computed
		formatName,
		docType,
		docHeader,
		docFooter,
		qrEnabled,
		typstPreamble,
		rawTypst,
		typstCode,
		removeQr,

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
