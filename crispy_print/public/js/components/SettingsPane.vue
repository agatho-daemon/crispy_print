<template>
	<div class="settings-pane">
		<div class="settings-pane__header">
			<div class="settings-pane__header-row">
				<h3 class="settings-pane__title">Typst Settings</h3>
				<div class="settings-pane__spacer"></div>
				<div>
					<button
						type="button"
						class="settings-pane__help-btn"
						popovertarget="settings-help"
						popovertargetaction="toggle"
						title="Toggle help"
					>
						?
					</button>
					<div id="settings-help" popover class="settings-pane__help-popover">
						<ul class="settings-pane__help-list">
							<li>Configure page size, margins, and typography for Typst.</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
		<div class="settings-pane__body">
			<div class="settings-pane__form">
				<div class="settings-pane__section-card">
					<button
						type="button"
						class="settings-pane__section-header"
						@click="isPageSettingsExpanded = !isPageSettingsExpanded"
					>
						<span>Page Settings</span>
						<svg
							:class="[
								'settings-pane__chevron',
								{ 'settings-pane__chevron--expanded': isPageSettingsExpanded },
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

					<div v-if="isPageSettingsExpanded" class="settings-pane__section-content">
						<div class="settings-pane__field">
							<label class="settings-pane__label">Size</label>
							<select v-model="pageSettings.pageSize" class="settings-pane__select">
								<option value="A3">A3 (297 × 420 mm)</option>
								<option value="A4">A4 (210 × 297 mm)</option>
								<option value="A5">A5 (148 × 210 mm)</option>
								<option value="Letter">Letter (8.5 × 11 in)</option>
								<option value="Legal">Legal (8.5 × 14 in)</option>
								<option value="Tabloid">Tabloid (11 × 17 in)</option>
								<option value="Executive">Executive (7.25 × 10.5 in)</option>
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
									<span class="settings-pane__margin-prefix">top</span>
									<input
										v-model.number="pageSettings.margins.top"
										type="number"
										placeholder="Top"
										class="settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">bottom</span>
									<input
										v-model.number="pageSettings.margins.bottom"
										type="number"
										placeholder="Bottom"
										class="settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">left</span>
									<input
										v-model.number="pageSettings.margins.left"
										type="number"
										placeholder="Left"
										class="settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">right</span>
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
				<div class="settings-pane__section-card">
					<button
						type="button"
						class="settings-pane__section-header"
						@click="isTypographyExpanded = !isTypographyExpanded"
					>
						<span>Typography</span>
						<svg
							:class="[
								'settings-pane__chevron',
								{ 'settings-pane__chevron--expanded': isTypographyExpanded },
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

					<div v-if="isTypographyExpanded" class="settings-pane__section-content">
						<!-- Section Labels -->
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Section Labels</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Family</label>
									<select
										v-model="typography.sectionLabel.fontFamily"
										class="settings-pane__select"
									>
										<option v-for="font in availableFonts" :key="font" :value="font">
											{{ font }}
										</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Size (pt)</label>
									<input
										v-model.number="sectionLabelFontSizePt"
										type="number"
										min="1"
										step="1"
										class="settings-pane__input"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Style</label>
									<select v-model="typography.sectionLabel.fontStyle" class="settings-pane__select">
										<option value="normal">Normal</option>
										<option value="italic">Italic</option>
										<option value="oblique">Oblique</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Weight</label>
									<select
										v-model="typography.sectionLabel.fontWeight"
										class="settings-pane__select"
									>
										<option value="thin">Thin</option>
										<option value="extralight">Extralight</option>
										<option value="light">Light</option>
										<option value="regular">Regular</option>
										<option value="medium">Medium</option>
										<option value="semibold">Semibold</option>
										<option value="bold">Bold</option>
										<option value="extrabold">Extrabold</option>
										<option value="black">Black</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Color</label>
									<ColorInput v-model="typography.sectionLabel.color" />
								</div>
							</div>
						</div>
						<!-- Field Labels -->
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Field Labels</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Family</label>
									<select v-model="typography.fieldLabel.fontFamily" class="settings-pane__select">
										<option v-for="font in availableFonts" :key="font" :value="font">
											{{ font }}
										</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Size (pt)</label>
									<input
										v-model.number="fieldLabelFontSizePt"
										type="number"
										min="1"
										step="1"
										class="settings-pane__input"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Style</label>
									<select v-model="typography.fieldLabel.fontStyle" class="settings-pane__select">
										<option value="normal">Normal</option>
										<option value="italic">Italic</option>
										<option value="oblique">Oblique</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Weight</label>
									<select v-model="typography.fieldLabel.fontWeight" class="settings-pane__select">
										<option value="thin">Thin</option>
										<option value="extralight">Extralight</option>
										<option value="light">Light</option>
										<option value="regular">Regular</option>
										<option value="medium">Medium</option>
										<option value="semibold">Semibold</option>
										<option value="bold">Bold</option>
										<option value="extrabold">Extrabold</option>
										<option value="black">Black</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Color</label>
									<ColorInput v-model="typography.fieldLabel.color" />
								</div>
							</div>
						</div>
						<!-- Field Values -->
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Field Values</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Family</label>
									<select v-model="typography.fieldValue.fontFamily" class="settings-pane__select">
										<option v-for="font in availableFonts" :key="font" :value="font">
											{{ font }}
										</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Size (pt)</label>
									<input
										v-model.number="fieldValueFontSizePt"
										type="number"
										min="1"
										step="1"
										class="settings-pane__input"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Style</label>
									<select v-model="typography.fieldValue.fontStyle" class="settings-pane__select">
										<option value="normal">Normal</option>
										<option value="italic">Italic</option>
										<option value="oblique">Oblique</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Weight</label>
									<select v-model="typography.fieldValue.fontWeight" class="settings-pane__select">
										<option value="thin">Thin</option>
										<option value="extralight">Extralight</option>
										<option value="light">Light</option>
										<option value="regular">Regular</option>
										<option value="medium">Medium</option>
										<option value="semibold">Semibold</option>
										<option value="bold">Bold</option>
										<option value="extrabold">Extrabold</option>
										<option value="black">Black</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Color</label>
									<ColorInput v-model="typography.fieldValue.color" />
								</div>
							</div>
						</div>
					</div>
				</div>

				<div class="settings-pane__field">
					<label class="settings-pane__label">Letterhead / Logo</label>
					<select v-model="pageSettings.letterhead" class="settings-pane__select">
						<option value="">None</option>
						<option v-if="loadingLetterheads" disabled>Loading letterheads...</option>
						<option
							v-for="letterhead in availableLetterheads"
							:key="letterhead"
							:value="letterhead"
						>
							{{ letterhead }}
						</option>
					</select>
				</div>
				<div class="settings-pane__field settings-pane__field--inline">
					<label class="settings-pane__label">Remove QRCode</label>
					<input v-model="store.removeQr.value" type="checkbox" class="settings-pane__checkbox" />
				</div>
			</div>
		</div>
	</div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, computed } from "vue"
