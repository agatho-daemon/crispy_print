// composables/useStore.ts
// State management for Crispy Print Format Builder

import { ref, computed, watch, nextTick } from "vue"
import { createDefaultLayout, serializeLayout } from "../utils/layout"
import type { CrispyLayout, DocField } from "../utils/layout"
import { defaultPageSettings, ensureQrSettings, type PageSettings } from "../utils/pageSettings"
import { parseCrispyFormatDoc, resolveLetterheadDoc } from "../utils/formatLoader"
import { getCrispyFormat, saveCrispyFormat } from "../api/crispy"
import { withDoctype } from "../api/frappe"

let storeInstance: ReturnType<typeof buildStore> | null = null

interface CrispyFormat {
	name: string
	doc_type?: string
	// TODO: invistigate teh possibility of having a dynamic crispy_format_type for future.
	crispy_format_type?: string
	report?: string
	contract?: string
	is_default?: number
	is_generic?: number
	generic_report_type?: string
	doc_header?: string
	doc_footer?: string
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
	const builderContext = ref<Record<string, any>>({})
	const layout = ref<CrispyLayout | null>(null)
	const meta = ref<any>(null)
	const fields = ref<DocField[]>([])
	const reportColumns = ref<any[]>([])
	const reportFilters = ref<Record<string, any>>({})
	const sampleReports = ref<any[]>([]) // Available reports for generic template preview
	const letterhead = ref<any>(null)
	const dirty = ref(false)
	const loading = ref(false)
	const initializing = ref(false) // Prevents dirty marking during init
	const changeKey = ref(0)
	const rawTypst = ref(false)
	const typstCode = ref("")

	const pageSettings = ref<PageSettings>({ ...defaultPageSettings })

	// Computed
	const formatName = computed(() => crispyFormat.value?.name || null)
	const docType = computed(() => crispyFormat.value?.doc_type || null)
	const formatType = computed(() => crispyFormat.value?.crispy_format_type || "DocType")
	const isReportMode = computed(() => formatType.value === "Report")
	const docHeader = computed(() => crispyFormat.value?.doc_header || "")
	const docFooter = computed(() => crispyFormat.value?.doc_footer || "")
	const qrEnabled = computed(() => {
		const qr = pageSettings.value?.qr
		if (qr && typeof qr.enabled === "boolean") {
			return qr.enabled
		}
		return false
	})
	const typstPreamble = computed(() => crispyFormat.value?.typst_preamble || "")

