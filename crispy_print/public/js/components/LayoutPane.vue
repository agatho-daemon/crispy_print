<template>
	<div class="layout-pane">
		<div class="section-head layout-pane__header">
			<div class="section-head-content layout-pane__header-row">
				<h3 class="section-title layout-pane__title">Layout Builder</h3>
				<div class="layout-pane__controls">
					<button class="btn btn-default btn-sm" @click="resetLayout">
						Reset to Default
					</button>
					<div class="layout-pane__spacer"></div>
					<div class="layout-pane__help">
						<button
							type="button"
							class="btn btn-default btn-xs layout-pane__help-btn"
							popovertarget="layout-help"
							popovertargetaction="toggle"
							title="Toggle help"
						>
							?
						</button>
						<div id="layout-help" popover class="layout-pane__help-popover">
							<ul class="layout-pane__help-list">
								<li>Drag fields from Fields pane into columns.</li>
								<li>
									Use handles to reorder sections, columns, and fields in place.
								</li>
								<li>
									Use the &#8943; menu on a section for add/remove/page
									break/orientation.
								</li>
							</ul>
						</div>
					</div>
				</div>
			</div>
		</div>
		<div v-if="!layout" class="layout-pane__empty">
			No layout loaded.
			<button class="btn btn-link btn-sm" @click="ensureLayout">Load default</button>
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
								<span class="section-grip" title="Drag section">&#8942;</span>
								<input
									v-model="section.label"
									type="text"
									class="form-control section-title-input"
									placeholder="Section title"
								/>
							</div>
							<div class="section-card__actions">
								<button
									type="button"
									class="section-card__menu-btn"
									title="Section menu"
									@click.stop="toggleSectionMenu(section, sectionIndex, $event)"
								>
									&#8943;
								</button>
								<div
									v-if="
										openSectionMenuId ===
										getSectionMenuId(section, sectionIndex)
									"
									class="section-card__menu"
									:style="sectionMenuStyle"
									@click.stop
								>
									<button
										type="button"
										class="section-card__menu-item"
										@click="onAddSectionAbove(sectionIndex)"
									>
										Add section above
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										@click="onAddSectionBelow(sectionIndex)"
									>
										Add section below
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										:disabled="section.columns.length >= 4"
										@click="onAddColumn(section)"
									>
										Add column
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										:disabled="section.columns.length <= 1"
										@click="onRemoveLastColumn(section)"
									>
										Remove column
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										@click="onTogglePageBreak(section)"
									>
										{{
											section.page_break
												? "Remove page break"
												: "Add page break"
										}}
									</button>
									<button
										type="button"
										class="section-card__menu-item"
										@click="onToggleFieldOrientation(section)"
									>
										Field orientation ({{ getFieldOrientationLabel(section) }})
									</button>
									<div class="section-card__menu-divider"></div>
									<button
										type="button"
										class="section-card__menu-item section-card__menu-item--danger"
										@click="onRemoveSection(sectionIndex)"
									>
										Remove section
									</button>
								</div>
							</div>
						</div>

						<div class="section-grid" :style="gridStyle(section)">
							<div
								v-for="(column, colIndex) in section.columns"
								:key="colIndex"
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
									item-key="fieldname"
									handle=".field-grip"
									:animation="150"
									class="section-column__fields"
								>
									<template #item="{ element: field, index: fieldIndex }">
										<div class="field-card">
											<div class="field-card__row">
												<div class="field-card__info">
													<span class="field-grip" title="Drag field">
														&#8942;
													</span>
													<input
														v-model="field.label"
														type="text"
														class="form-control field-card__label field-card__label-input"
														:placeholder="field.fieldname"
														@blur="markDirty()"
														@keydown.enter.prevent="onLabelEnter"
													/>
												</div>
												<div class="field-card__actions">
													<button
														type="button"
														class="field-card__menu-btn"
														title="Field menu"
														@click.stop="
															toggleFieldMenu(
																getFieldMenuId(
																	section,
																	colIndex,
																	field
																),
																$event
															)
														"
													>
														&#8943;
													</button>
													<teleport to="body">
														<div
															v-if="
																openFieldMenuId ===
																getFieldMenuId(
																	section,
																	colIndex,
																	field
																)
															"
															class="field-card__menu"
															:style="fieldMenuStyle"
															@click.stop
														>
															<button
																type="button"
																class="field-card__menu-item"
																@click="toggleAlignSubmenu"
															>
																Align
																<span
																	class="field-card__menu-arrow"
																	>›</span
																>
															</button>
															<div
																v-if="openFieldSubmenu === 'align'"
																class="field-card__submenu"
																@click.stop
															>
																<button
																	type="button"
																	class="field-card__menu-item"
																	@click="
																		setAlignment(field, 'left')
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
																	Left
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
																	Center
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
																	Right
																</button>
															</div>

															<button
																type="button"
																class="field-card__menu-item"
																@click="onToggleFieldLabel(field)"
															>
																{{
																	(field.label ?? "").trim()
																		? "Hide label"
																		: "Show label"
																}}
															</button>

															<button
																v-if="field.fieldtype === 'Table'"
																type="button"
																class="field-card__menu-item"
																@click="onConfigureColumns(field)"
															>
																Configure columns
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
															>
																Edit code
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
															>
																Configure spacer
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
															>
																Configure divider
															</button>

															<div
																class="field-card__menu-divider"
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
															>
																Remove
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
													:title="`Width: ${col.width ?? 'auto'}%`"
												>
													{{ col.label }}
												</div>
											</div>
										</div>
									</template>
								</draggable>

								<div v-if="!column.fields.length" class="section-column__empty">
									Drop fields here
								</div>
							</div>
						</div>

						<div v-if="section.page_break" class="section-page-break">Page Break</div>
					</div>
				</template>
			</draggable>
		</div>
		<TableColumnsDialog
			v-if="columnEditor"
			:model-value="editingColumns"
			:doctype="columnEditor.field.options || ''"
			@update:modelValue="onColumnsUpdate"
			@close="closeColumnEditor"
		/>
	</div>