import { ensureTypography, type PageSettings, type TypographySettings } from "../utils/pageSettings"
import ColorInput from "./ColorInput.vue"
import { getLetterheads, getTypstLocalFonts } from "../api/crispy"
import { useStore } from "../composables/useStore"

interface Props {
	pageSettings: PageSettings
	markDirty: () => void
}

const props = defineProps<Props>()

const availableFonts = ref<string[]>([])
const loadingFonts = ref(false)
const availableLetterheads = ref<string[]>([])
const loadingLetterheads = ref(false)
const isPageSettingsExpanded = ref(false)
const isTypographyExpanded = ref(false)
const store = useStore()

// Initialize typography with defaults if not present
const typography = computed<TypographySettings>(() => {
	return ensureTypography(props.pageSettings)
})

// Fetch available fonts from Typst
async function fetchFonts() {
	if (typeof frappe === "undefined") {
		// Dev mode fallback
		availableFonts.value = ["Arial", "Helvetica", "Times New Roman", "Courier"]
		return
	}

	loadingFonts.value = true
	try {
		availableFonts.value = await getTypstLocalFonts()
	} catch (error) {
		console.error("[SettingsPane] Failed to fetch fonts:", error)
		// Fallback fonts
		availableFonts.value = ["Arial", "Helvetica", "Times New Roman"]
	} finally {
		loadingFonts.value = false
	}
}

// Fetch available letterheads
async function fetchLetterheads() {
	if (typeof frappe === "undefined") {
		// Dev mode fallback
		availableLetterheads.value = []
		return
	}

	loadingLetterheads.value = true
	try {
		availableLetterheads.value = await getLetterheads()
	} catch (error) {
		console.error("[SettingsPane] Failed to fetch letterheads:", error)
		availableLetterheads.value = []
	} finally {
		loadingLetterheads.value = false
	}
}

