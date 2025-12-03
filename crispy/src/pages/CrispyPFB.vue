<template>
	<div id="crispy-print-root" class="crispy-layout">
		<FieldsPane class="pane pane--fields" :fields="store.fields" :loading="store.loading" />
		<LayoutPane class="pane pane--layout" />
		<PreviewPane class="pane pane--preview" />
		<SettingsPane class="pane pane--settings" :page-settings="pageSettings" :mark-dirty="store.markDirty" />
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
	const route = frappe.get_route()

	if (route.length > 1) {
		await store.fetch(route[1])
	} else {
		console.log("[CrispyPFB] No format specified in route")
	}
})

// Watch for route changes
if (typeof frappe !== "undefined" && frappe?.router?.on) {
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
