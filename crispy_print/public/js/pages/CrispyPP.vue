<template>
	<div class="crispy-preview-layout">
		<!-- Left Pane: Settings -->
		<div class="settings-pane">
			<div class="settings-pane__header">
				<div class="settings-pane__header-row">
					<h3 class="settings-pane__title">Print Settings</h3>
					<div class="settings-pane__spacer"></div>
					<div>
						<button
							type="button"
							class="settings-pane__help-btn"
							popovertarget="preview-settings-help"
							popovertargetaction="toggle"
							title="Toggle help"
						>
							?
						</button>
						<div id="preview-settings-help" popover class="settings-pane__help-popover">
							<ul class="settings-pane__help-list">
								<li>Configure page settings and document options.</li>
								<li>Changes apply immediately to the preview.</li>
							</ul>
						</div>
					</div>
				</div>
			</div>
			<div class="settings-pane__body">
				<div class="settings-pane__form">
				<!-- Print Format -->
				<div class="settings-pane__field">
					<label class="settings-pane__label">Print Format</label>
					<select v-model="selectedFormat" class="settings-pane__select" @change="onFormatChange">
						<option v-for="fmt in availableFormats" :key="fmt.name" :value="fmt.name">
							{{ fmt.name }}{{ fmt.is_default ? ' (Default)' : '' }}
						</option>
					</select>
				</div>

				<!-- Language -->
				<div class="settings-pane__field">
					<label class="settings-pane__label">Language</label>
					<select v-model="language" class="settings-pane__select">
						<option value="en">English</option>
						<option value="ar">Arabic</option>
						<option value="fr">French</option>
						<option value="de">German</option>
						<option value="es">Spanish</option>
					</select>
				</div>

				<!-- Letter Head -->
				<div class="settings-pane__field">
					<label class="settings-pane__label">Letter Head</label>
					<select v-model="letterhead" class="settings-pane__select">
						<option value="">None</option>
						<option v-for="lh in availableLetterheads" :key="lh" :value="lh">
							{{ lh }}
						</option>
					</select>
				</div>					<!-- Page Size -->
					<div class="settings-pane__field">
						<label class="settings-pane__label">Page Size</label>
						<select v-model="pageSize" class="settings-pane__select">
							<option value="A3">A3 (297 × 420 mm)</option>
							<option value="A4">A4 (210 × 297 mm)</option>
							<option value="A5">A5 (148 × 210 mm)</option>
							<option value="Letter">Letter (8.5 × 11 in)</option>
							<option value="Legal">Legal (8.5 × 14 in)</option>
						</select>
					</div>

					<!-- Orientation -->
					<div class="settings-pane__field">
						<label class="settings-pane__label">Orientation</label>
						<select v-model="orientation" class="settings-pane__select">
							<option value="portrait">Portrait</option>
							<option value="landscape">Landscape</option>
						</select>
					</div>

					<!-- Margins -->
					<div class="settings-pane__field">
						<label class="settings-pane__label">Margins (mm)</label>
						<div class="settings-pane__margins">
							<div class="settings-pane__margin-input">
								<span class="settings-pane__margin-prefix">T</span>
								<input
									v-model.number="margins.top"
									type="number"
									placeholder="Top"
									class="settings-pane__input"
								/>
							</div>
							<div class="settings-pane__margin-input">
								<span class="settings-pane__margin-prefix">B</span>
								<input
									v-model.number="margins.bottom"
									type="number"
									placeholder="Bottom"
									class="settings-pane__input"
								/>
							</div>
							<div class="settings-pane__margin-input">
								<span class="settings-pane__margin-prefix">L</span>
								<input
									v-model.number="margins.left"
									type="number"
									placeholder="Left"
									class="settings-pane__input"
								/>
							</div>
							<div class="settings-pane__margin-input">
								<span class="settings-pane__margin-prefix">R</span>
								<input
									v-model.number="margins.right"
									type="number"
									placeholder="Right"
									class="settings-pane__input"
								/>
							</div>
						</div>
					</div>
				</div>
			</div>
		</div>

		<!-- Right Pane: Preview -->
		<div class="preview-pane">
			<div class="preview-pane__body">
				<div id="typst-svg-container" class="typst-preview-container">
					<div class="preview-placeholder">
						Loading preview...
					</div>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from "vue"
import { 
	getFormatsForDoctype, 
	getDefaultFormat, 
	loadFormatData, 
	getLetterheads,
	getLetterheadData,
	type FormatInfo,
	type PageSettings 
} from "../utils/formatLoader"

declare const frappe: any
declare const __: any

const defaultPageSettings: PageSettings = {
	pageSize: "A4",
	orientation: "portrait",
	margins: { top: 25, bottom: 20, left: 20, right: 20 },
	fontFamily: "Arial",
	fontSize: 11,
	letterhead: "",
	typography: undefined,
	language: "en"
}

