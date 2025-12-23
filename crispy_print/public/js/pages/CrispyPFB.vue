<template>
	<div id="crispy-print-root" class="crispy-layout">
		<FieldsPane class="pane pane--fields" :fields="store.fields" :loading="store.loading" />
		<LayoutPane class="pane pane--layout" />
		<PreviewPane class="pane pane--preview" />
		<SettingsPane
			class="pane pane--settings"
			:page-settings="pageSettings"
			:mark-dirty="store.markDirty"
		/>
	</div>
</template>

<script setup lang="ts">
import { onMounted } from "vue"
import FieldsPane from "../components/FieldsPane.vue"
import LayoutPane from "../components/LayoutPane.vue"
import PreviewPane from "../components/PreviewPane.vue"
import SettingsPane from "../components/SettingsPane.vue"
import { useStore } from "../composables/useStore"
import { getCrispyBuilderFormatName } from "../utils/routes"

const store = useStore()
const pageSettings = store.pageSettings

onMounted(async () => {
	const formatName = getCrispyBuilderFormatName()
	if (formatName) await store.fetch(formatName)
})

// Watch for route changes
if (typeof frappe !== "undefined" && frappe?.router?.on) {
	frappe.router.on("change", async () => {
		const formatName = getCrispyBuilderFormatName()
		if (formatName) await store.fetch(formatName)
	})
}
</script>

<style scoped>
/* CrispyPFB.vue */
.crispy-layout {
	display: grid;
	grid-template-columns: 280px minmax(0, 1fr) minmax(0, 1fr) 280px;
	gap: 16px;
	background: #f8fafc;
	padding: 16px;
	align-items: stretch;
	min-height: 0;
	height: calc(100vh - 60px);
}

.pane {
	min-height: 0;
}

.pane--fields {
	grid-column-start: 1;
}

.pane--layout {
	grid-column-start: 2;
}

.pane--preview {
	grid-column-start: 3;
}

.pane--settings {
	grid-column-start: 4;
}
</style>
