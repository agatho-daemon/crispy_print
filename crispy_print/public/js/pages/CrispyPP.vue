<template>
	<div class="crispy-preview-layout">
		<!-- Left Pane: Settings -->
		<div class="settings-pane">
			<div class="settings-pane__header">
				<div class="settings-pane__header-row">
					<h3 class="settings-pane__title">Print Settings</h3>
					<div class="settings-pane__spacer"></div>
					<button
						type="button"
						class="settings-pane__reset-btn"
						@click="resetFormat"
						title="Reset to saved format"
					>
						Reset
					</button>
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
								{{ fmt.name }}{{ fmt.is_default ? " (Default)" : "" }}
							</option>
						</select>
					</div>

					<div class="settings-pane__section-card">
						<button
							type="button"
							class="settings-pane__section-header"
							@click="isOverridesExpanded = !isOverridesExpanded"
						>
							<span>Preview Overrides</span>
							<svg
								:class="[
									'settings-pane__chevron',
									{ 'settings-pane__chevron--expanded': isOverridesExpanded },
								]"
								xmlns="http://www.w3.org/2000/svg"
								viewBox="0 0 20 20"
								fill="currentColor"
							>
								<path
									fill-rule="evenodd"
									d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
									clip-rule="evenodd"
								/>
							</svg>
						</button>
						<div v-if="isOverridesExpanded" class="settings-pane__section-content">
							<p class="settings-pane__hint">
								Preview-only changes. The saved format is unchanged.
							</p>

							<div class="settings-pane__field">
								<label class="settings-pane__label">Language</label>
								<select v-model="pageSettings.language" class="settings-pane__select">
									<option value="en">English</option>
									<option value="ar">Arabic</option>
									<option value="fr">French</option>
									<option value="de">German</option>
									<option value="es">Spanish</option>
								</select>
							</div>

							<div class="settings-pane__field">
								<label class="settings-pane__label">Branding</label>
								<select v-model="brandingMode" class="settings-pane__select">
									<option value="none">None</option>
									<option value="letterhead">Letterhead</option>
									<option value="logo">Logo</option>
								</select>
							</div>

							<div v-if="brandingMode === 'letterhead'" class="settings-pane__field">
								<label class="settings-pane__label">Letter Head</label>
								<select v-model="pageSettings.letterhead" class="settings-pane__select">
									<option value="">None</option>
									<option v-if="loadingLetterheads" disabled>Loading letterheads...</option>
									<option v-for="lh in availableLetterheads" :key="lh" :value="lh">
										{{ lh }}
									</option>
								</select>
							</div>

							<div v-if="brandingMode === 'logo'">
								<p class="settings-pane__hint">Logo is anchored to top-left using #place().</p>
								<div class="settings-pane__field">
									<label class="settings-pane__label">Company</label>
									<select v-model="logoSettings.company" class="settings-pane__select">
										<option value="">Select company</option>
										<option v-if="loadingCompanies" disabled>Loading companies...</option>
										<option
											v-for="company in availableCompanies"
											:key="company.name"
											:value="company.name"
										>
											{{ company.abbr ? `${company.abbr} - ${company.name}` : company.name }}
										</option>
									</select>
								</div>
								<p v-if="logoSettings.company && !logoSettings.image" class="settings-pane__hint">
									Selected company has no logo set.
								</p>
								<div class="settings-pane__grid">
									<div class="settings-pane__field">
										<label class="settings-pane__sublabel">Size (mm)</label>
										<input
											v-model.number="logoSettings.size"
											type="number"
											class="settings-pane__input"
										/>
									</div>
									<div class="settings-pane__field">
										<label class="settings-pane__sublabel">dx (mm)</label>
										<input
											v-model.number="logoSettings.dx"
											type="number"
											class="settings-pane__input"
										/>
									</div>
									<div class="settings-pane__field">
										<label class="settings-pane__sublabel">dy (mm)</label>
										<input
											v-model.number="logoSettings.dy"
											type="number"
											class="settings-pane__input"
										/>
									</div>
								</div>
							</div>

							<div class="settings-pane__field settings-pane__field--inline">
								<label class="settings-pane__label">Remove QRCode</label>
								<input v-model="removeQr" type="checkbox" class="settings-pane__checkbox" />
							</div>

							<div class="settings-pane__field">
								<label class="settings-pane__label">Page Size</label>
								<select v-model="pageSettings.pageSize" class="settings-pane__select">
									<option value="A3">A3 (297 × 420 mm)</option>
									<option value="A4">A4 (210 × 297 mm)</option>
									<option value="A5">A5 (148 × 210 mm)</option>
									<option value="Letter">Letter (8.5 × 11 in)</option>
									<option value="Legal">Legal (8.5 × 14 in)</option>
								</select>
							</div>

							<div class="settings-pane__field">
								<label class="settings-pane__label">Orientation</label>
								<select v-model="pageSettings.orientation" class="settings-pane__select">
									<option value="portrait">Portrait</option>
									<option value="landscape">Landscape</option>
								</select>
							</div>

							<div class="settings-pane__field">
								<label class="settings-pane__label">Margins (mm)</label>
								<div class="settings-pane__margins">
									<div class="settings-pane__margin-input">
										<span class="settings-pane__margin-prefix">T</span>
										<input
											v-model.number="pageSettings.margins.top"
											type="number"
											placeholder="Top"
											class="settings-pane__input"
										/>
									</div>
									<div class="settings-pane__margin-input">
										<span class="settings-pane__margin-prefix">B</span>
										<input
											v-model.number="pageSettings.margins.bottom"
											type="number"
											placeholder="Bottom"
											class="settings-pane__input"
										/>
									</div>
									<div class="settings-pane__margin-input">
										<span class="settings-pane__margin-prefix">L</span>
										<input
											v-model.number="pageSettings.margins.left"
											type="number"
											placeholder="Left"
											class="settings-pane__input"
										/>
									</div>
									<div class="settings-pane__margin-input">
										<span class="settings-pane__margin-prefix">R</span>
										<input
											v-model.number="pageSettings.margins.right"
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
			</div>
		</div>

		<!-- Right Pane: Preview -->
		<PreviewRenderer
			:format-name="selectedFormat"
			:layout="layout"
			:doc-header="docHeader"
			:doc-footer="docFooter"
			:typst-preamble="typstPreamble"
			:typst-code="typstCode"
			:raw-typst="rawTypst"
			:qr-enabled="qrEnabledEffective"
			:letterhead="letterheadDoc"
			:doc-type="props.doctype || null"
			:doc-name="props.docname || null"
			:page-settings="pageSettingsComputed"
			:change-key="changeKey"
			:watch-data-changes="true"
		/>
	</div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch, computed } from "vue"