</template>

<script setup lang="ts">
import draggable from "vuedraggable";
import { onBeforeUnmount, onMounted, ref, watch } from "vue";
import { useStore } from "../composables/useStore";
import TableColumnsDialog from "../components/TableColumnsDialog.vue";
import type {
	LayoutSection,
	LayoutColumn,
	LayoutField,
	DocField,
	TableColumn,
} from "../utils/layout";
import { getTableColumns } from "../utils/layout";
import { getDefaultAlignment } from "../utils/tableColumns";

type Section = LayoutSection & {
	id?: number;
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

const openSectionMenuId = ref<string | null>(null);
const sectionMenuStyle = ref<Record<string, string>>({});

const openFieldMenuId = ref<string | null>(null);
const fieldMenuStyle = ref<Record<string, string>>({});
const openFieldSubmenu = ref<"align" | null>(null);
let sectionIdSeed = 0;

const sectionKey = (section: Section, index: number) => {
	return (section as any).id || index;
};

function nextSectionId() {
	sectionIdSeed += 1;
	return `section_${Date.now()}_${sectionIdSeed}`;
}

function ensureSectionIds() {
	if (!layout.value?.sections?.length) return;
	const seen = new Set<string | number>();
	layout.value.sections.forEach((section) => {
		const currentId = (section as any).id;
		if (!currentId || seen.has(currentId)) {
			(section as any).id = nextSectionId();
		}
		seen.add((section as any).id);
	});
}

function getSectionMenuId(section: Section, index: number) {
	return String(section.id || index);
}

function closeSectionMenu() {
	openSectionMenuId.value = null;
	sectionMenuStyle.value = {};
}

function getFieldMenuId(section: Section, colIndex: number | string, field: Field) {
	const sid = String(section.id ?? "section");
	const fname = String(field.fieldname ?? "field");
	return `${sid}:${String(colIndex)}:${fname}`;
}

function closeFieldMenu() {
	openFieldMenuId.value = null;
	openFieldSubmenu.value = null;
	fieldMenuStyle.value = {};
}

function toggleSectionMenu(section: Section, index: number, event: MouseEvent) {
	const id = getSectionMenuId(section, index);
	if (openSectionMenuId.value === id) {
		closeSectionMenu();
		return;
	}

	openSectionMenuId.value = id;

	const target = event.currentTarget as HTMLElement | null;
	if (!target) return;

	const rect = target.getBoundingClientRect();
	const menuHeight = 280; // Approximate menu height
	const viewportHeight = window.innerHeight;

	// Check if menu would overflow bottom of viewport
	const shouldFlipUp = rect.bottom + menuHeight + 6 > viewportHeight;

	const top = shouldFlipUp ? rect.top - menuHeight - 6 : rect.bottom + 6;
	const left = rect.right;

	sectionMenuStyle.value = {
		position: "fixed",
		top: `${top}px`,
		left: `${left}px`,
		transform: "translateX(-100%)",
		zIndex: "1000",
	};
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

	const rect = target?.getBoundingClientRect?.();
	const estimatedMenuHeight = 280;
	const maxTop = Math.max(12, window.innerHeight - estimatedMenuHeight);

	const top = Math.min((rect?.bottom ?? event.clientY) + 6, maxTop);
	const left = rect?.right ?? event.clientX;

	fieldMenuStyle.value = {
		position: "fixed",
		top: `${top}px`,
		left: `${left}px`,
		transform: "translateX(-100%)",
		zIndex: "1000",
	};
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
	ensureSectionIds();
}

function ensureAtLeastOneSection() {
	if (!layout.value) {
		layout.value = { sections: [] };
	}
	if (!layout.value.sections?.length) {
		layout.value.sections = [createEmptySection()];
	}
	ensureSectionIds();
}

onMounted(() => {
	ensureLayout();
	ensureAtLeastOneSection();
});

const onDocClick = () => {
	closeSectionMenu();
	closeFieldMenu();
};
const onKeyDown = (e: KeyboardEvent) => {
	if (e.key === "Escape") {
		closeSectionMenu();
		closeFieldMenu();
	}
};

onMounted(() => {
	document.addEventListener("click", onDocClick);
	document.addEventListener("keydown", onKeyDown);
});

onBeforeUnmount(() => {
	document.removeEventListener("click", onDocClick);
	document.removeEventListener("keydown", onKeyDown);
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
		columns: [{ label: "", fields: [] }],
		id: nextSectionId(),
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
	section.columns.push({ label: "", fields: [] });
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

function removeField(column: Column, fieldIndex: number) {
	column.fields.splice(fieldIndex, 1);
	store.markDirty();
}

function getFieldAlign(field: Field): "left" | "center" | "right" {
	return field.align || getDefaultAlignment(field.fieldtype);
}

function toggleAlignSubmenu() {
	openFieldSubmenu.value = openFieldSubmenu.value === "align" ? null : "align";
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
		? "Left-Right"
		: "Top-Down";
}

async function ensureTableColumns(field: Field) {
	if (field.fieldtype !== "Table" || (field.table_columns && field.table_columns.length)) {
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
		console.warn("Failed to load table columns", e);
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

		column.fields.push(field);
		store.markDirty();
	} catch (e) {
		console.warn("Failed to drop field", e);
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
	editingColumns.value = JSON.parse(JSON.stringify(field.table_columns || []));
	columnEditor.value = { field };
}

async function onConfigureColumns(field: Field) {
	await configureColumns(field);
	closeFieldMenu();
}

function onColumnsUpdate(columns: TableColumn[]) {
	if (!columnEditor.value) return;
	editingColumns.value = JSON.parse(JSON.stringify(columns || []));
	columnEditor.value.field.table_columns = columns;
	store.markDirty();
}

function closeColumnEditor() {
	columnEditor.value = null;
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
		const next = window.prompt("Edit Raw Typst Field", existing);
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
			console.error("Pickr container not found");
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
				console.error("Failed to load Pickr:", error);
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
	display: flex;
	flex-direction: column;
	overflow-y: auto;
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

.layout-pane__title {
	margin: 0;
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

.section-card__menu-item:disabled {
	cursor: not-allowed;
}

.section-card__menu-divider {
	height: 1px;
	margin: 6px 6px;
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

.field-card__menu-divider {
	height: 1px;
	margin: 6px 6px;
}

.field-card__menu-item--danger {
}

.field-card__submenu {
	position: absolute;
	top: 6px;
	left: calc(100% + 6px);
	border-radius: 12px;
	border: 1px solid var(--border-color, #e2e8f0);
	background: var(--card-bg, #fff);
	padding: 6px;
	width: 180px;
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
