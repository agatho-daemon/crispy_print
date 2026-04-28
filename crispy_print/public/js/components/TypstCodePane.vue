<template>
	<div class="typst-code-pane">
		<div class="typst-code-pane__header">
			<div class="typst-code-pane__header-row">
				<h3 class="section-title typst-code-pane__title">{{ __("Typst Code") }}</h3>
				<div class="typst-code-pane__spacer"></div>
				<div>
					<button
						type="button"
						class="typst-code-pane__help-btn"
						popovertarget="typst-code-help"
						popovertargetaction="toggle"
						:title="__('Toggle help')"
						aria-haspopup="dialog"
						aria-controls="typst-code-help"
					>
						?
					</button>
					<div
						id="typst-code-help"
						popovertargetaction="toggle"
						popover
						class="typst-code-pane__help-popover"
					>
						<ul class="typst-code-pane__help-list">
							<li>
								{{
									__(
										"Raw Typst mode; drag fields into the editor to insert `#doc.fieldname`."
									)
								}}
							</li>
							<li>
								{{ __("Use Refresh in the preview pane to compile changes.") }}
							</li>
							<li>
								{{
									__(
										"Optional: add `// fields: customer, items.item_code` to narrow payload fields."
									)
								}}
							</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
		<div class="typst-code-pane__body">
			<textarea
				ref="editorRef"
				v-model="typstCode"
				:class="[
					'typst-code-pane__editor',
					{ 'typst-code-pane__editor--drag': isDragOver },
				]"
				spellcheck="false"
				:placeholder="
					__('Write Typst code here... (drag fields in to insert #doc.fieldname)')
				"
				@dragover.prevent="onDragOver"
				@dragleave="onDragLeave"
				@drop.prevent="onDrop"
			></textarea>
		</div>
	</div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useStore } from "../composables/useStore";
import { __ } from "../utils/i18n";

const store = useStore();
const editorRef = ref<HTMLTextAreaElement | null>(null);
const isDragOver = ref(false);

const typstCode = computed({
	get: () => store.typstCode.value,
	set: (value: string) => {
		store.typstCode.value = value;
	},
});

function insertSnippet(snippet: string) {
	const editor = editorRef.value;
	if (!editor) {
		typstCode.value = `${typstCode.value}${snippet}`;
		return;
	}

	const start = editor.selectionStart ?? editor.value.length;
	const end = editor.selectionEnd ?? editor.value.length;
	editor.setRangeText(snippet, start, end, "end");
	typstCode.value = editor.value;
	editor.focus();
}

function onDragOver() {
	isDragOver.value = true;
}

function onDragLeave() {
	isDragOver.value = false;
}

function onDrop(event: DragEvent) {
	isDragOver.value = false;
	if (!event.dataTransfer) return;
	const raw = event.dataTransfer.getData("application/json");
	let fieldname = "";
	if (raw) {
		try {
			const parsed = JSON.parse(raw);
			fieldname = parsed?.fieldname || "";
		} catch {
			fieldname = "";
		}
	}
	if (!fieldname) {
		fieldname = event.dataTransfer.getData("text/plain") || "";
	}
	if (!fieldname) return;
	insertSnippet(`#doc.${fieldname}`);
}
</script>

<style scoped>
.typst-code-pane {
	display: flex;
	flex-direction: column;
	border: 1px solid #e2e8f0;
	background: #fff;
	overflow: hidden;
}

.typst-code-pane__header {
	border-bottom: 1px solid #e2e8f0;
	padding: 12px 16px;
	background: rgba(255, 255, 255, 0.9);
}

.typst-code-pane__header-row {
	display: flex;
	align-items: center;
	gap: 12px;
}

.typst-code-pane__title {
	margin: 0;
}

.typst-code-pane__spacer {
	margin-left: auto;
}

.typst-code-pane__help-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	border-radius: 9999px;
	border: 1px solid transparent;
	background: transparent;
	color: #334155;
	font-size: 13px;
	font-weight: 500;
	cursor: pointer;
	box-shadow: none;
	transition: color 0.15s ease, font-size 0.15s ease, font-weight 0.15s ease;
}

.typst-code-pane__help-btn:hover,
.typst-code-pane__help-btn:focus-visible {
	border-color: transparent;
	background: transparent;
	color: #0f172a;
	font-size: 14px;
	font-weight: 700;
}

.typst-code-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	border: 1px solid #e0e7ff;
	background: #fff;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
	color: #334155;
	box-shadow: 0 10px 25px rgba(148, 163, 184, 0.25), 0 8px 10px rgba(148, 163, 184, 0.15);
}

.typst-code-pane__help-list {
	margin: 0;
	padding-left: 16px;
	display: grid;
	gap: 6px;
	list-style: disc;
}

.typst-code-pane__body {
	flex: 1;
	padding: 12px;
	background: #f8fafc;
}

.typst-code-pane__editor {
	width: 100%;
	height: 100%;
	border: 1px solid #e2e8f0;
	border-radius: 8px;
	padding: 12px;
	font-family: "SFMono-Regular", Menlo, Monaco, Consolas, "Liberation Mono", "Courier New",
		monospace;
	font-size: 12px;
	line-height: 1.5;
	color: #0f172a;
	background: #fff;
	resize: none;
}

.typst-code-pane__editor--drag {
	border-color: #60a5fa;
	box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.15);
	background: #f8fbff;
}
</style>