import {
	getFormatsForDoctype,
	loadFormatData,
	getLetterheads,
	loadLetterheadDoc,
	type FormatInfo,
} from "../utils/formatLoader"
import { getCompanies, type CompanyOption } from "../api/crispy"
import { defaultPageSettings, ensureLogoSettings, type PageSettings } from "../utils/pageSettings"
import PreviewRenderer from "../components/PreviewRenderer.vue"
import { pickFormatName } from "../utils/formatSelection"

interface Props {
	doctype?: string
	docname?: string
	format?: string
}

const props = defineProps<Props>()

// Format selection
const availableFormats = ref<FormatInfo[]>([])
const availableLetterheads = ref<string[]>([])
const loadingLetterheads = ref(false)
const availableCompanies = ref<CompanyOption[]>([])
const loadingCompanies = ref(false)
const selectedFormat = ref<string>("")

// Settings state (single in-memory copy; PP does not persist)
const pageSettings = ref<PageSettings>({ ...defaultPageSettings })

const layout = ref<any>(null)
const loading = ref(true)
const docHeader = ref("")
const docFooter = ref("")
const typstPreamble = ref("")
const typstCode = ref("")
const rawTypst = ref(false)
const qrEnabled = ref(false)
const removeQr = ref(false)
const letterheadDoc = ref<any | null>(null)
const changeKey = ref(0)
const OVERRIDES_STORAGE_KEY = "crispy-print:pp:preview-overrides-expanded"
const isOverridesExpanded = ref(false)
const qrEnabledEffective = computed(() => qrEnabled.value && !removeQr.value)
const logoSettings = computed(() => ensureLogoSettings(pageSettings.value))

