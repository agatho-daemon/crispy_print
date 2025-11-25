<template>
	<div class="crispy-pfb-container">
		<!-- Column 1: DocType Fields Pane -->
		<FieldsPane :fields="store.fields" :loading="store.loading" />

		<!-- Column 2: Layout Builder Pane -->
		<LayoutPane class="builder-pane" />

		<!-- Column 3: Preview Pane -->
		<div class="preview-pane">
			<div class="pane-header">
				<h3 class="text-sm font-semibold text-gray-700 mb-2">Preview</h3>
			</div>
			<div class="preview-canvas">
				<p class="text-gray-500 text-sm">Live preview will appear here</p>
			</div>
		</div>

		<!-- Column 4: Settings Pane -->
		<div class="settings-pane">
			<div class="pane-header">
				<h3 class="text-sm font-semibold text-gray-700 mb-2">Typst Page Settings</h3>
			</div>
			<div class="settings-form">
				<div class="setting-group">
					<label class="setting-label">Page Size</label>
					<select v-model="pageSettings.pageSize" class="setting-input">
						<option value="A4">A4</option>
						<option value="Letter">Letter</option>
						<option value="Legal">Legal</option>
					</select>
				</div>

				<div class="setting-group">
					<label class="setting-label">Orientation</label>
					<select v-model="pageSettings.orientation" class="setting-input">
						<option value="portrait">Portrait</option>
						<option value="landscape">Landscape</option>
					</select>
				</div>

				<div class="setting-group">
					<label class="setting-label">Margins (mm)</label>
					<div class="grid grid-cols-2 gap-2">
						<input
							v-model.number="pageSettings.margins.top"
							type="number"
							placeholder="Top"
							class="setting-input"
						/>
						<input
							v-model.number="pageSettings.margins.bottom"
							type="number"
							placeholder="Bottom"
							class="setting-input"
						/>
						<input
							v-model.number="pageSettings.margins.left"
							type="number"
							placeholder="Left"
							class="setting-input"
						/>
						<input
							v-model.number="pageSettings.margins.right"
							type="number"
							placeholder="Right"
							class="setting-input"
						/>
					</div>
				</div>

				<div class="setting-group">
					<label class="setting-label">Font Family</label>
					<input
						v-model="pageSettings.fontFamily"
						type="text"
						placeholder="e.g., Arial, Helvetica"
						class="setting-input"
					/>
				</div>

				<div class="setting-group">
					<label class="setting-label">Font Size (pt)</label>
					<input
						v-model.number="pageSettings.fontSize"
						type="number"
						placeholder="11"
						class="setting-input"
					/>
				</div>

				<div class="setting-group">
					<label class="setting-label">Letterhead/Background</label>
					<select v-model="pageSettings.letterhead" class="setting-input">
						<option value="">None</option>
						<option value="default">Default Letterhead</option>
					</select>
				</div>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { onMounted, watch } from "vue"
import FieldsPane from "@/components/FieldsPane.vue"
import LayoutPane from "@/components/LayoutPane.vue"
import { useStore } from "@/composables/useStore"

const store = useStore()
const pageSettings = store.pageSettings

onMounted(async () => {
	// Guard for dev mode
	if (typeof frappe === "undefined") {
		console.log("[Dev Mode] Frappe not available - using mock data")
		return
	}

	const route = frappe.get_route()

	if (route.length > 1) {
		const formatName = route[1]
		console.log("[CrispyPFB] Loading format:", formatName)

		// Fetch format and fields via store
		await store.fetch(formatName)
	} else {
		console.log("[CrispyPFB] No format specified in route")
	}
})

// Watch for route changes
if (typeof frappe !== "undefined") {
	frappe.router.on("change", async () => {
		const route = frappe.get_route()
		if (route[0] === "crispy-print-builder" && route.length > 1) {
			const formatName = route[1]
			console.log("[CrispyPFB] Route changed, loading format:", formatName)
			await store.fetch(formatName)
		}
	})
}

// Mark dirty on settings change
watch(
	pageSettings,
	() => {
		store.markDirty()
	},
	{ deep: true }
)
</script>

<style scoped>
.crispy-pfb-container {
	display: grid;
	grid-template-columns: 280px minmax(0, 1fr) minmax(0, 1fr) 280px;
	gap: 16px;
	height: calc(100vh - 60px);
	padding: 16px;
	background-color: #f9fafb;
	align-items: stretch;
}

.crispy-pfb-container > * {
	min-height: 0;
}

.builder-pane,
.preview-pane,
.settings-pane {
	background: white;
	border: 1px solid #e5e7eb;
	border-radius: 8px;
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.pane-header {
	padding: 16px;
	border-bottom: 1px solid #e5e7eb;
}

.builder-canvas,
.preview-canvas {
	flex: 1;
	padding: 16px;
	overflow-y: auto;
}

.settings-form {
	flex: 1;
	padding: 16px;
	overflow-y: auto;
}

.setting-group {
	margin-bottom: 16px;
}

.setting-label {
	display: block;
	font-size: 13px;
	font-weight: 500;
	color: #374151;
	margin-bottom: 6px;
}

.setting-input {
	width: 100%;
	padding: 8px 12px;
	font-size: 13px;
	border: 1px solid #d1d5db;
	border-radius: 6px;
	background: white;
	transition: border-color 0.2s;
}

.setting-input:focus {
	outline: none;
	border-color: #3b82f6;
	box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.1);
}
</style>