function parseSize(input: string | null | undefined): {
	value: number
	unit: string
	decimals: number
} {
	const raw = String(input || "").trim()
	const match = raw.match(/^([0-9]+(?:\.[0-9]+)?)\s*([a-z%]+)?$/i)
	if (!match) return { value: 0, unit: "pt", decimals: 0 }
	const value = Number(match[1])
	const unit = (match[2] || "pt").toLowerCase()
	const decimals = (match[1].split(".")[1] || "").length
	return { value: Number.isFinite(value) ? value : 0, unit, decimals }
}

function formatPt(value: number): string {
	const safe = Math.max(1, value)
	const num = safe.toFixed(2).replace(/\.?0+$/, "")
	return `${num}pt`
}

const sectionLabelFontSizePt = computed<number>({
	get: () => Math.max(1, parseSize(typography.value.sectionLabel.fontSize).value || 0),
	set: (value) => {
		typography.value.sectionLabel.fontSize = formatPt(value)
	},
})

const fieldLabelFontSizePt = computed<number>({
	get: () => Math.max(1, parseSize(typography.value.fieldLabel.fontSize).value || 0),
	set: (value) => {
		typography.value.fieldLabel.fontSize = formatPt(value)
	},
})

const fieldValueFontSizePt = computed<number>({
	get: () => Math.max(1, parseSize(typography.value.fieldValue.fontSize).value || 0),
	set: (value) => {
		typography.value.fieldValue.fontSize = formatPt(value)
	},
})

onMounted(() => {
	fetchFonts()
	fetchLetterheads()
})

watch(
	() => props.pageSettings,
	() => props.markDirty(),
	{ deep: true }
)
</script>

<style scoped>
/* SettingsPane.vue */
.settings-pane {
	background: #fff;
	border: 1px solid #e2e8f0;
	display: flex;
	flex-direction: column;
	overflow-y: auto;
}

.settings-pane__header {
	border-bottom: 1px solid #e2e8f0;
	padding: 12px;
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
	color: #1e293b;
}

.settings-pane__spacer {
	margin-left: auto;
}

.settings-pane__help-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	border-radius: 9999px;
	border: 1px solid #e2e8f0;
	background: #fff;
	color: #4f46e5;
	font-size: 14px;
	font-weight: 600;
	cursor: pointer;
	transition:
		background-color 0.2s ease,
		border-color 0.2s ease;
}

.settings-pane__help-btn:hover {
	background: #eef2ff;
	border-color: #c7d2fe;
}

.settings-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	border: 1px solid #e0e7ff;
	background: #fff;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
	color: #334155;
	box-shadow:
		0 10px 25px rgba(148, 163, 184, 0.25),
		0 8px 10px rgba(148, 163, 184, 0.15);
}

.settings-pane__help-list {
	margin: 0;
	padding-left: 16px;
	display: grid;
	gap: 6px;
	list-style: disc;
}

.settings-pane__body {
	flex: 1;
	overflow-y: auto;
	padding: 12px 16px;
}

.settings-pane__form {
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.settings-pane__field {
	display: flex;
	flex-direction: column;
	gap: 0px;
}

.settings-pane__field--inline {
	flex-direction: row;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
}

.settings-pane__label {
	font-size: 13px;
	font-weight: 600;
	color: #334155;
}

.settings-pane__select,
.settings-pane__input {
	width: 100%;
	padding: 8px 12px;
	font-size: 14px;
	color: #0f172a;
	border: 1px solid #e2e8f0;
	border-radius: 3px;
	background: #fff;
	outline: none;
	transition:
		border-color 0.15s ease,
		box-shadow 0.15s ease;
	box-sizing: border-box;
}

.settings-pane__select:focus,
.settings-pane__input:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
}

.settings-pane__checkbox {
	width: 16px;
	height: 16px;
	accent-color: #4f46e5;
}

.settings-pane__margins {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 8px;
}

.settings-pane__margin-input {
	position: relative;
}

.settings-pane__margin-prefix {
	position: absolute;
	left: 10px;
	top: 50%;
	transform: translateY(-50%);
	font-size: 10px;
	font-weight: 600;
	color: #94a3b8;
	pointer-events: none;
}

.settings-pane__margin-input .settings-pane__input {
	padding-left: 50px;
}

.settings-pane__section {
	display: flex;
	flex-direction: column;
	gap: 16px;
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
	/* transform-origin: right center; */
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

.settings-pane__subsection {
	display: flex;
	flex-direction: column;
	gap: 8px;
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
</style>