const brandingMode = computed<string>({
	get: () => {
		const mode = pageSettings.value.brandingMode
		if (mode === "letterhead" || mode === "logo" || mode === "none") {
			return mode
		}
		if (pageSettings.value.logo?.company || pageSettings.value.logo?.image) {
			return "logo"
		}
		if (pageSettings.value.letterhead) {
			return "letterhead"
		}
		return "none"
	},
	set: (value) => {
		pageSettings.value.brandingMode = value as "letterhead" | "logo" | "none"
	},
})

// Explicit invalidation for preview recompilation (avoids deep watches inside PreviewRenderer).
watch(
	() => [
		layout.value,
		pageSettings.value,
		letterheadDoc.value,
		docHeader.value,
		docFooter.value,
		typstPreamble.value,
		typstCode.value,
		rawTypst.value,
		qrEnabled.value,
		removeQr.value,
	],
	() => {
		changeKey.value++
	},
	{ deep: true }
)

// Initialize: Load available formats and letterheads
async function initializeData() {
	if (!props.doctype) {
		console.warn("[CrispyPP] No doctype specified")
		loading.value = false
		return
	}

	try {
		loading.value = true

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

		await fetchLetterheads()
		await fetchCompanies()

		// Determine which format to use
		const formatToLoad = pickFormatName(formatsWithDefault, props.format || null)

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
			indicator: "red",
		})
		loading.value = false
	}
}

// Load settings for a specific format
async function loadFormatSettings(formatName: string) {
	try {
		loading.value = true

		const data = await loadFormatData(formatName)

		if (!data) {
			throw new Error("Failed to load format data")
		}

		// Overwrite in-memory page settings (ephemeral)
		pageSettings.value = data.pageSettings || { ...defaultPageSettings }

		// Preload letterhead data if the format has one set
		if (pageSettings.value.letterhead) {
			letterheadDoc.value = await loadLetterheadDoc(pageSettings.value.letterhead)
		} else {
			letterheadDoc.value = null
		}

		// Store layout
		layout.value = data.layout
		docHeader.value = data.formatDoc.doc_header || ""
		docFooter.value = data.formatDoc.doc_footer || ""
		typstPreamble.value = data.formatDoc.typst_preamble || ""
		typstCode.value = data.formatDoc.typst_code || ""
		rawTypst.value = Boolean(data.formatDoc.raw_typst)
		qrEnabled.value = Boolean(data.formatDoc.qrcode)

		loading.value = false
	} catch (error) {
		console.error("[CrispyPP] Error loading format settings:", error)
		frappe.show_alert({
			message: __("Failed to load format: {0}", [error.message]),
			indicator: "red",
		})
		loading.value = false
	}
}

function resolveCompanyLogo(companyName: string): string {
	if (!companyName) return ""
	const match = availableCompanies.value.find((company) => company.name === companyName)
	return match?.company_logo || ""
}

async function fetchLetterheads() {
	loadingLetterheads.value = true
	try {
		availableLetterheads.value = await getLetterheads()
	} catch (error) {
		console.error("[CrispyPP] Failed to fetch letterheads:", error)
		availableLetterheads.value = []
	} finally {
		loadingLetterheads.value = false
	}
}

async function fetchCompanies() {
	if (typeof frappe === "undefined") {
		availableCompanies.value = []
		return
	}

	loadingCompanies.value = true
	try {
		availableCompanies.value = await getCompanies()
	} catch (error) {
		console.error("[CrispyPP] Failed to fetch companies:", error)
		availableCompanies.value = []
	} finally {
		loadingCompanies.value = false
	}
}

// Handle format change
async function onFormatChange() {
	await loadFormatSettings(selectedFormat.value)
}

async function resetFormat() {
	if (!selectedFormat.value) return
	await loadFormatSettings(selectedFormat.value)
}

// Expose settings getters for external access
const getPageSettings = () => ({
	...pageSettings.value,
	letterheadImage: letterheadDoc.value?.image || null, // Include image path for change detection
})

const pageSettingsComputed = computed(() => getPageSettings())

function triggerRefresh() {
	// Manual refresh (refetch + recompile) for crispy-print page.
	window.dispatchEvent(new CustomEvent("crispy-preview:refresh"))
}