interface Props {
	doctype?: string
	docname?: string
	format?: string
}

const props = defineProps<Props>()

// Format selection
const availableFormats = ref<FormatInfo[]>([])
const availableLetterheads = ref<string[]>([])
const selectedFormat = ref<string>("")

// Settings state
const persistedPageSettings = ref<PageSettings>({ ...defaultPageSettings })
const language = ref("en")
const letterhead = ref("") // letterhead name
const letterheadData = ref<any>(null) // full letterhead document with image
const pageSize = ref("A4")
const orientation = ref("portrait")
const margins = ref({
	top: 25,
	bottom: 20,
	left: 20,
	right: 20
})

const layout = ref<any>(null)
const loading = ref(true)

// Initialize: Load available formats and letterheads
async function initializeData() {
	if (!props.doctype) {
		console.warn("[CrispyPP] No doctype specified")
		loading.value = false
		return
	}

	try {
		loading.value = true
		console.log("[CrispyPP] Initializing for doctype:", props.doctype)

		// Load available formats for this doctype
		const formats = await getFormatsForDoctype(props.doctype)
		
		// Check is_default flag for each format
		const formatsWithDefault = await Promise.all(
			formats.map(async (fmt) => {
				const isDefault = await frappe.db.get_value("Crispy Format", fmt.name, "is_default")
				return { ...fmt, is_default: isDefault.message.is_default }
			})
		)
		
		availableFormats.value = formatsWithDefault
		console.log("[CrispyPP] Available formats:", formatsWithDefault)

		// Load letterheads
		availableLetterheads.value = await getLetterheads()
		console.log("[CrispyPP] Available letterheads:", availableLetterheads.value)

		// Determine which format to use
		let formatToLoad = props.format
		
		if (!formatToLoad) {
			// No format specified, use default
			const defaultFormat = formatsWithDefault.find(f => f.is_default === 1)
			formatToLoad = defaultFormat?.name || formatsWithDefault[0]?.name
		}

		if (formatToLoad) {
			selectedFormat.value = formatToLoad
			await loadFormatSettings(formatToLoad)
		} else {
			console.warn("[CrispyPP] No formats available for doctype:", props.doctype)
			loading.value = false
		}
	} catch (error) {
		console.error("[CrispyPP] Error initializing:", error)
		frappe.show_alert({
			message: __("Failed to initialize preview: {0}", [error.message]),
			indicator: "red"
		})
		loading.value = false
	}
}

// Load settings for a specific format
async function loadFormatSettings(formatName: string) {
	try {
		loading.value = true
		console.log("[CrispyPP] Loading format:", formatName)

		const data = await loadFormatData(formatName)
		
		if (!data) {
			throw new Error("Failed to load format data")
		}

		// Apply persisted page settings (from the builder)
		persistedPageSettings.value = { ...defaultPageSettings, ...data.pageSettings }

		// Apply ephemeral controls from persisted settings
		pageSize.value = persistedPageSettings.value.pageSize
		orientation.value = persistedPageSettings.value.orientation
		margins.value = { ...persistedPageSettings.value.margins }
		letterhead.value = persistedPageSettings.value.letterhead || ""
		language.value = persistedPageSettings.value.language || "en"
		
		// Store layout
		layout.value = data.layout

		console.log("[CrispyPP] Loaded format settings:", data.pageSettings)
		console.log("[CrispyPP] Loaded layout:", data.layout)

		loading.value = false

		// Trigger initial render after data loaded
		setTimeout(() => triggerRefresh(), 200)
	} catch (error) {
		console.error("[CrispyPP] Error loading format settings:", error)
		frappe.show_alert({
			message: __("Failed to load format: {0}", [error.message]),
			indicator: "red"
		})
		loading.value = false
	}
}

// Handle format change
async function onFormatChange() {
	console.log("[CrispyPP] Format changed to:", selectedFormat.value)
	await loadFormatSettings(selectedFormat.value)
}

// Expose settings getters for external access
const getPageSettings = () => ({
	// Start from persisted builder settings so PP renders like PFB
	...persistedPageSettings.value,
	// Apply live overrides from PP controls
	pageSize: pageSize.value,
	orientation: orientation.value,
	margins: { ...margins.value },
	language: language.value,
	letterhead: letterhead.value,
	letterheadImage: letterheadData.value?.image || null  // Include image path for change detection
})

const getLayout = () => layout.value
const getLetterhead = () => {
	// Return the letterhead object with image path
	// setupWorker expects an object with .image property
	return letterheadData.value
}

// Expose refresh trigger
const triggerRefresh = () => {
	console.log("[CrispyPP] Triggering refresh with settings:", getPageSettings())
	window.dispatchEvent(new CustomEvent("crispy-refresh-preview", {
		detail: {
			settings: getPageSettings(),
			layout: getLayout(),
			doctype: props.doctype,
			docname: props.docname
		}
	}))
}

