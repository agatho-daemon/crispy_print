<template>
	<div class="settings-pane">
		<div class="settings-pane__header">
			<div class="settings-pane__header-row">
				<h3 class="settings-pane__title">Typst Page Settings</h3>
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
				<div class="settings-pane__field">
					<label class="settings-pane__label">Page Size</label>
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

				<div class="settings-pane__field">
					<label class="settings-pane__label">Font Family</label>
					<select v-model="pageSettings.fontFamily" class="settings-pane__select">
						<option v-if="loadingFonts" disabled>Loading fonts...</option>
						<option v-for="font in availableFonts" :key="font" :value="font">{{ font }}</option>
					</select>
				</div>

				<div class="settings-pane__field">
					<label class="settings-pane__label">Font Size (pt)</label>
					<input v-model.number="pageSettings.fontSize" type="number" placeholder="11" class="settings-pane__input" />
				</div>

				<div class="settings-pane__field">
					<label class="settings-pane__label">Letterhead / Logo</label>
					<select v-model="pageSettings.letterhead" class="settings-pane__select">
						<option value="">None</option>
						<option v-if="loadingLetterheads" disabled>Loading letterheads...</option>
						<option v-for="letterhead in availableLetterheads" :key="letterhead" :value="letterhead">
							{{ letterhead }}
						</option>
					</select>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from "vue"

declare const frappe: any

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

interface Props {
	pageSettings: PageSettings
	markDirty: () => void
}

const props = defineProps<Props>()

const availableFonts = ref<string[]>([])
const loadingFonts = ref(false)
const availableLetterheads = ref<string[]>([])
const loadingLetterheads = ref(false)

// Fetch available fonts from Typst
async function fetchFonts() {
	if (typeof frappe === "undefined") {
		// Dev mode fallback
		availableFonts.value = ["Arial", "Helvetica", "Times New Roman", "Courier"]
		return
	}

	loadingFonts.value = true
	try {
		const response = await frappe.call({
			method: "crispy_print.api.get_typst_local_fonts",
		})
		availableFonts.value = response.message || []
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
		const response = await frappe.call({
			method: "frappe.client.get_list",
			args: {
				doctype: "Letter Head",
				fields: ["name"],
				filters: { disabled: 0 },
				order_by: "name asc",
			},
		})
		availableLetterheads.value = (response.message || []).map((lh: any) => lh.name)
	} catch (error) {
		console.error("[SettingsPane] Failed to fetch letterheads:", error)
		availableLetterheads.value = []
	} finally {
		loadingLetterheads.value = false
	}
}

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
	transition: background-color 0.2s ease, border-color 0.2s ease;
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
	gap: 6px;
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
	border-radius: 8px;
	background: #fff;
	outline: none;
	transition: border-color 0.15s ease, box-shadow 0.15s ease;
	box-sizing: border-box;
}

.settings-pane__select:focus,
.settings-pane__input:focus {
	border-color: #a5b4fc;
	box-shadow: 0 0 0 2px rgba(99, 102, 241, 0.2);
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

</style>