const getLayout = () => layout.value
const getLetterhead = () => {
	// Return the letterhead object with image path
	// setupWorker expects an object with .image property
	return letterheadDoc.value
}

// Fetch letterhead data when letterhead selection changes
watch(
	() => pageSettings.value.letterhead,
	async (newLetterhead) => {
		if (newLetterhead) {
			letterheadDoc.value = await loadLetterheadDoc(newLetterhead)
		} else {
			letterheadDoc.value = null
		}
	}
)

watch(
	() => logoSettings.value.company,
	(newCompany) => {
		logoSettings.value.image = resolveCompanyLogo(newCompany)
	}
)

watch(availableCompanies, () => {
	if (!logoSettings.value.company) return
	logoSettings.value.image = resolveCompanyLogo(logoSettings.value.company)
})

// No explicit preview events needed: PreviewRenderer/setupWorker reacts to prop changes directly.

onMounted(async () => {
	if (typeof window !== "undefined") {
		const stored = window.localStorage.getItem(OVERRIDES_STORAGE_KEY)
		if (stored !== null) {
			isOverridesExpanded.value = stored === "true"
		}
	}
	await initializeData()
})

watch(isOverridesExpanded, (next) => {
	if (typeof window === "undefined") return
	window.localStorage.setItem(OVERRIDES_STORAGE_KEY, String(next))
})

// Generate and open PDF in new tab
async function generatePDF() {
	window.dispatchEvent(
		new CustomEvent("crispy-preview:request-pdf", { detail: { action: "view" } })
	)
}

async function downloadPDF() {
	window.dispatchEvent(
		new CustomEvent("crispy-preview:request-pdf", { detail: { action: "download" } })
	)
}

// Simple readiness check: we consider Typst ready if a prior compile set code in worker
function lastTypstReady() {
	// We can't read lastTypstCode from worker here; rely on layout present and prior refresh
	return Boolean(layout.value)
}

// Expose methods for parent access
defineExpose({
	getPageSettings,
	getLayout,
	getLetterhead,
	loadFormatSettings,
	initializeData,
	generatePDF,
	downloadPDF,
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

.settings-pane__reset-btn {
	background: #f3f4f6;
	border: 1px solid #d1d5db;
	border-radius: 4px;
	padding: 4px 8px;
	margin-right: 8px;
	cursor: pointer;
	font-size: 12px;
	color: #1f2937;
	transition: all 0.2s;
}

.settings-pane__reset-btn:hover {
	background: #e5e7eb;
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

.settings-pane__field--inline {
	flex-direction: row;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
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

.settings-pane__checkbox {
	width: 16px;
	height: 16px;
	accent-color: #2563eb;
}

.settings-pane__hint {
	margin: 0;
	font-size: 12px;
	color: #64748b;
}

.settings-pane__input--readonly {
	background: #f9fafb;
	color: #6b7280;
	cursor: not-allowed;
}

.settings-pane__select {
	cursor: pointer;
}

.settings-pane__section-card {
	background: #f8fafc;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	overflow: hidden;
}

.settings-pane__section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	margin: 0;
	padding: 10px 12px;
	font-size: 13px;
	font-weight: 700;
	color: #1e293b;
	text-transform: uppercase;
	letter-spacing: 0.5px;
	background: transparent;
	border: none;
	cursor: pointer;
}

.settings-pane__chevron {
	width: 16px;
	height: 16px;
	transition: transform 0.2s ease;
}

.settings-pane__chevron--expanded {
	transform: rotate(-180deg);
}

.settings-pane__section-content {
	display: flex;
	flex-direction: column;
	gap: 12px;
	padding: 12px 12px 14px;
	background: #f8fafc;
	border-top: 1px solid #e2e8f0;
}

.settings-pane__grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 8px;
}

.settings-pane__sublabel {
	font-size: 11px;
	font-weight: 500;
	color: #64748b;
	margin-bottom: 0px;
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
	box-shadow:
		0 4px 12px rgba(148, 163, 184, 0.25),
		0 2px 6px rgba(148, 163, 184, 0.2);
	background: white;
}

:global(.typst-page svg) {
	width: 100%;
	height: auto;
	display: block;
}
</style>