// Fetch letterhead data when letterhead selection changes
watch(letterhead, async (newLetterhead) => {
	if (newLetterhead) {
		letterheadData.value = await getLetterheadData(newLetterhead)
		console.log("[CrispyPP] Letterhead data loaded:", letterheadData.value)
		if (letterheadData.value?.image) {
			console.log("[CrispyPP] Letterhead image path:", letterheadData.value.image)
		} else {
			console.warn("[CrispyPP] Letterhead has no image field!")
		}
	} else {
		letterheadData.value = null
	}
	// Trigger refresh after letterhead data is loaded
	if (!loading.value) {
		triggerRefresh()
	}
})

// Watch for other settings changes and trigger refresh
watch([language, pageSize, orientation, margins], () => {
	console.log("[CrispyPP] Settings changed:", getPageSettings())
	if (!loading.value) {
		triggerRefresh()
	}
}, { deep: true })

onMounted(async () => {
	console.log("[CrispyPP] Mounted with props:", props)
	await initializeData()
})

// Expose methods for parent access
defineExpose({
	getPageSettings,
	getLayout,
	getLetterhead,
	triggerRefresh,
	loadFormatSettings,
	initializeData
})
</script>

<style scoped>
/* Layout */
.crispy-preview-layout {
	display: grid;
	grid-template-columns: 280px 1fr;
	gap: 0;
	background: #f8fafc;
	height: calc(100vh - 110px);
	min-height: 0;
}

/* Settings Pane */
.settings-pane {
	background: white;
	border-right: 1px solid #e5e7eb;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.settings-pane__header {
	padding: 16px;
	border-bottom: 1px solid #e5e7eb;
	flex-shrink: 0;
}

.settings-pane__header-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.settings-pane__title {
	margin: 0;
	font-size: 14px;
	font-weight: 600;
	color: #1f2937;
}

.settings-pane__spacer {
	flex: 1;
}

.settings-pane__help-btn {
	background: transparent;
	border: 1px solid #d1d5db;
	border-radius: 4px;
	width: 24px;
	height: 24px;
	display: flex;
	align-items: center;
	justify-content: center;
	cursor: pointer;
	font-size: 12px;
	color: #6b7280;
	transition: all 0.2s;
}

.settings-pane__help-btn:hover {
	background: #f3f4f6;
	color: #1f2937;
}

.settings-pane__help-popover {
	padding: 12px;
	border-radius: 6px;
	border: 1px solid #e5e7eb;
	background: white;
	box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.1);
	max-width: 300px;
}

.settings-pane__help-list {
	margin: 0;
	padding-left: 20px;
	font-size: 13px;
	color: #6b7280;
	line-height: 1.6;
}

.settings-pane__body {
	flex: 1;
	overflow-y: auto;
	padding: 16px;
}

.settings-pane__form {
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.settings-pane__field {
	display: flex;
	flex-direction: column;
	gap: 6px;
}

.settings-pane__label {
	font-size: 13px;
	font-weight: 500;
	color: #374151;
}

.settings-pane__input,
.settings-pane__select {
	width: 100%;
	padding: 6px 10px;
	border: 1px solid #d1d5db;
	border-radius: 4px;
	font-size: 13px;
	color: #1f2937;
	background: white;
	transition: border-color 0.2s;
}

.settings-pane__input:focus,
.settings-pane__select:focus {
	outline: none;
	border-color: #3b82f6;
}

.settings-pane__input--readonly {
	background: #f9fafb;
	color: #6b7280;
	cursor: not-allowed;
}

.settings-pane__select {
	cursor: pointer;
}

.settings-pane__margins {
	display: grid;
	grid-template-columns: 1fr 1fr;
	gap: 8px;
}

.settings-pane__margin-input {
	display: flex;
	align-items: center;
	gap: 4px;
}

.settings-pane__margin-prefix {
	font-size: 11px;
	font-weight: 600;
	color: #6b7280;
	width: 16px;
	text-align: center;
}

.settings-pane__margin-input .settings-pane__input {
	flex: 1;
}

/* Preview Pane */
.preview-pane {
	background: #f4f5f6;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.preview-pane__body {
	flex: 1;
	overflow-y: auto;
	padding: 20px;
}

.typst-preview-container {
	max-width: 900px;
	margin: 0 auto;
}

.preview-placeholder {
	background: white;
	border: 1px solid #d1d8dd;
	border-radius: 4px;
	padding: 60px 40px;
	text-align: center;
	color: #8d99a6;
	font-size: 14px;
	box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
}

/* Typst page styling (will be populated by setupWorker) */
:global(.typst-page) {
	margin-bottom: 1.5rem;
	box-shadow: 0 4px 12px rgba(148, 163, 184, 0.25), 0 2px 6px rgba(148, 163, 184, 0.2);
	background: white;
}

:global(.typst-page svg) {
	width: 100%;
	height: auto;
	display: block;
}
</style>
