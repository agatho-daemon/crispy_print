<template>
	<div class="typst-block-dialog">
		<div class="typst-block-dialog__card">
			<div class="typst-block-dialog__header">
				<div>
					<h3 class="typst-block-dialog__title">{{ __("Choose Typst block") }}</h3>
					<p class="typst-block-dialog__subtitle">
						{{ __("Select a saved Crispy Typst Block for this layout field.") }}
					</p>
				</div>
				<button class="typst-block-dialog__close" type="button" @click="$emit('close')">
					&#x2715;
				</button>
			</div>

			<div class="typst-block-dialog__body">
				<input
					v-model="searchQuery"
					type="text"
					class="form-control typst-block-dialog__search"
					:placeholder="__('Search blocks...')"
					autofocus
				/>

				<div v-if="loading" class="typst-block-dialog__empty">
					{{ __("Loading blocks...") }}
				</div>
				<div v-else-if="!filteredBlocks.length" class="typst-block-dialog__empty">
					{{ __("No matching blocks found.") }}
				</div>
				<div v-else class="typst-block-dialog__list">
					<button
						v-for="block in filteredBlocks"
						:key="block.block_key"
						type="button"
						class="typst-block-dialog__item"
						:class="{
							'typst-block-dialog__item--selected':
								block.block_key === selectedBlockKey,
						}"
						@click="$emit('select', block)"
					>
						<div class="typst-block-dialog__item-main">
							<span class="typst-block-dialog__item-name">{{
								block.block_name
							}}</span>
							<span class="typst-block-dialog__item-key">{{ block.block_key }}</span>
						</div>
						<div class="typst-block-dialog__item-meta">
							<span v-if="block.category">{{ block.category }}</span>
							<span v-if="block.version">v{{ block.version }}</span>
						</div>
						<p v-if="block.description" class="typst-block-dialog__description">
							{{ block.description }}
						</p>
					</button>
				</div>
			</div>

			<div class="typst-block-dialog__footer">
				<button class="btn btn-default btn-sm" type="button" @click="$emit('close')">
					{{ __("Close") }}
				</button>
			</div>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import type { CrispyTypstBlockOption } from "../api/crispy";
import { __ } from "../utils/i18n";

const props = defineProps<{
	blocks: CrispyTypstBlockOption[];
	loading?: boolean;
	selectedBlockKey?: string;
}>();

defineEmits<{
	(e: "select", block: CrispyTypstBlockOption): void;
	(e: "close"): void;
}>();

const searchQuery = ref("");

const filteredBlocks = computed(() => {
	const query = searchQuery.value.trim().toLowerCase();
	const blocks = props.blocks || [];
	if (!query) return blocks;
	return blocks.filter((block) => {
		return [
			block.block_name,
			block.block_key,
			block.category,
			block.description,
			block.version,
		].some((value) =>
			String(value || "")
				.toLowerCase()
				.includes(query)
		);
	});
});
</script>

<style scoped>
.typst-block-dialog {
	position: fixed;
	inset: 0;
	z-index: 1050;
	display: flex;
	align-items: center;
	justify-content: center;
	padding: 24px;
	background: rgba(15, 23, 42, 0.28);
}

.typst-block-dialog__card {
	width: min(680px, 100%);
	max-height: min(720px, 90vh);
	display: flex;
	flex-direction: column;
	border-radius: 8px;
	background: #fff;
	box-shadow: 0 18px 48px rgba(15, 23, 42, 0.22);
}

.typst-block-dialog__header,
.typst-block-dialog__footer {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 16px;
	padding: 16px;
	border-bottom: 1px solid #e2e8f0;
}

.typst-block-dialog__footer {
	justify-content: flex-end;
	border-top: 1px solid #e2e8f0;
	border-bottom: 0;
}

.typst-block-dialog__title {
	margin: 0;
	font-size: 16px;
	font-weight: 600;
}

.typst-block-dialog__subtitle {
	margin: 4px 0 0;
	color: #64748b;
	font-size: 13px;
}

.typst-block-dialog__close {
	border: 0;
	background: transparent;
	color: #64748b;
}

.typst-block-dialog__body {
	min-height: 0;
	padding: 16px;
	overflow: auto;
}

.typst-block-dialog__search {
	margin-bottom: 12px;
}

.typst-block-dialog__list {
	display: grid;
	gap: 8px;
}

.typst-block-dialog__item {
	width: 100%;
	border: 1px solid #e2e8f0;
	border-radius: 6px;
	padding: 10px 12px;
	background: #fff;
	text-align: start;
}

.typst-block-dialog__item:hover,
.typst-block-dialog__item--selected {
	border-color: #94a3b8;
	background: #f8fafc;
}

.typst-block-dialog__item-main,
.typst-block-dialog__item-meta {
	display: flex;
	align-items: center;
	gap: 8px;
}

.typst-block-dialog__item-main {
	justify-content: space-between;
}

.typst-block-dialog__item-name {
	color: #0f172a;
	font-weight: 600;
}

.typst-block-dialog__item-key,
.typst-block-dialog__item-meta,
.typst-block-dialog__description {
	color: #64748b;
	font-size: 12px;
}

.typst-block-dialog__description {
	margin: 6px 0 0;
	line-height: 1.4;
}

.typst-block-dialog__empty {
	padding: 20px;
	border: 1px dashed #cbd5e1;
	border-radius: 6px;
	color: #64748b;
	text-align: center;
}
</style>
