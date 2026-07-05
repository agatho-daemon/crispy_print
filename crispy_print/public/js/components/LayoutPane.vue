<template>
	<div ref="layoutPaneRef" class="layout-pane">
		<div class="section-head layout-pane__header">
			<div class="section-head-content layout-pane__header-row">
				<div class="layout-pane__title-wrap">
					<h3 class="section-title layout-pane__title">{{ __("Layout Builder") }}</h3>
					<span
						v-if="showGenericReportTypeBadge"
						class="layout-pane__generic-type-badge"
					>
						Generic Type: {{ genericReportTypeLabel }}
					</span>
				</div>
				<div class="layout-pane__controls">
					<button
						class="btn btn-default btn-sm"
						:disabled="!store.canUndo.value"
						:title="__('Undo (Ctrl/Cmd+Z)')"
						@click="store.undo()"
					>
						{{ __("Undo") }}
					</button>
					<button
						class="btn btn-default btn-sm"
						:disabled="!store.canRedo.value"
						:title="__('Redo (Ctrl/Cmd+Y)')"
						@click="store.redo()"
					>
						{{ __("Redo") }}
					</button>
					<button class="btn btn-default btn-sm" @click="resetLayout">
						{{ __("Reset to Default") }}
					</button>
					<div class="layout-pane__spacer"></div>
					<div class="layout-pane__help">
						<button
							type="button"
							class="btn btn-default btn-xs layout-pane__help-btn"
							popovertarget="layout-help"
							popovertargetaction="toggle"
							:title="__('Toggle help')"
							aria-haspopup="dialog"
							aria-controls="layout-help"
						>
							?
						</button>
						<div id="layout-help" popover class="layout-pane__help-popover">
							<ul class="layout-pane__help-list">
								<li>{{ __("Drag fields from Fields pane into columns.") }}</li>
								<li>
									{{
										__(
											"Use handles to reorder sections, columns, and fields in place."
										)
									}}
								</li>
								<li>
									{{
										__(
											"Use the ⋯ menu on a section for add/remove/page break/orientation."
										)
									}}
								</li>
							</ul>
						</div>
					</div>
				</div>
			</div>
			<div v-if="isReportFormat" class="layout-pane__report-selector-row">
				<div class="layout-pane__report-selector-wrap">
					<span class="layout-pane__preview-note">
						{{ __("Style preview mode: layout uses deterministic sample data.") }}
					</span>
				</div>
			</div>
		</div>
		<div v-if="!layout" class="layout-pane__empty">
			{{ __("No layout loaded.") }}
			<button class="btn btn-link btn-sm" @click="ensureLayout">
				{{ __("Load default") }}
			</button>
		</div>

		<div v-else class="layout-pane__body">
			<draggable
				v-model="layout.sections"
				:item-key="sectionKey"
				handle=".section-grip"
				:animation="200"
				class="layout-pane__sections"
			>
				<template #item="{ element: section, index: sectionIndex }">
					<div class="section-card">
						<div class="section-card__header">
							<div class="section-card__title-row">
								<span class="section-grip" :title="__('Drag section')"
									>&#8942;</span
								>
								<input
									v-model="section.label"
									type="text"
									class="form-control section-title-input"
									:placeholder="__('Section title')"
								/>
							</div>
							<div class="section-card__actions">
								<button
									type="button"
									class="section-card__menu-btn"
									:title="__('Section menu')"
									@click.stop="toggleSectionMenu(section, sectionIndex, $event)"
									aria-haspopup="menu"
									:aria-expanded="
										openSectionMenuId ===
										getSectionMenuId(section, sectionIndex)
									"
									:aria-controls="`section-menu-${getSectionMenuId(
										section,
										sectionIndex
									)}`"
								>
									&#8943;
								</button>
								<teleport to="body">
									<div
										v-if="
											openSectionMenuId ===
											getSectionMenuId(section, sectionIndex)
										"
										:id="`section-menu-${getSectionMenuId(
											section,
											sectionIndex
										)}`"
										:ref="setSectionMenuRef"
										class="section-card__menu"
										:style="sectionMenuStyle"
										@click.stop
										role="menu"
										tabindex="-1"
										@keydown="onSectionMenuKeydown"
									>
										<button
											type="button"
											class="section-card__menu-item"
											@click="onAddSectionAbove(sectionIndex)"
											role="menuitem"
										>
											{{ __("Add section above") }}
										</button>
										<button
											type="button"
											class="section-card__menu-item"
											@click="onAddSectionBelow(sectionIndex)"
											role="menuitem"
										>
											{{ __("Add section below") }}
										</button>
										<div
											class="section-card__menu-divider"
											role="separator"
										></div>
										<button
											type="button"
											class="section-card__menu-item"
											:disabled="section.columns.length >= 4"
											@click="onAddColumn(section)"
											role="menuitem"
										>
											{{ __("Add column") }}
										</button>
										<button
											type="button"
											class="section-card__menu-item"
											:disabled="section.columns.length <= 1"
											@click="onRemoveLastColumn(section)"
											role="menuitem"
										>
											{{ __("Remove column") }}
										</button>
										<div
											class="section-card__menu-divider"
											role="separator"
										></div>
										<button
											type="button"
											class="section-card__menu-item"
											@click="onOpenSectionSettings(section)"
											role="menuitem"
										>
											{{ __("Section settings") }}
										</button>
										<button
											type="button"
											class="section-card__menu-item"
											@click="onTogglePageBreak(section)"
											role="menuitem"
										>
											{{
												section.page_break
													? __("Remove page break")
													: __("Add page break")
											}}
										</button>
										<button
											type="button"
											class="section-card__menu-item"
											@click="onToggleFieldOrientation(section)"
											role="menuitem"
										>
											{{ __("Field orientation") }} ({{
												getFieldOrientationLabel(section)
											}})
										</button>
										<div
											class="section-card__menu-divider"
											role="separator"
										></div>
										<button
											type="button"
											class="section-card__menu-item section-card__menu-item--danger"
											@click="onRemoveSection(sectionIndex)"
											role="menuitem"
										>
											{{ __("Remove section") }}
										</button>
									</div>
								</teleport>
							</div>
						</div>

						<div class="section-grid" :style="gridStyle(section)">
							<div
								v-for="(column, colIndex) in section.columns"
								:key="column.id || colIndex"
								:class="[
									'section-column',
									{ 'section-column--empty': !column.fields.length },
								]"
								@dragover.prevent
								@drop="onDropField($event, column)"
							>
								<draggable
									v-model="column.fields"
									group="layout-fields"
									item-key="id"
									handle=".field-grip"
									:animation="150"
									class="section-column__fields"
								>
									<template #item="{ element: field, index: fieldIndex }">
										<div class="field-card">
											<div class="field-card__row">
												<div class="field-card__info">
													<span
														class="field-grip"
														:title="__('Drag field')"
													>
														&#8942;
													</span>
													<input
														v-model="field.label"
														type="text"
														:class="[
															'form-control field-card__label field-card__label-input',
															{
																'field-card__label-input--with-status':
																	field.fieldtype ===
																		'Crispy Typst Block' ||
																	isCrispyImageField(field),
															},
														]"
														:placeholder="field.fieldname"
														@change="markDirty()"
														@keydown.enter.prevent="onLabelEnter"
													/>
													<span
														v-if="
															field.fieldtype ===
																'Crispy Typst Block' ||
															isCrispyImageField(field)
														"
														class="field-card__inline-status"
														:class="{
															'field-card__inline-status--empty':
																field.fieldtype ===
																'Crispy Typst Block'
																	? !field.crispy_typst_block
																	: !field.crispy_image,
														}"
														:title="
															field.fieldtype ===
															'Crispy Typst Block'
																? getTypstBlockStatus(field)
																: getImageStatus(field)
														"
													>
														<span
															class="field-card__inline-separator"
															aria-hidden="true"
															>·</span
														>
														<span
															class="field-card__inline-status-text"
														>
															{{
																field.fieldtype ===
																"Crispy Typst Block"
																	? getTypstBlockStatus(field)
																	: getImageStatus(field)
															}}
														</span>
													</span>
												</div>
												<div class="field-card__actions">
													<button
														type="button"
														class="field-card__menu-btn"
														:title="__('Field menu')"
														@click.stop="
															toggleFieldMenu(
																getFieldMenuId(
																	section,
																	column,
																	field,
																	colIndex
																),
																$event
															)
														"
														aria-haspopup="menu"
														:aria-expanded="
															openFieldMenuId ===
															getFieldMenuId(
																section,
																column,
																field,
																colIndex
															)
														"
														:aria-controls="`field-menu-${getFieldMenuId(
															section,
															column,
															field,
															colIndex
														)}`"
													>
														&#8943;
													</button>
													<teleport to="body">
														<div
															v-if="
																openFieldMenuId ===
																getFieldMenuId(
																	section,
																	column,
																	field,
																	colIndex
																)
															"
															:id="`field-menu-${getFieldMenuId(
																section,
																column,
																field,
																colIndex
															)}`"
															:ref="setFieldMenuRef"
															class="field-card__menu"
															:style="fieldMenuStyle"
															@click.stop
															role="menu"
															tabindex="-1"
															@keydown="onFieldMenuKeydown"
														>
															<button
																type="button"
																class="field-card__menu-item"
																@click="toggleAlignSubmenu"
																:ref="setAlignMenuItemRef"
																role="menuitem"
																aria-haspopup="menu"
																:aria-expanded="
																	openFieldSubmenu === 'align'
																"
															>
																{{ __("Align") }}
																<span
																	class="field-card__menu-arrow"
																	>›</span
																>
															</button>
															<div
																v-if="openFieldSubmenu === 'align'"
																class="field-card__submenu"
																:style="alignSubmenuStyle"
																@click.stop
																:ref="setAlignSubmenuRef"
																role="menu"
																:aria-label="
																	__('Alignment options')
																"
																tabindex="-1"
																@keydown="onAlignSubmenuKeydown"
															>
																<button
																	type="button"
																	class="field-card__menu-item"
																	@click="
																		setAlignment(field, 'left')
																	"
																	role="menuitemradio"
																	:aria-checked="
																		getFieldAlign(field) ===
																		'left'
																	"
																>
																	<span
																		class="field-card__menu-check"
																		>{{
																			getFieldAlign(
																				field
																			) === "left"
																				? "✓"
																				: ""
																		}}</span
																	>
																	{{ __("Left") }}
																</button>
																<button
																	type="button"
																	class="field-card__menu-item"
																	@click="
																		setAlignment(
																			field,
																			'center'
																		)
																	"
																	role="menuitemradio"
																	:aria-checked="
																		getFieldAlign(field) ===
																		'center'
																	"
																>
																	<span
																		class="field-card__menu-check"
																		>{{
																			getFieldAlign(
																				field
																			) === "center"
																				? "✓"
																				: ""
																		}}</span
																	>
																	{{ __("Center") }}
																</button>
																<button
																	type="button"
																	class="field-card__menu-item"
																	@click="
																		setAlignment(
																			field,
																			'right'
																		)
																	"
																	role="menuitemradio"
																	:aria-checked="
																		getFieldAlign(field) ===
																		'right'
																	"
																>
																	<span
																		class="field-card__menu-check"
																		>{{
																			getFieldAlign(
																				field
																			) === "right"
																				? "✓"
																				: ""
																		}}</span
																	>
																	{{ __("Right") }}
																</button>
															</div>

															<button
																type="button"
																class="field-card__menu-item"
																@click="onToggleFieldLabel(field)"
																role="menuitem"
															>
																{{
																	(field.label ?? "").trim()
																		? __("Hide label")
																		: __("Show label")
																}}
															</button>

															<button
																v-if="field.fieldtype === 'Table'"
																type="button"
																class="field-card__menu-item"
																@click="onConfigureColumns(field)"
																role="menuitem"
															>
																{{ __("Configure columns") }}
															</button>

															<button
																v-if="
																	(
																		field.fieldtype || ''
																	).toLowerCase() === 'typst'
																"
																type="button"
																class="field-card__menu-item"
																@click="onEditTypstCode(field)"
																role="menuitem"
															>
																{{ __("Edit code") }}
															</button>

															<button
																v-if="
																	field.fieldtype ===
																	'Crispy Typst Block'
																"
																type="button"
																class="field-card__menu-item"
																@click="onChooseTypstBlock(field)"
																role="menuitem"
															>
																{{ __("Choose block") }}
															</button>

															<button
																v-if="isCrispyImageField(field)"
																type="button"
																class="field-card__menu-item"
																@click="onChooseImage(field)"
																role="menuitem"
															>
																{{ __("Choose image") }}
															</button>

															<button
																v-if="
																	(
																		field.fieldtype || ''
																	).toLowerCase() === 'spacer'
																"
																type="button"
																class="field-card__menu-item"
																@click="onEditSpacer(field)"
																role="menuitem"
															>
																{{ __("Configure spacer") }}
															</button>

															<button
																v-if="
																	(
																		field.fieldtype || ''
																	).toLowerCase() === 'divider'
																"
																type="button"
																class="field-card__menu-item"
																@click="onEditDivider(field)"
																role="menuitem"
															>
																{{ __("Configure divider") }}
															</button>

															<div
																class="field-card__menu-divider"
																role="separator"
															></div>

															<button
																type="button"
																class="field-card__menu-item field-card__menu-item--danger"
																@click="
																	onRemoveField(
																		column,
																		fieldIndex
																	)
																"
																role="menuitem"
															>
																{{ __("Remove") }}
															</button>
														</div>
													</teleport>
												</div>
											</div>
											<div
												v-if="
													field.fieldtype === 'Table' &&
													field.table_columns?.length
												"
												class="field-card__columns"
											>
												<div
													v-for="col in field.table_columns"
													:key="col.fieldname"
													class="field-card__column-pill"
													:title="
														__('Width: {0}%', [col.width ?? 'auto'])
													"
												>
													{{ col.label }}
												</div>
											</div>
										</div>
									</template>
								</draggable>

								<div v-if="!column.fields.length" class="section-column__empty">
									{{ __("Drop fields here") }}
								</div>
							</div>
						</div>

						<div v-if="section.page_break" class="section-page-break">
							{{ __("Page Break") }}
						</div>
					</div>
				</template>
			</draggable>
		</div>
		<TableColumnsDialog
			v-if="columnEditor"
			:model-value="editingColumns"
			:doctype="columnEditor.field.options || ''"
			:available-columns="columnEditorAvailableColumns"
			@update:modelValue="onColumnsUpdate"
			@close="closeColumnEditor"
		/>
		<CrispyTypstBlockDialog
			v-if="blockEditor"
			:blocks="blockOptions"
			:loading="blockOptionsLoading"
			:selected-block-key="blockEditor.crispy_typst_block"
			@select="onTypstBlockSelected"
			@close="closeBlockEditor"
		/>
		<CrispyImageDialog
			v-if="imageEditor"
			:selected-filename="imageEditor.crispy_image"
			:settings="getImageEditorSettings(imageEditor)"
			@select="onImageSelected"
			@close="closeImageEditor"
		/>
	</div>
</template>

<script setup lang="ts">
import draggable from "vuedraggable";
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useStore } from "../composables/useStore";
import TableColumnsDialog from "../components/TableColumnsDialog.vue";
import CrispyTypstBlockDialog from "../components/CrispyTypstBlockDialog.vue";
import CrispyImageDialog, { type CrispyImageSettings } from "../components/CrispyImageDialog.vue";
import { getLogger } from "../logger";
import type { CrispyTypstBlockOption } from "../api/crispy";
import type {
	LayoutSection,
	LayoutColumn,
	LayoutField,
	DocField,
	TableColumn,
} from "../utils/layout";
import { createLayoutId, getTableColumns } from "../utils/layout";
import { getDefaultAlignment } from "../utils/tableColumns";
import { deepClone } from "../utils/json";
import { __ } from "../utils/i18n";

type Section = LayoutSection & {
	id?: string | number;
	page_break?: boolean;
	field_orientation?: "left-right" | "top-down";
};
type Column = LayoutColumn;
type Field = LayoutField;
type TableEditorContext = {
	field: Field;
};

const store = useStore();
const layout = store.layout;
const columnEditor = ref<TableEditorContext | null>(null);
const editingColumns = ref<TableColumn[]>([]);
const blockEditor = ref<Field | null>(null);
const blockOptions = ref<CrispyTypstBlockOption[]>([]);
const blockOptionsLoading = ref(false);
const imageEditor = ref<Field | null>(null);
const logger = getLogger({ component: "LayoutPane" });
const layoutPaneRef = ref<HTMLElement | null>(null);
const sectionMenuEl = ref<HTMLElement | null>(null);
const fieldMenuEl = ref<HTMLElement | null>(null);
const alignMenuItemEl = ref<HTMLElement | null>(null);
const alignSubmenuEl = ref<HTMLElement | null>(null);
const sectionMenuAnchorEl = ref<HTMLElement | null>(null);
const fieldMenuAnchorEl = ref<HTMLElement | null>(null);

const setSectionMenuRef = (el: HTMLElement | null) => {
	if (el) sectionMenuEl.value = el;
};

const setFieldMenuRef = (el: HTMLElement | null) => {
	if (el) fieldMenuEl.value = el;
};

const setAlignMenuItemRef = (el: HTMLElement | null) => {
	if (el) alignMenuItemEl.value = el;
};

const setAlignSubmenuRef = (el: HTMLElement | null) => {
	if (el) alignSubmenuEl.value = el;
};

const openSectionMenuId = ref<string | null>(null);
const sectionMenuStyle = ref<Record<string, string>>({});

const openFieldMenuId = ref<string | null>(null);
const fieldMenuStyle = ref<Record<string, string>>({});
const alignSubmenuStyle = ref<Record<string, string>>({});
const openFieldSubmenu = ref<"align" | null>(null);
const currentFormat = computed(() => store.crispyFormat?.value || null);
const showGenericReportTypeBadge = computed(() => {
	const format = currentFormat.value;
	return (
		format?.crispy_format_type === "Report" &&
		Number(format?.is_generic || 0) === 1 &&
		Boolean(format?.generic_report_type)
	);
});
const genericReportTypeLabel = computed(() =>
	String(currentFormat.value?.generic_report_type || "").trim()
);
const isReportFormat = computed(() => currentFormat.value?.crispy_format_type === "Report");
const columnEditorAvailableColumns = computed(() => {
	if (!columnEditor.value) return [];
	if (!isReportFormat.value) return [];
	const fieldname = columnEditor.value.field.fieldname;
	if (fieldname === "data.table") {
		return (store.reportColumns.value || []).map((col: any) => ({
			label: col.label || col.fieldname || "",
			fieldname: col.fieldname || "",
			fieldtype: col.fieldtype || "Data",
		}));
	}
	if (fieldname === "data.filters") {
		const options = (store.reportFilterFields?.value || []).map((df: any) => ({
			label: df.label || df.fieldname || "",
			fieldname: df.fieldname || "",
			fieldtype: df.fieldtype || "Data",
		}));
		if (options.length > 0) return options;
		return [
			{ label: __("Label"), fieldname: "label", fieldtype: "Data" },
			{ label: __("Value"), fieldname: "value", fieldtype: "Data" },
		];
	}
	if (fieldname === "data.report_summary") {
		return [
			{ label: __("Label"), fieldname: "label", fieldtype: "Data" },
			{ label: __("Value"), fieldname: "value", fieldtype: "Data" },
			{ label: __("Indicator"), fieldname: "indicator", fieldtype: "Data" },
			{ label: __("Data Type"), fieldname: "datatype", fieldtype: "Data" },
			{ label: __("Currency"), fieldname: "currency", fieldtype: "Data" },
		];
	}
	return [];
});

function clamp(value: number, min: number, max: number) {
	return Math.min(Math.max(value, min), max);
}

type FloatingPlacement = "bottom-end" | "right-start";

function getFloatingMenuPosition(
	anchor: HTMLElement,
	menu: HTMLElement,
	placement: FloatingPlacement = "bottom-end"
) {
	const anchorRect = anchor.getBoundingClientRect();
	const menuRect = menu.getBoundingClientRect();
	const padding = 8;
	const gap = 6;
	const viewportWidth = window.innerWidth || document.documentElement.clientWidth;
	const viewportHeight = window.innerHeight || document.documentElement.clientHeight;
	const maxLeft = viewportWidth - menuRect.width - padding;
	const maxTop = viewportHeight - menuRect.height - padding;
	let left = 0;
	let top = 0;

	if (placement === "right-start") {
		left = anchorRect.right + gap;
		top = anchorRect.top;
		if (left > maxLeft) {
			left = anchorRect.left - menuRect.width - gap;
		}
	} else {
		left = anchorRect.right - menuRect.width;
		top = anchorRect.bottom + gap;
		if (top > maxTop) {
			top = anchorRect.top - menuRect.height - gap;
		}
	}

	left = clamp(left, padding, Math.max(padding, maxLeft));
	top = clamp(top, padding, Math.max(padding, maxTop));

	return {
		position: "fixed",
		top: `${top}px`,
		left: `${left}px`,
		zIndex: "1200",
	};
}

function updateFloatingMenuPositions() {
	if (openSectionMenuId.value && sectionMenuAnchorEl.value && sectionMenuEl.value) {
		sectionMenuStyle.value = getFloatingMenuPosition(
			sectionMenuAnchorEl.value,
			sectionMenuEl.value
		);
	}
	if (openFieldMenuId.value && fieldMenuAnchorEl.value && fieldMenuEl.value) {
		fieldMenuStyle.value = getFloatingMenuPosition(fieldMenuAnchorEl.value, fieldMenuEl.value);
	}
	if (openFieldSubmenu.value === "align" && alignMenuItemEl.value && alignSubmenuEl.value) {
		alignSubmenuStyle.value = getFloatingMenuPosition(
			alignMenuItemEl.value,
			alignSubmenuEl.value,
			"right-start"
		);
	}
}

function getMenuItems(menuEl: HTMLElement, includeSubmenu = true) {
	const items = Array.from(menuEl.querySelectorAll<HTMLButtonElement>("button:not([disabled])"));
	if (includeSubmenu) return items;
	return items.filter((item) => !item.closest(".field-card__submenu"));
}

function focusMenuItem(menuEl: HTMLElement, index: number, includeSubmenu = true) {
	const items = getMenuItems(menuEl, includeSubmenu);
	if (!items.length) return;
	const safeIndex = Math.max(0, Math.min(items.length - 1, index));
	items[safeIndex]?.focus();
}

function focusFirstMenuItem(menuEl: HTMLElement, includeSubmenu = true) {
	focusMenuItem(menuEl, 0, includeSubmenu);
}

function handleMenuKeydown(
	event: KeyboardEvent,
	menuEl: HTMLElement,
	options?: { includeSubmenu?: boolean; onEscape?: () => void }
) {
	const includeSubmenu = options?.includeSubmenu ?? true;
	const items = getMenuItems(menuEl, includeSubmenu);
	if (!items.length) return;

	const active = document.activeElement as HTMLElement | null;
	let index = items.findIndex((item) => item === active);
	if (index < 0) index = 0;

	switch (event.key) {
		case "ArrowDown":
			event.preventDefault();
			focusMenuItem(menuEl, index + 1, includeSubmenu);
			break;
		case "ArrowUp":
			event.preventDefault();
			focusMenuItem(menuEl, index - 1, includeSubmenu);
			break;
		case "Home":
			event.preventDefault();
			focusMenuItem(menuEl, 0, includeSubmenu);
			break;
		case "End":
			event.preventDefault();
			focusMenuItem(menuEl, items.length - 1, includeSubmenu);
			break;
		case "Enter":
		case " ":
			if (active && active.tagName === "BUTTON") {
				event.preventDefault();
				(active as HTMLButtonElement).click();
			}
			break;
		case "Escape":
			event.preventDefault();
			options?.onEscape?.();
			break;
	}
}

const sectionKey = (section: Section, index: number) => {
	return (section as any).id || index;
};

function ensureSectionIds() {
	if (!layout.value?.sections?.length) return;
	const seen = new Set<string | number>();
	layout.value.sections.forEach((section) => {
		const currentId = (section as any).id;
		if (!currentId || seen.has(currentId)) {
			(section as any).id = createLayoutId();
		}
		seen.add((section as any).id);
	});
}

function ensureColumnIds(section: Section) {
	const seen = new Set<string | number>();
	section.columns.forEach((column: Column) => {
		const currentId = (column as any).id;
		if (!currentId || seen.has(currentId)) {
			(column as any).id = createLayoutId();
		}
		seen.add((column as any).id);
	});
}

function ensureFieldIds(column: Column) {
	const seen = new Set<string | number>();
	column.fields.forEach((field: Field) => {
		const currentId = (field as any).id;
		if (!currentId || seen.has(currentId)) {
			(field as any).id = createLayoutId();
		}
		seen.add((field as any).id);
	});
}

function ensureLayoutIds() {
	if (!layout.value?.sections?.length) return;
	ensureSectionIds();
	layout.value.sections.forEach((section) => {
		ensureColumnIds(section);
		section.columns.forEach((column) => ensureFieldIds(column));
	});
}

function getSectionMenuId(section: Section, index: number) {
	return String(section.id || index);
}

function closeSectionMenu() {
	openSectionMenuId.value = null;
	sectionMenuStyle.value = {};
	sectionMenuAnchorEl.value = null;
}

function getFieldMenuId(
	section: Section,
	column: Column,
	field: Field,
	colIndex: number | string
) {
	const sid = String(section.id ?? "section");
	const cid = String((column as any).id ?? colIndex ?? "col");
	const fid = String((field as any).id ?? field.fieldname ?? "field");
	return `${sid}:${cid}:${fid}`;
}

function closeFieldMenu() {
	openFieldMenuId.value = null;
	openFieldSubmenu.value = null;
	fieldMenuStyle.value = {};
	alignSubmenuStyle.value = {};
	fieldMenuAnchorEl.value = null;
}

function onSectionMenuKeydown(event: KeyboardEvent) {
	const menu = sectionMenuEl.value;
	if (!menu) return;
	handleMenuKeydown(event, menu, { includeSubmenu: false, onEscape: closeSectionMenu });
}

function onFieldMenuKeydown(event: KeyboardEvent) {
	const menu = fieldMenuEl.value;
	if (!menu) return;

	const active = document.activeElement as HTMLElement | null;
	if (
		event.key === "ArrowRight" &&
		active &&
		alignMenuItemEl.value &&
		active === alignMenuItemEl.value
	) {
		event.preventDefault();
		if (openFieldSubmenu.value !== "align") {
			openFieldSubmenu.value = "align";
			nextTick(() => {
				updateFloatingMenuPositions();
				const submenu = alignSubmenuEl.value;
				if (submenu) focusFirstMenuItem(submenu, true);
			});
		}
		return;
	}

	handleMenuKeydown(event, menu, {
		includeSubmenu: false,
		onEscape: closeFieldMenu,
	});
}

function onAlignSubmenuKeydown(event: KeyboardEvent) {
	const submenu = alignSubmenuEl.value;
	if (!submenu) return;

	if (event.key === "ArrowLeft") {
		event.preventDefault();
		openFieldSubmenu.value = null;
		alignSubmenuStyle.value = {};
		nextTick(() => alignMenuItemEl.value?.focus());
		return;
	}

	handleMenuKeydown(event, submenu, {
		includeSubmenu: true,
		onEscape: () => {
			openFieldSubmenu.value = null;
			alignSubmenuStyle.value = {};
			nextTick(() => alignMenuItemEl.value?.focus());
		},
	});
}

function toggleSectionMenu(section: Section, index: number, event: MouseEvent) {
	const id = getSectionMenuId(section, index);
	if (openSectionMenuId.value === id) {
		closeSectionMenu();
		return;
	}

	closeFieldMenu();
	openSectionMenuId.value = id;

	const target = event.currentTarget as HTMLElement | null;
	if (!target) return;
	sectionMenuAnchorEl.value = target;

	nextTick(() => {
		const menu = sectionMenuEl.value;
		if (!menu) return;
		updateFloatingMenuPositions();
		focusFirstMenuItem(menu, false);
	});
}

function toggleFieldMenu(id: string, event: MouseEvent) {
	if (openFieldMenuId.value === id) {
		closeFieldMenu();
		return;
	}

	closeSectionMenu();
	openFieldMenuId.value = id;
	openFieldSubmenu.value = null;

	const target =
		(event.currentTarget as HTMLElement | null) ||
		((event.target as HTMLElement | null)?.closest?.(
			".field-card__menu-btn"
		) as HTMLElement | null);
	if (!target) return;
	fieldMenuAnchorEl.value = target;

	nextTick(() => {
		const menu = fieldMenuEl.value;
		if (!menu) return;
		updateFloatingMenuPositions();
		focusFirstMenuItem(menu, false);
	});
}

function ensureLayout() {
	if (!layout.value || !layout.value.sections?.length) {
		if (!store.meta.value) return;
		const fresh = store.getDefaultLayout();
		if (fresh) {
			store.layout.value = fresh;
			store.markDirty();
		}
	}
	ensureLayoutIds();
}

function ensureAtLeastOneSection() {
	if (!layout.value) {
		layout.value = { sections: [] };
	}
	if (!layout.value.sections?.length) {
		layout.value.sections = [createEmptySection()];
	}
	ensureLayoutIds();
}

onMounted(() => {
	ensureLayout();
	ensureAtLeastOneSection();
});

const onPaneClick = () => {
	closeSectionMenu();
	closeFieldMenu();
};
const onPaneKeyDown = (e: KeyboardEvent) => {
	if (e.key === "Escape") {
		closeSectionMenu();
		closeFieldMenu();
	}
};

function isMenuEventTarget(target: EventTarget | null) {
	if (!(target instanceof Element)) return false;
	return Boolean(
		target.closest(
			".section-card__menu, .field-card__menu, .field-card__submenu, .section-card__menu-btn, .field-card__menu-btn"
		)
	);
}

const onDocumentPointerDown = (event: PointerEvent) => {
	if (isMenuEventTarget(event.target)) return;
	closeSectionMenu();
	closeFieldMenu();
};

const onDocumentKeyDown = (event: KeyboardEvent) => {
	if (event.key !== "Escape") return;
	closeSectionMenu();
	closeFieldMenu();
};

const onFloatingBoundaryChange = () => {
	if (!openSectionMenuId.value && !openFieldMenuId.value) return;
	updateFloatingMenuPositions();
};

onMounted(() => {
	const pane = layoutPaneRef.value;
	pane?.addEventListener("click", onPaneClick);
	pane?.addEventListener("keydown", onPaneKeyDown);
	document.addEventListener("pointerdown", onDocumentPointerDown);
	document.addEventListener("keydown", onDocumentKeyDown);
	window.addEventListener("resize", onFloatingBoundaryChange);
	window.addEventListener("scroll", onFloatingBoundaryChange, true);
});

onBeforeUnmount(() => {
	const pane = layoutPaneRef.value;
	pane?.removeEventListener("click", onPaneClick);
	pane?.removeEventListener("keydown", onPaneKeyDown);
	document.removeEventListener("pointerdown", onDocumentPointerDown);
	document.removeEventListener("keydown", onDocumentKeyDown);
	window.removeEventListener("resize", onFloatingBoundaryChange);
	window.removeEventListener("scroll", onFloatingBoundaryChange, true);
});

watch(
	() => store.meta.value,
	() => {
		ensureLayout();
		ensureAtLeastOneSection();
	},
	{ immediate: false }
);

function addSection() {
	if (!layout.value) {
		layout.value = { sections: [] };
	}
	layout.value.sections.push(createEmptySection());
	store.markDirty();
}

function addSectionAbove(index: number) {
	if (!layout.value) {
		layout.value = { sections: [] };
	}
	layout.value.sections.splice(Math.max(0, index), 0, createEmptySection());
	store.markDirty();
}

function onAddSectionAbove(index: number) {
	addSectionAbove(index);
	closeSectionMenu();
}

function addSectionBelow(index: number) {
	if (!layout.value) {
		layout.value = { sections: [] };
	}
	layout.value.sections.splice(Math.max(0, index + 1), 0, createEmptySection());
	store.markDirty();
}

function onAddSectionBelow(index: number) {
	addSectionBelow(index);
	closeSectionMenu();
}

function createEmptySection(): Section {
	return {
		label: "",
		columns: [{ id: createLayoutId(), label: "", fields: [] }],
		id: createLayoutId(),
		field_orientation: "left-right",
	};
}

function removeSection(index: number) {
	layout.value?.sections.splice(index, 1);
	store.markDirty();
}

function onRemoveSection(index: number) {
	removeSection(index);
	closeSectionMenu();
}

function addColumn(section: Section) {
	if (!section.columns) section.columns = [];
	if (section.columns.length >= 4) {
		return;
	}
	section.columns.push({ id: createLayoutId(), label: "", fields: [] });
	store.markDirty();
}

function onAddColumn(section: Section) {
	addColumn(section);
	closeSectionMenu();
}

function removeColumn(section: Section, colIndex: number) {
	if (section.columns.length <= 1) return;
	const removed = section.columns.splice(colIndex, 1)[0];
	const targetIndex = Math.max(colIndex - 1, 0);
	section.columns[targetIndex].fields.push(...removed.fields);
	store.markDirty();
}

function removeLastColumn(section: Section) {
	if (section.columns.length <= 1) return;
	removeColumn(section, section.columns.length - 1);
}

function onRemoveLastColumn(section: Section) {
	removeLastColumn(section);
	closeSectionMenu();
}

function openSectionSettings(section: Section) {
	if (typeof frappe === "undefined" || !frappe.ui?.Dialog) {
		const widths = section.columns.map((col, idx) => {
			const label = `Column ${idx + 1} width (default 1fr)`;
			const current = col.width || "1fr";
			const next = window.prompt(label, current);
			return typeof next === "string" ? next.trim() : "";
		});
		widths.forEach((value, idx) => {
			section.columns[idx].width = value || "";
		});
		store.markDirty();
		return;
	}

	const fields = section.columns.map((col, idx) => ({
		fieldtype: "Data",
		fieldname: `col_${idx}_width`,
		label: `Column ${idx + 1} width`,
		description: "Typst units: 1fr, 2fr, auto, 100pt, 50%, 2cm, etc.",
		default: col.width || "1fr",
	}));

	const dialog = new frappe.ui.Dialog({
		title: __("Section Settings"),
		fields,
		primary_action_label: __("Apply"),
		primary_action: (values: Record<string, any>) => {
			section.columns.forEach((col, idx) => {
				const key = `col_${idx}_width`;
				const value = String(values[key] ?? "").trim();
				col.width = value || "";
			});
			store.markDirty();
			dialog.hide();
		},
	});

	dialog.show();
}

function onOpenSectionSettings(section: Section) {
	openSectionSettings(section);
	closeSectionMenu();
}

function removeField(column: Column, fieldIndex: number) {
	column.fields.splice(fieldIndex, 1);
	store.markDirty();
}

function getFieldAlign(field: Field): "left" | "center" | "right" {
	return field.align || getDefaultAlignment(field.fieldtype);
}

function toggleAlignSubmenu() {
	openFieldSubmenu.value = openFieldSubmenu.value === "align" ? null : "align";
	if (openFieldSubmenu.value === "align") {
		nextTick(() => {
			updateFloatingMenuPositions();
			const submenu = alignSubmenuEl.value;
			if (submenu) focusFirstMenuItem(submenu, true);
		});
	} else {
		alignSubmenuStyle.value = {};
		alignMenuItemEl.value?.focus();
	}
}

function setAlignment(field: Field, align: "left" | "center" | "right") {
	field.align = align;
	store.markDirty();
	closeFieldMenu();
}

function togglePageBreak(section: Section) {
	(section as any).page_break = !(section as any).page_break;
	store.markDirty();
}

function onTogglePageBreak(section: Section) {
	togglePageBreak(section);
	closeSectionMenu();
}

function toggleFieldOrientation(section: Section) {
	const current = section.field_orientation || "left-right";
	section.field_orientation = current === "left-right" ? "top-down" : "left-right";
	store.markDirty();
}

function onToggleFieldOrientation(section: Section) {
	toggleFieldOrientation(section);
	closeSectionMenu();
}

function getFieldOrientationLabel(section: Section) {
	return (section.field_orientation || "left-right") === "left-right"
		? __("Left-Right")
		: __("Top-Down");
}

async function ensureTableColumns(field: Field) {
	if (field.fieldtype !== "Table" || (field.table_columns && field.table_columns.length)) {
		return;
	}
	if (field.fieldname === "data.filters") {
		const filterFields = (store.reportFilterFields?.value || []).map((df: any) => ({
			fieldname: df.fieldname,
			label: df.label || df.fieldname,
			fieldtype: df.fieldtype || "Data",
			width: "auto",
			align: "left" as const,
		}));
		field.table_columns =
			filterFields.length > 0
				? filterFields
				: [
						{
							fieldname: "label",
							label: __("Label"),
							fieldtype: "Data",
							width: "auto",
							align: "left",
						},
						{
							fieldname: "value",
							label: __("Value"),
							fieldtype: "Data",
							width: "auto",
							align: "left",
						},
				  ];
		return;
	}
	if (field.fieldname === "data.report_summary") {
		field.table_columns = [
			{
				fieldname: "label",
				label: __("Label"),
				fieldtype: "Data",
				width: "auto",
				align: "left",
			},
			{
				fieldname: "value",
				label: __("Value"),
				fieldtype: "Data",
				width: "auto",
				align: "right",
			},
			{
				fieldname: "indicator",
				label: __("Indicator"),
				fieldtype: "Data",
				width: "auto",
				align: "left",
			},
			{
				fieldname: "datatype",
				label: __("Data Type"),
				fieldtype: "Data",
				width: "auto",
				align: "left",
			},
			{
				fieldname: "currency",
				label: __("Currency"),
				fieldtype: "Data",
				width: "auto",
				align: "left",
			},
		];
		return;
	}
	if (!field.options) {
		field.table_columns = [];
		return;
	}
	try {
		if (typeof frappe !== "undefined" && frappe.model?.with_doctype) {
			await new Promise<void>((resolve) => {
				frappe.model.with_doctype(field.options, () => resolve());
			});
		}
		field.table_columns = getTableColumns(field.options);
	} catch (e) {
		field.table_columns = [];
		logger.warn("Failed to load table columns", e);
	}
}

async function onDropField(event: DragEvent, column: Column) {
	if (!event.dataTransfer) return;
	try {
		const data = event.dataTransfer.getData("application/json");
		if (!data) return;
		const parsed: DocField = JSON.parse(data);
		if (!parsed.fieldname) return;

		const field: LayoutField = {
			id: createLayoutId(),
			fieldname: parsed.fieldname,
			label: parsed.label || parsed.fieldname,
			fieldtype: parsed.fieldtype || "Data",
			align: getDefaultAlignment(parsed.fieldtype), // Add default alignment
		};

		if (parsed.fieldtype === "Table") {
			field.table_columns = [];
			field.options = parsed.options;
			await ensureTableColumns(field);
		}

		if (parsed.fieldtype === "Crispy Typst Block") {
			field.crispy_typst_block = "";
			field.crispy_typst_block_name = "";
		}

		if (isCrispyImageField(parsed as Field)) {
			field.crispy_image = "";
			field.crispy_image_width = "100%";
			field.crispy_image_height = "";
			field.crispy_image_fit = "";
		}

		column.fields.push(field);
		store.markDirty();
	} catch (e) {
		logger.warn("Failed to drop field", e);
	}
}

function resetLayout() {
	const confirmReset = () => {
		const fresh = store.getDefaultLayout();
		if (fresh) {
			store.layout.value = fresh;
			ensureAtLeastOneSection();
			store.markDirty();
		}
	};

	if (typeof frappe !== "undefined" && typeof frappe.confirm === "function") {
		frappe.confirm(
			__(
				"Reset layout to DocType default (from meta)? This discards all layout changes and restores the starting sections/columns/fields arrangement."
			),
			() => confirmReset(),
			() => {}
		);
		return;
	}

	if (
		!window.confirm(
			"Reset layout to DocType default (from meta)? This discards all layout changes and restores the starting sections/columns/fields arrangement."
		)
	) {
		return;
	}
	const fresh = store.getDefaultLayout();
	if (fresh) {
		store.layout.value = fresh;
		ensureAtLeastOneSection();
		store.markDirty();
	}
}

function gridStyle(section: Section) {
	const cols = Math.max(1, section.columns.length);
	return {
		gridTemplateColumns: `repeat(${cols}, minmax(0, 1fr))`,
	};
}

async function configureColumns(field: Field) {
	if (field.fieldtype !== "Table") return;
	await ensureTableColumns(field);
	editingColumns.value = deepClone(field.table_columns || []);
	columnEditor.value = { field };
}

async function onConfigureColumns(field: Field) {
	await configureColumns(field);
	closeFieldMenu();
}

function onColumnsUpdate(columns: TableColumn[]) {
	if (!columnEditor.value) return;
	editingColumns.value = deepClone(columns || []);
	columnEditor.value.field.table_columns = columns;
	store.markDirty();
}

function closeColumnEditor() {
	columnEditor.value = null;
}

function getTypstBlockStatus(field: Field): string {
	return field.crispy_typst_block_name || field.crispy_typst_block || __("No block selected");
}

function isCrispyImageField(field: Pick<Field, "fieldname" | "fieldtype">): boolean {
	return field.fieldtype === "Crispy Image" || field.fieldname === "_crispy_image";
}

function getImageStatus(field: Field): string {
	return field.crispy_image || __("No image selected");
}

async function chooseTypstBlock(field: Field) {
	blockEditor.value = field;
	blockOptionsLoading.value = true;
	try {
		blockOptions.value = await store.loadApplicableTypstBlocks();
	} catch (error) {
		logger.warn("Failed to load Crispy Typst Blocks", error);
		blockOptions.value = [];
		if (typeof frappe !== "undefined") {
			frappe.show_alert({
				message: __("Failed to load Crispy Typst Blocks"),
				indicator: "red",
			});
		}
	} finally {
		blockOptionsLoading.value = false;
	}
}

function onChooseTypstBlock(field: Field) {
	chooseTypstBlock(field);
	closeFieldMenu();
}

function onTypstBlockSelected(block: CrispyTypstBlockOption) {
	if (!blockEditor.value) return;
	blockEditor.value.crispy_typst_block = block.block_key;
	blockEditor.value.crispy_typst_block_name = block.block_name;
	blockEditor.value.crispy_typst_block_code = block.typst_code || "";
	store.markDirty();
	closeBlockEditor();
}

function closeBlockEditor() {
	blockEditor.value = null;
}

function onChooseImage(field: Field) {
	imageEditor.value = field;
	closeFieldMenu();
}

function getImageEditorSettings(field: Field): CrispyImageSettings {
	return {
		filename: field.crispy_image || "",
		width: field.crispy_image_width ?? "100%",
		height: field.crispy_image_height ?? "",
		fit: field.crispy_image_fit ?? "",
	};
}

function onImageSelected(settings: CrispyImageSettings) {
	if (!imageEditor.value) return;
	imageEditor.value.crispy_image = settings.filename;
	imageEditor.value.crispy_image_width = settings.width;
	imageEditor.value.crispy_image_height = settings.height;
	imageEditor.value.crispy_image_fit = settings.fit;
	store.markDirty();
	closeImageEditor();
}

function closeImageEditor() {
	imageEditor.value = null;
}

function markDirty() {
	store.markDirty();
}

function onLabelEnter(event: KeyboardEvent) {
	const el = event.target as HTMLInputElement | null;
	el?.blur();
}

function getDefaultLabel(field: Field): string {
	const meta = store.meta.value as any;
	const df = meta?.fields?.find?.((f: any) => f?.fieldname === field.fieldname);
	return df?.label || field.fieldname;
}

function toggleFieldLabel(field: Field) {
	const current = (field.label || "").trim();
	if (current) {
		field.label = "";
	} else {
		field.label = getDefaultLabel(field);
	}
	store.markDirty();
}

function onToggleFieldLabel(field: Field) {
	toggleFieldLabel(field);
	closeFieldMenu();
}

function onRemoveField(column: Column, fieldIndex: number) {
	removeField(column, fieldIndex);
	closeFieldMenu();
}

function editTypstCode(field: Field) {
	const existing = field.raw_typst_field || "";

	if (typeof frappe === "undefined" || !frappe.ui?.Dialog) {
		const next = window.prompt(__("Edit Raw Typst Field"), existing);
		if (next === null) return;
		field.raw_typst_field = next;
		store.markDirty();
		return;
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Edit Raw Typst Field"),
		fields: [
			{
				fieldtype: "Code",
				fieldname: "raw_typst_field",
				label: __("Raw Typst Field"),
				options: "Rust",
				reqd: 0,
				default: existing,
			},
		],
		primary_action_label: __("Apply"),
		primary_action: (values: Record<string, any>) => {
			const value = values.raw_typst_field ?? "";
			field.raw_typst_field = value;
			store.markDirty();
			dialog.hide();
		},
	});

	dialog.show();
}

function onEditTypstCode(field: Field) {
	editTypstCode(field);
	closeFieldMenu();
}

function editSpacer(field: Field) {
	const existing = field.spacer_value || "1em";

	if (typeof frappe === "undefined" || !frappe.ui?.Dialog) {
		const next = window.prompt("Enter spacer value (e.g., 1em, 2cm, 10pt):", existing);
		if (next === null) return;
		field.spacer_value = next;
		store.markDirty();
		return;
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Configure Spacer"),
		fields: [
			{
				fieldtype: "Data",
				fieldname: "spacer_value",
				label: __("Spacer Value"),
				description: __("Typst units: 1em, 2cm, 10pt, 5mm, etc."),
				reqd: 1,
				default: existing,
			},
		],
		primary_action_label: __("Apply"),
		primary_action: (values: Record<string, any>) => {
			field.spacer_value = values.spacer_value || "1em";
			store.markDirty();
			dialog.hide();
		},
	});

	dialog.show();
}

function onEditSpacer(field: Field) {
	editSpacer(field);
	closeFieldMenu();
}

function editDivider(field: Field) {
	const existingLength = field.divider_length || "100%";
	const existingStroke = field.divider_stroke || "0.5pt";
	let existingColor = field.divider_color || "gray";

	if (typeof frappe === "undefined" || !frappe.ui?.Dialog) {
		const length = window.prompt("Enter divider length (e.g., 100%, 10cm):", existingLength);
		if (length === null) return;
		const stroke = window.prompt("Enter stroke width (e.g., 0.5pt, 1pt):", existingStroke);
		if (stroke === null) return;
		const color = window.prompt("Enter color (e.g., gray, #333, rgb(0,0,0)):", existingColor);
		if (color === null) return;

		field.divider_length = length;
		field.divider_stroke = stroke;
		field.divider_color = color;
		store.markDirty();
		return;
	}

	const dialog = new frappe.ui.Dialog({
		title: __("Configure Divider"),
		fields: [
			{
				fieldtype: "Data",
				fieldname: "divider_length",
				label: __("Length"),
				description: __("Typst units: 100%, 80%, 10cm, etc."),
				reqd: 1,
				default: existingLength,
			},
			{
				fieldtype: "Data",
				fieldname: "divider_stroke",
				label: __("Stroke Width"),
				description: __("Typst units: 0.5pt, 1pt, 2pt, etc."),
				reqd: 1,
				default: existingStroke,
			},
			{
				fieldtype: "HTML",
				fieldname: "color_picker_html",
				options: `<div class="form-group">
					<label class="control-label">${__("Color")}</label>
					<div id="divider-color-picker"></div>
				</div>`,
			},
		],
		primary_action_label: __("Apply"),
		primary_action: (values: Record<string, any>) => {
			field.divider_length = values.divider_length || "100%";
			field.divider_stroke = values.divider_stroke || "0.5pt";
			field.divider_color = existingColor; // Will be updated by Pickr
			store.markDirty();
			dialog.hide();
		},
	});

	dialog.show();

	// Mount Pickr after dialog is shown
	setTimeout(() => {
		const container = document.getElementById("divider-color-picker");
		if (!container) {
			logger.error("Pickr container not found");
			return;
		}

		// Import Pickr and its CSS dynamically
		Promise.all([
			import("@simonwep/pickr"),
			import("@simonwep/pickr/dist/themes/nano.min.css"),
		])
			.then(([module]) => {
				const Pickr = module.default;

				const pickr = Pickr.create({
					el: container,
					theme: "nano",
					default: existingColor,
					swatches: [
						"#ef4444",
						"#f97316",
						"#f59e0b",
						"#eab308",
						"#84cc16",
						"#22c55e",
						"#10b981",
						"#14b8a6",
						"#06b6d4",
						"#0ea5e9",
						"#3b82f6",
						"#6366f1",
						"#8b5cf6",
						"#a855f7",
						"#d946ef",
						"#ec4899",
						"#000000",
						"#333333",
						"#666666",
						"#999999",
						"#cccccc",
						"#ffffff",
					],
					components: {
						preview: true,
						opacity: false,
						hue: true,
						interaction: {
							hex: true,
							rgba: false,
							hsla: false,
							input: true,
							clear: false,
							save: true,
						},
					},
				});

				pickr.on("save", (color: any) => {
					existingColor = color.toHEXA().toString();
					field.divider_color = existingColor;
					pickr.hide();
				});

				pickr.on("change", (color: any) => {
					existingColor = color.toHEXA().toString();
					field.divider_color = existingColor;
				});

				// Cleanup when dialog is hidden
				dialog.$wrapper.on("hidden.bs.modal", () => {
					pickr?.destroyAndRemove();
				});
			})
			.catch((error) => {
				logger.error("Failed to load Pickr", error);
			});
	}, 300);
}

function onEditDivider(field: Field) {
	editDivider(field);
	closeFieldMenu();
}
</script>

<style scoped>
/* LayoutPane.vue */
.layout-pane {
	position: relative;
	border: 1px solid #e2e8f0;
	display: flex;
	flex-direction: column;
	overflow: visible;
	background: #fff;
}

.layout-pane__header {
	margin: 12px 16px 0;
	padding: 0;
}

.layout-pane__header-row {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 8px;
}

.layout-pane__report-selector-row {
	margin-top: 10px;
}

.layout-pane__report-selector-wrap {
	max-width: 320px;
}

.layout-pane__report-selector {
	width: 100%;
}

.layout-pane__preview-note {
	display: inline-flex;
	font-size: 12px;
	color: #475569;
}

.layout-pane__title-wrap {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	min-width: 0;
}

.layout-pane__title {
	margin: 0;
}

.layout-pane__generic-type-badge {
	display: inline-flex;
	align-items: center;
	padding: 2px 8px;
	font-size: 11px;
	line-height: 1.4;
	color: #1e3a8a;
	background: #eff6ff;
	border: 1px solid #bfdbfe;
	border-radius: 9999px;
	white-space: nowrap;
}

.layout-pane__controls {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
}

.layout-pane__spacer {
	margin-left: auto;
}

.layout-pane__help-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 24px;
	height: 24px;
	border-radius: 9999px;
	border-color: transparent !important;
	background: transparent !important;
	box-shadow: none !important;
	color: #334155;
	font-size: 13px;
	font-weight: 500;
	transition: color 0.15s ease, font-size 0.15s ease, font-weight 0.15s ease;
}

.layout-pane__help-btn:hover,
.layout-pane__help-btn:focus-visible {
	border-color: transparent !important;
	background: transparent !important;
	color: #0f172a;
	font-size: 14px;
	font-weight: 700;
}

.layout-pane__help {
	display: flex;
	align-items: center;
}

.layout-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
}

.layout-pane__help-list {
	margin: 0;
	padding-left: 16px;
	display: grid;
	gap: 6px;
	list-style: disc;
}

.layout-pane__empty {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	gap: 8px;
	font-size: 14px;
	padding: 12px;
}

.layout-pane__body {
	flex: 1;
	overflow: auto;
	padding: 12px 16px;
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.layout-pane__sections {
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.section-card {
	border: 1px solid var(--border-color, #e2e8f0);
	background: var(--card-bg, #fff);
	padding: 16px;
	border-radius: 12px;
}

.section-card__header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	gap: 12px;
	margin-bottom: 8px;
}

.section-card__title-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.section-grip {
	cursor: grab;
	font-size: 24px;
}

.section-title-input {
	width: 190px;
	border-radius: 8px;
}

.section-card__actions {
	display: flex;
	align-items: center;
	gap: 8px;
	flex-wrap: wrap;
}

.section-card__menu-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 28px;
	height: 28px;
	border-radius: 8px;
	border: none;
	background: transparent;
	cursor: pointer;
	font-size: 18px;
	line-height: 1;
}

.section-card__menu {
	border-radius: 12px;
	border: 1px solid var(--border-color, #e2e8f0);
	background: var(--card-bg, #fff);
	padding: 6px;
	width: 260px;
	max-width: calc(100vw - 32px);
	box-shadow: 0 16px 40px rgba(15, 23, 42, 0.14);
}

.section-card__menu-item {
	width: 100%;
	text-align: left;
	border: 0;
	background: transparent;
	padding: 8px 10px;
	border-radius: 8px;
	font-size: 13px;
	cursor: pointer;
	white-space: nowrap;
}

.section-card__menu-item:hover {
	background: var(--control-bg, #f8f9fa);
}

.section-card__menu-item:disabled {
	cursor: not-allowed;
}

.section-card__menu-divider {
	height: 1px;
	margin: 6px 6px;
	background: var(--border-color, #e2e8f0);
}

.section-card__menu-item--danger {
}

.section-grid {
	display: grid;
	gap: 12px;
}

.section-column {
	display: flex;
	flex-direction: column;
	gap: 10px;
	padding: 0;
	min-height: 0;
}

.section-column--empty {
	min-height: 56px;
	border: 1px dashed var(--border-color, #e2e8f0);
	border-radius: 12px;
	background: var(--control-bg, #f8f9fa);
	padding: 10px;
}

.section-column__fields {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.section-column__empty {
	flex: 1;
	display: flex;
	align-items: center;
	justify-content: center;
	text-align: center;
	font-size: 12px;
	padding: 12px;
}

.field-card {
	border: 1px solid var(--border-color, #e2e8f0);
	background: var(--card-bg, #fff);
	padding: 12px;
	border-radius: 8px;
}

.field-card__row {
	display: flex;
	align-items: flex-start;
	justify-content: space-between;
	gap: 8px;
	position: relative;
}

.field-card__info {
	display: flex;
	align-items: center;
	gap: 8px;
	min-width: 0;
	flex: 1;
}

.field-grip {
	cursor: grab;
	font-size: 12px;
	line-height: 1;
}

.field-card__label {
	font-size: 14px;
	white-space: nowrap;
	overflow: hidden;
	text-overflow: ellipsis;
}

.field-card__label-input {
	width: 100%;
	border: none;
	outline: none;
	background: transparent;
	padding: 0;
	min-width: 0;
}

.field-card__label-input--with-status {
	flex: 0 1 auto;
	min-width: 9rem;
	width: auto;
}

.field-card__inline-status {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	min-width: 0;
	max-width: 45%;
	color: #64748b;
	font-size: 13px;
	white-space: nowrap;
}

.field-card__inline-status-text {
	min-width: 0;
	overflow: hidden;
	text-overflow: ellipsis;
}

.field-card__inline-status--empty {
	color: #94a3b8;
}

.field-card__inline-separator {
	color: #cbd5e1;
	flex: 0 0 auto;
}

.field-card__actions {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	position: absolute;
	right: 4px;
	top: 50%;
	transform: translateY(-50%);
	opacity: 0;
	pointer-events: none;
	transition: opacity 0.15s ease;
}

.field-card:hover .field-card__actions,
.field-card:focus-within .field-card__actions {
	opacity: 1;
	pointer-events: auto;
}

.field-card__menu-btn {
	display: inline-flex;
	align-items: center;
	justify-content: center;
	width: 28px;
	height: 28px;
	border-radius: 8px;
	border: none;
	background: transparent;
	cursor: pointer;
	font-size: 18px;
	line-height: 1;
}

.field-card__menu {
	border-radius: 12px;
	border: 1px solid var(--border-color, #e2e8f0);
	background: var(--card-bg, #fff);
	padding: 6px;
	width: 220px;
	max-width: calc(100vw - 32px);
	box-shadow: 0 16px 40px rgba(15, 23, 42, 0.14);
}

.field-card__menu-item {
	width: 100%;
	text-align: left;
	border: 0;
	background: transparent;
	padding: 8px 10px;
	border-radius: 8px;
	font-size: 13px;
	cursor: pointer;
	white-space: nowrap;
	display: flex;
	align-items: center;
	gap: 8px;
}

.field-card__menu-item:hover {
	background: var(--control-bg, #f8f9fa);
}

.field-card__menu-divider {
	height: 1px;
	margin: 6px 6px;
}

.field-card__menu-item--danger {
}

.field-card__submenu {
	border-radius: 12px;
	border: 1px solid var(--border-color, #e2e8f0);
	background: var(--card-bg, #fff);
	padding: 6px;
	width: 180px;
	max-width: calc(100vw - 32px);
	box-shadow: 0 16px 40px rgba(15, 23, 42, 0.14);
}

.field-card__menu-check {
	width: 14px;
	display: inline-flex;
	justify-content: center;
}

.field-card__menu-arrow {
	margin-left: auto;
}

.field-card__columns {
	margin-top: 8px;
	display: flex;
	flex-wrap: wrap;
	gap: 6px;
	font-size: 11px;
}

.field-card__column-pill {
	border: 1px solid var(--border-color, #e2e8f0);
	background: var(--control-bg, #f8f9fa);
	border-radius: 6px;
	padding: 4px 8px;
}

.section-page-break {
	margin-top: 8px;
	border-top: 1px dashed var(--border-color, #e2e8f0);
	padding-top: 8px;
	text-align: center;
	font-size: 12px;
}

.layout-pane__header :deep(.section-head-content) {
	padding: 0 0 8px;
}
</style>