	/**
	 * Fetch Crispy Format document and load DocType metadata
	 */
	async function fetch(formatName: string) {
		loading.value = true
		initializing.value = true
		changeKey.value = 0
		dirty.value = false // Set clean state BEFORE triggering any reactive updates

		try {
			// Fetch the Crispy Format document
			const doc = await getCrispyFormat(formatName)
			crispyFormat.value = doc

			// Fetch builder mode from backend
			const modeResponse = await frappe.call({
				method: "crispy_print.api.get_builder_mode",
				args: { format_name: formatName },
			})

			const builderMode = modeResponse?.message || {}

			// Set raw typst mode based on backend response
			rawTypst.value = builderMode.mode === "code" || Boolean(doc.raw_typst)
			typstCode.value = doc.typst_code || ""

			const formatType = doc.crispy_format_type || builderContext.value?.crispy_format_type || "DocType"

			// Handle Report mode
			if (formatType === "Report" && doc.report) {
				await loadReportColumns(doc.report, builderContext.value?.report_filters || {})
				console.log("[Store] Report columns loaded:", reportColumns.value)
			}

			// Load sample reports for generic Report templates
			if (formatType === "Report" && doc.is_generic && rawTypst.value) {
				await loadSampleReports()
				console.log("[Store] Sample reports loaded:", sampleReports.value)
			}

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
					{ label: "Custom Typst", fieldname: "_typst_snippet", fieldtype: "Typst" },
					{ label: "Empty Field", fieldname: "empty", fieldtype: "Empty" },
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
			const hadNoLayout = !parsed.layout
			layout.value = parsed.layout || getDefaultLayout()

			// Load page settings (already merged with defaults by parser)
			pageSettings.value = parsed.pageSettings || { ...defaultPageSettings }
			const qrSettings = ensureQrSettings(pageSettings.value)
			const parsedQrEnabled = (parsed.pageSettings as PageSettings | undefined)?.qr?.enabled
			if (typeof parsedQrEnabled !== "boolean") {
				qrSettings.enabled = false
			}

			// Load letterhead if specified
			if (pageSettings.value.letterhead) {
				letterhead.value = await resolveLetterheadDoc(pageSettings.value.letterhead)
			}

			// Auto-save if this was the first time (no layout_json in DB)
			if (hadNoLayout && layout.value) {
				await saveChanges()
			}
		} catch (error) {
			console.error("[Store] Failed to fetch Crispy Format:", error)
			frappe.throw(__("Failed to load Crispy Format"))
		} finally {
			loading.value = false
			// Use nextTick to ensure initializing flag persists through all queued watchers
			await nextTick()
			initializing.value = false
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
		// Don't mark dirty during initial load
		if (loading.value || initializing.value) {
			return
		}

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

	/**
	 * Set builder context from route options
	 */
	function setBuilderContext(context: Record<string, any> = {}) {
		builderContext.value = context
		console.log("[Store] Builder context set:", context)
	}

	/**
	 * Load report columns for Report mode
	 */
	async function loadReportColumns(reportName: string, filters: Record<string, any> = {}) {
		if (!reportName) {
			reportColumns.value = []
			return
		}

		try {
			console.log("[Store] Loading report columns for:", reportName)

			// Use frappe.call to fetch report columns
			const response = await frappe.call({
				method: "frappe.desk.query_report.run",
				args: {
					report_name: reportName,
					filters: filters,
					are_default_filters: 1,
					ignore_prepared_report: 1,
				},
			})

			const columns = response?.message?.columns || []
			console.log("[Store] Raw columns from API:", columns)

			// Normalize columns to match DocField structure
			reportColumns.value = columns.map((col: any) => {
				if (typeof col === "string") {
					// Parse string format: "Label:Type:Width"
					const parts = col.split(":")
					const label = parts[0] || ""
					const fieldtype = parts[1] || "Data"
					const fieldname = (typeof frappe !== "undefined" && typeof frappe.scrub === "function")
						? frappe.scrub(label)
						: label.toLowerCase().replace(/\s+/g, "_")

					return {
						label,
						fieldname,
						fieldtype,
					}
				}

				// Object format
				return {
					label: col.label || col.fieldname || "",
					fieldname: col.fieldname || (typeof frappe !== "undefined" && typeof frappe.scrub === "function"
						? frappe.scrub(col.label)
						: col.label?.toLowerCase().replace(/\s+/g, "_")) || "",
					fieldtype: col.fieldtype || "Data",
					width: col.width,
					options: col.options,
				}
			})

			console.log("[Store] Normalized report columns:", reportColumns.value)
		} catch (error) {
			console.error("[Store] Failed to load report columns:", error)
			reportColumns.value = []
		}
	}

	/**
	 * Load sample reports for generic template preview
	 */
	async function loadSampleReports() {
		try {
			console.log("[Store] Loading sample reports...")

			// Get generic report type from format (e.g., "Grid" or "Tree")
			const genericReportType = crispyFormat.value?.generic_report_type || null

			const response = await frappe.call({
				method: "crispy_print.api.get_reports_without_custom_html",
				args: {
					generic_report_type: genericReportType,
				},
			})

			sampleReports.value = response?.message || []
			console.log("[Store] Sample reports loaded:", sampleReports.value)
		} catch (error) {
			console.error("[Store] Failed to load sample reports:", error)
			sampleReports.value = []
		}
	}

	/**
	 * Build and compile report preview (reuses existing compile_typst)
	 */
	async function compileReportPreview(reportName: string, columnConfig: any[] = []) {
		try {
			console.log("[Store] Building report source:", reportName)

			// Step 1: Get Typst source
			const sourceResponse = await frappe.call({
				method: "crispy_print.api.get_report_typst_source",
				args: {
					report: reportName,
					format_name: formatName.value,
					filters: reportFilters.value || {},
					column_config: columnConfig,
					limit: 50,
				},
			})

			const typstSource = sourceResponse?.message
			if (!typstSource) {
				throw new Error("No Typst source returned")
			}

			console.log("[Store] Compiling to SVG...")

			// Step 2: Compile using existing endpoint (same as DocType mode)
			const compileResponse = await frappe.call({
				method: "crispy_print.api.compile_typst",
				args: {
					typst_source: typstSource,
					output_format: "svg",
				},
			})

			console.log("[Store] Compilation result:", compileResponse?.message)
			return compileResponse?.message || null
		} catch (error) {
			console.error("[Store] Failed to compile report preview:", error)
			throw error
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
		builderContext,
		layout,
		meta,
		fields,
		reportColumns,
		reportFilters,
		sampleReports,
		letterhead,
		pageSettings,
		dirty,
		loading,
		initializing,
		changeKey,

		// Computed
		formatName,
		docType,
		formatType,
		isReportMode,
		docHeader,
		docFooter,
		qrEnabled,
		typstPreamble,
		rawTypst,
		typstCode,

		// Methods
		fetch,
		saveChanges,
		markDirty,
		resetLayout,
		getDefaultLayout,
		setBuilderContext,
		loadReportColumns,
		loadSampleReports,
		compileReportPreview,
	}
	return store
}

export function useStore() {
	if (storeInstance !== null) {
		return storeInstance
	}
	storeInstance = buildStore()
	return storeInstance
}
