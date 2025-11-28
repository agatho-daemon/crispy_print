<template>
	<div
		class="grid h-32 gap-4 bg-slate-50 p-4 items-stretch"
		style="grid-template-columns: 280px minmax(0,1fr) minmax(0,1fr) 280px; min-height: 0; height: calc(100vh - 60px);"
	>
		<FieldsPane class="min-h-0 col-start-1" :fields="store.fields" :loading="store.loading" />
		<LayoutPane class="min-h-0 col-start-2" />
		<PreviewPane class="min-h-0 col-start-3" />
		<SettingsPane class="min-h-0 col-start-4" :page-settings="pageSettings" :mark-dirty="store.markDirty" />
	</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue"
import FieldsPane from "@/components/FieldsPane.vue"
import LayoutPane from "@/components/LayoutPane.vue"
import PreviewPane from "@/components/PreviewPane.vue"
import SettingsPane from "@/components/SettingsPane.vue"
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
</script>
