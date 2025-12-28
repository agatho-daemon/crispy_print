<template>
	<div class="qr-dialog">
		<div class="qr-dialog__card">
			<div class="qr-dialog__header">
				<div>
					<h3 class="qr-dialog__title">QR Code Fields</h3>
					<p class="qr-dialog__subtitle">Choose fields to include in the QR payload.</p>
				</div>
				<button class="qr-dialog__close" type="button" @click="$emit('close')">&#x2715;</button>
			</div>
			<div class="qr-dialog__body">
				<div class="qr-dialog__search">
					<input
						v-model="query"
						type="text"
						class="qr-dialog__input"
						placeholder="Search fields..."
					/>
				</div>
				<div class="qr-dialog__list">
					<label v-for="field in filteredFields" :key="field.fieldname" class="qr-dialog__item">
						<input
							v-model="localSelection"
							class="qr-dialog__checkbox"
							type="checkbox"
							:value="field.fieldname"
						/>
						<span class="qr-dialog__label">
							{{ field.label || field.fieldname }}
						</span>
					</label>
				</div>
				<p v-if="!filteredFields.length" class="qr-dialog__empty">No fields found.</p>
			</div>
			<div class="qr-dialog__footer">
				<button class="qr-dialog__btn" type="button" @click="$emit('close')">Cancel</button>
				<button class="qr-dialog__btn qr-dialog__btn--primary" type="button" @click="apply">
					Apply
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue"
import type { DocField } from "../utils/layout"

interface Props {
	fields: DocField[]
	modelValue: string[]
}

const props = defineProps<Props>()
const emit = defineEmits<{
	(e: "update:modelValue", value: string[]): void
	(e: "close"): void
}>()

const query = ref("")
const localSelection = ref<string[]>([...(props.modelValue || [])])

watch(
	() => props.modelValue,
	(value) => {
		localSelection.value = [...(value || [])]
	}
)

const virtualFields: DocField[] = [
	{
		fieldname: "timestamp",
		label: "Posting Timestamp",
		fieldtype: "Datetime",
	},
]

const filteredFields = computed(() => {
	const term = query.value.trim().toLowerCase()
	const allowFieldnames = new Set([
		"name",
		"company",
		"company_name",
		"customer",
		"customer_name",
		"supplier",
		"supplier_name",
		"tax_id",
		"vat",
		"gst",
		"tin",
		"trn",
		"timestamp",
		"due_date",
		"currency",
		"conversion_rate",
		"net_total",
		"base_net_total",
		"total",
		"base_total",
		"grand_total",
		"base_grand_total",
		"total_taxes_and_charges",
		"base_total_taxes_and_charges",
		"rounded_total",
		"base_rounded_total",
		"return_against",
		"is_return",
	])
	return [...virtualFields, ...(props.fields || [])]
		.filter((field) => field.fieldname && allowFieldnames.has(field.fieldname))
		.filter((field) => {
			if (!term) return true
			const label = (field.label || "").toLowerCase()
			return label.includes(term) || field.fieldname.toLowerCase().includes(term)
		})
})

const apply = () => {
	emit("update:modelValue", [...localSelection.value])
	emit("close")
}
</script>

<style scoped>
.qr-dialog {
	position: fixed;
	inset: 0;
	background: rgba(15, 23, 42, 0.4);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 2000;
}

.qr-dialog__card {
	width: min(520px, 90vw);
	max-height: 80vh;
	background: #fff;
	border-radius: 12px;
	border: 1px solid #e2e8f0;
	box-shadow:
		0 20px 40px rgba(15, 23, 42, 0.2),
		0 8px 16px rgba(15, 23, 42, 0.12);
	display: flex;
	flex-direction: column;
	overflow: hidden;
}

.qr-dialog__header {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 12px;
	padding: 16px;
	border-bottom: 1px solid #e2e8f0;
}

.qr-dialog__title {
	margin: 0;
	font-size: 16px;
	font-weight: 700;
	color: #0f172a;
}

.qr-dialog__subtitle {
	margin: 6px 0 0;
	font-size: 12px;
	color: #64748b;
}

.qr-dialog__close {
	border: none;
	background: transparent;
	font-size: 18px;
	cursor: pointer;
	color: #64748b;
}

.qr-dialog__body {
	padding: 16px;
	overflow: auto;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.qr-dialog__search {
	display: flex;
}

.qr-dialog__input {
	width: 100%;
	padding: 8px 10px;
	border-radius: 8px;
	border: 1px solid #e2e8f0;
	font-size: 13px;
}

.qr-dialog__list {
	display: grid;
	grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
	column-gap: 24px;
	row-gap: 12px;
}

.qr-dialog__item {
	display: flex;
	align-items: center;
	gap: 10px;
	padding: 2px 0;
}

.qr-dialog__checkbox {
	width: 14px;
	height: 14px;
	accent-color: #4f46e5;
}

.qr-dialog__label {
	font-size: 13px;
	color: #0f172a;
	font-weight: 500;
}

.qr-dialog__empty {
	font-size: 12px;
	color: #94a3b8;
}

.qr-dialog__footer {
	border-top: 1px solid #e2e8f0;
	padding: 12px 16px;
	display: flex;
	justify-content: flex-end;
	gap: 8px;
}

.qr-dialog__btn {
	padding: 6px 12px;
	border-radius: 8px;
	border: 1px solid #e2e8f0;
	background: #fff;
	font-size: 13px;
	cursor: pointer;
	color: #1e293b;
}

.qr-dialog__btn--primary {
	background: #4f46e5;
	border-color: #4f46e5;
	color: #fff;
}
</style>
