<template>
	<div class="settings-pane">
		<div class="section-head settings-pane__header">
			<div class="section-head-content settings-pane__header-row">
				<slot name="header-actions"></slot>
				<h3 class="section-title settings-pane__title">{{ __("Presentation") }}</h3>
				<div class="settings-pane__spacer"></div>
				<div>
					<button
						type="button"
						class="btn btn-default btn-xs settings-pane__help-btn"
						popovertarget="settings-help"
						popovertargetaction="toggle"
						:title="__('Toggle help')"
						aria-haspopup="dialog"
						aria-controls="settings-help"
					>
						?
					</button>
					<div id="settings-help" popover class="settings-pane__help-popover">
						<ul class="settings-pane__help-list">
							<li>
								{{ __("Configure page size, margins, and typography for Typst.") }}
							</li>
						</ul>
					</div>
				</div>
			</div>
		</div>
		<div class="settings-pane__body">
			<div class="settings-pane__form">
				<slot name="before-form"></slot>
				<div class="settings-pane__identity-row">
					<div class="settings-pane__field">
						<label class="settings-pane__label">{{ __("Company") }}</label>
						<select v-model="selected_company" class="form-control">
							<option value="">{{ __("Select company") }}</option>
							<option v-if="loadingCompanies" disabled>
								{{ __("Loading companies...") }}
							</option>
							<option
								v-for="company in availableCompanies"
								:key="company.name"
								:value="company.name"
							>
								{{
									company.abbr
										? `${company.abbr} - ${company.name}`
										: company.name
								}}
							</option>
						</select>
					</div>
					<div class="settings-pane__field">
						<label class="settings-pane__label">{{ __("Branding Profile") }}</label>
						<select v-model="branding_profile_selection" class="form-control">
							<option value="" disabled>{{ __("Select Branding Profile") }}</option>
							<option value="custom">{{ __("Custom") }}</option>
							<option v-if="loading_branding_profiles" disabled>
								{{ __("Loading profiles...") }}
							</option>
							<option
								v-for="profile in branding_profiles"
								:key="profile.name"
								:value="profile.name"
							>
								{{
									profile.is_default
										? `${profile.profile_name || profile.name} (${__(
												"Default"
										  )})`
										: profile.profile_name || profile.name
								}}
							</option>
						</select>
					</div>
				</div>

				<SettingsSection
					v-if="!isReportMode"
					v-model="isPrintBehaviorExpanded"
					:title="__('Print Behavior')"
				>
					<label class="settings-pane__checkbox-row">
						<span class="input-area">
							<input
								v-model="compactItemPrint"
								type="checkbox"
								autocomplete="off"
								class="input-with-feedback"
								data-fieldtype="Check"
								data-fieldname="compact_item_print"
							/>
						</span>
						<span class="label-area settings-pane__label">{{
							__("Compact Item Print")
						}}</span>
					</label>
					<label class="settings-pane__checkbox-row">
						<span class="input-area">
							<input
								v-model="printUomAfterQuantity"
								type="checkbox"
								autocomplete="off"
								class="input-with-feedback"
								data-fieldtype="Check"
								data-fieldname="print_uom_after_quantity"
							/>
						</span>
						<span class="label-area settings-pane__label">{{
							__("Print UOM after Quantity")
						}}</span>
					</label>
					<label class="settings-pane__checkbox-row">
						<span class="input-area">
							<input
								v-model="printTaxesWithZeroAmount"
								type="checkbox"
								autocomplete="off"
								class="input-with-feedback"
								data-fieldtype="Check"
								data-fieldname="print_taxes_with_zero_amount"
							/>
						</span>
						<span class="label-area settings-pane__label">{{
							__("Print Taxes with Zero Amount")
						}}</span>
					</label>
				</SettingsSection>

				<template v-if="is_custom_profile">
					<SettingsSection
						v-model="isPresentationSettingsExpanded"
						:title="__('Page Settings')"
					>
						<div class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Size") }}</label>
							<select v-model="presentation_settings.page.size" class="form-control">
								<option value="A3">{{ __("A3 (297 × 420 mm)") }}</option>
								<option value="A4">{{ __("A4 (210 × 297 mm)") }}</option>
								<option value="A5">{{ __("A5 (148 × 210 mm)") }}</option>
								<option value="Letter">
									{{ __("Letter (8.5 × 11 in)") }}
								</option>
								<option value="Legal">{{ __("Legal (8.5 × 14 in)") }}</option>
								<option value="Tabloid">
									{{ __("Tabloid (11 × 17 in)") }}
								</option>
								<option value="Executive">
									{{ __("Executive (7.25 × 10.5 in)") }}
								</option>
							</select>
						</div>

						<div class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Orientation") }}</label>
							<select
								v-model="presentation_settings.page.orientation"
								class="form-control"
							>
								<option value="portrait">{{ __("Portrait") }}</option>
								<option value="landscape">{{ __("Landscape") }}</option>
							</select>
						</div>

						<BoxSidesEditor
							v-model="presentation_settings.page.margins"
							:label="__('Margins (mm)')"
						/>
					</SettingsSection>
					<SettingsSection
						v-if="isReportMode"
						v-model="isReportTemplateExpanded"
						:title="__('Report Template')"
					>
						<div class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Preset") }}</label>
							<select
								v-model="reportBuilderConfig.preset"
								class="form-control"
								:disabled="reportBasicReadOnly"
							>
								<option value="grid">{{ __("Grid") }}</option>
								<option value="tree">{{ __("Tree") }}</option>
								<option value="summary">{{ __("Summary") }}</option>
								<option value="minimal">{{ __("Minimal") }}</option>
							</select>
						</div>
						<div class="settings-pane__grid">
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Font Family")
								}}</label>
								<select
									v-model="reportBuilderConfig.font_family"
									class="form-control"
									:disabled="reportBasicReadOnly"
								>
									<option
										v-for="font in availableFonts"
										:key="font"
										:value="font"
									>
										{{ font }}
									</option>
								</select>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Font Size (pt)")
								}}</label>
								<input
									v-model.number="reportBuilderConfig.font_size_pt"
									type="number"
									min="1"
									step="1"
									class="form-control"
									:disabled="reportBasicReadOnly"
								/>
							</div>
						</div>
						<div class="settings-pane__grid settings-pane__grid--stripe">
							<div class="settings-pane__field settings-pane__field--toggle">
								<label class="settings-pane__sublabel">{{
									__("Show Filters")
								}}</label>
								<div class="settings-pane__checkbox-wrap">
									<input
										v-model="reportBuilderConfig.show_filters"
										type="checkbox"
										class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										:disabled="reportBasicReadOnly"
									/>
								</div>
							</div>
							<div class="settings-pane__field settings-pane__field--toggle">
								<label class="settings-pane__sublabel">{{
									__("Show Summary")
								}}</label>
								<div class="settings-pane__checkbox-wrap">
									<input
										v-model="reportBuilderConfig.show_summary"
										type="checkbox"
										class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										:disabled="reportBasicReadOnly"
									/>
								</div>
							</div>
							<div class="settings-pane__field settings-pane__field--toggle">
								<label class="settings-pane__sublabel">{{
									__("Show Total Row")
								}}</label>
								<div class="settings-pane__checkbox-wrap">
									<input
										v-model="reportBuilderConfig.include_total_row"
										type="checkbox"
										class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										:disabled="reportBasicReadOnly"
									/>
								</div>
							</div>
						</div>
					</SettingsSection>
					<SettingsSection
						v-if="isReportMode"
						v-model="isChartExpanded"
						:title="__('Chart Settings')"
					>
						<div class="settings-pane__grid">
							<div class="settings-pane__field settings-pane__field--toggle">
								<label class="settings-pane__sublabel">{{
									__("Enable Chart")
								}}</label>
								<div class="settings-pane__checkbox-wrap">
									<input
										v-model="reportBuilderConfig.chart_enabled"
										type="checkbox"
										class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										:disabled="reportBasicReadOnly"
									/>
								</div>
							</div>
							<div class="settings-pane__field settings-pane__field--toggle">
								<label class="settings-pane__sublabel">{{
									__("Card Border")
								}}</label>
								<div class="settings-pane__checkbox-wrap">
									<input
										v-model="reportBuilderConfig.chart_card_border"
										type="checkbox"
										class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										:disabled="
											reportBasicReadOnly ||
											!reportBuilderConfig.chart_enabled
										"
									/>
								</div>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Chart Width (%)")
								}}</label>
								<input
									v-model.number="reportBuilderConfig.chart_width_percent"
									type="number"
									min="10"
									max="100"
									step="1"
									class="form-control"
									:disabled="
										reportBasicReadOnly || !reportBuilderConfig.chart_enabled
									"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Max Height (pt)")
								}}</label>
								<input
									v-model.number="reportBuilderConfig.chart_max_height_pt"
									type="number"
									min="60"
									max="600"
									step="1"
									class="form-control"
									:disabled="
										reportBasicReadOnly || !reportBuilderConfig.chart_enabled
									"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Spacing Top (pt)")
								}}</label>
								<input
									v-model.number="reportBuilderConfig.chart_spacing_top_pt"
									type="number"
									min="0"
									max="120"
									step="1"
									class="form-control"
									:disabled="
										reportBasicReadOnly || !reportBuilderConfig.chart_enabled
									"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Spacing Bottom (pt)")
								}}</label>
								<input
									v-model.number="reportBuilderConfig.chart_spacing_bottom_pt"
									type="number"
									min="0"
									max="120"
									step="1"
									class="form-control"
									:disabled="
										reportBasicReadOnly || !reportBuilderConfig.chart_enabled
									"
								/>
							</div>
						</div>
					</SettingsSection>
					<SettingsSection
						v-if="!isReportMode"
						v-model="isTypographyExpanded"
						:title="__('Typography')"
					>
						<TypographyStyleEditor
							v-model="typography.sectionLabel"
							:title="__('Section Labels')"
							:available-fonts="availableFonts"
						/>
						<TypographyStyleEditor
							v-model="typography.fieldLabel"
							:title="__('Field Labels')"
							:available-fonts="availableFonts"
						/>
						<TypographyStyleEditor
							v-model="typography.fieldValue"
							:title="__('Field Values')"
							:available-fonts="availableFonts"
						/>
					</SettingsSection>
					<SettingsSection v-model="isTableExpanded" :title="__('Table Settings')">
						<div class="settings-pane__subsection">
							<BoxSidesEditor
								v-model="tableSettings.inset"
								:label="__('Spacing (pt)')"
							/>
						</div>

						<div class="settings-pane__subsection">
							<label class="settings-pane__label">{{ __("Borders") }}</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Stroke (pt)")
									}}</label>
									<input
										v-model.number="tableSettings.stroke.width"
										type="number"
										min="0"
										step="0.1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Color")
									}}</label>
									<ColorInput v-model="tableSettings.stroke.color" />
								</div>
							</div>
						</div>

						<div class="settings-pane__subsection">
							<label class="settings-pane__label">{{ __("Colors") }}</label>
							<div class="settings-pane__grid settings-pane__grid--colors">
								<div class="settings-pane__field settings-pane__field--span">
									<label class="settings-pane__sublabel">{{
										__("Header Background")
									}}</label>
									<ColorInput v-model="tableSettings.header.backgroundColor" />
								</div>
							</div>
							<div class="settings-pane__grid settings-pane__grid--stripe">
								<div class="settings-pane__field settings-pane__field--toggle">
									<label class="settings-pane__sublabel">{{
										__("Striping")
									}}</label>
									<div class="settings-pane__checkbox-wrap">
										<input
											v-model="tableSettings.stripe.enabled"
											type="checkbox"
											class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										/>
									</div>
								</div>
								<div class="settings-pane__field settings-pane__field--color">
									<label class="settings-pane__sublabel">{{
										__("Stripe Color")
									}}</label>
									<ColorInput
										v-model="tableSettings.stripe.color"
										:disabled="!tableSettings.stripe.enabled"
									/>
								</div>
							</div>
						</div>

						<div class="settings-pane__subsection">
							<label class="settings-pane__label">{{
								__("Cell Label Settings")
							}}</label>
							<div class="settings-pane__grid settings-pane__grid--stripe">
								<div class="settings-pane__field settings-pane__field--toggle">
									<label class="settings-pane__sublabel">{{
										__("Compact Labels")
									}}</label>
									<div class="settings-pane__checkbox-wrap">
										<input
											v-model="tableSettings.cellLabel.enabled"
											type="checkbox"
											class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										/>
									</div>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Size (pt)")
									}}</label>
									<input
										v-model="tableSettings.cellLabel.fontSize"
										type="text"
										class="form-control"
										:disabled="!tableSettings.cellLabel.enabled"
									/>
								</div>
							</div>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Weight")
									}}</label>
									<select
										v-model="tableSettings.cellLabel.fontWeight"
										class="form-control"
										:disabled="!tableSettings.cellLabel.enabled"
									>
										<option
											v-for="option in weightOptions"
											:key="option.value"
											:value="option.value"
										>
											{{ __(option.label) }}
										</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Baseline Shift (pt)")
									}}</label>
									<input
										v-model.number="tableSettings.cellLabel.baselineShift"
										type="number"
										min="-24"
										max="24"
										step="0.5"
										class="form-control"
										:disabled="!tableSettings.cellLabel.enabled"
									/>
								</div>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{ __("Color") }}</label>
								<ColorInput
									v-model="tableSettings.cellLabel.color"
									:disabled="!tableSettings.cellLabel.enabled"
								/>
							</div>
						</div>

						<TypographyStyleEditor
							v-model="tableSettings.typography.header"
							:title="__('Header Typography')"
							:available-fonts="availableFonts"
							:family-label="__('Header Family')"
							:size-label="__('Header Size (pt)')"
							:style-label="__('Header Style')"
							:weight-label="__('Header Weight')"
							:color-label="__('Header Color')"
						/>

						<TypographyStyleEditor
							v-model="tableSettings.typography.body"
							:title="__('Body Typography')"
							:available-fonts="availableFonts"
							:family-label="__('Body Family')"
							:size-label="__('Body Size (pt)')"
							:style-label="__('Body Style')"
							:weight-label="__('Body Weight')"
							:color-label="__('Body Color')"
						/>
					</SettingsSection>

					<SettingsSection v-model="isBrandingExpanded" :title="__('Branding')">
						<div class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Type") }}</label>
							<select v-model="branding_mode" class="form-control">
								<option value="none">{{ __("None") }}</option>
								<option value="letterhead">{{ __("Letterhead") }}</option>
								<option value="logo">{{ __("Logo") }}</option>
							</select>
						</div>

						<div v-if="branding_mode === 'letterhead'" class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Letterhead") }}</label>
							<select
								v-model="presentation_settings.branding.letterhead"
								class="form-control"
							>
								<option value="">{{ __("None") }}</option>
								<option v-if="loadingLetterheads" disabled>
									{{ __("Loading letterheads...") }}
								</option>
								<option
									v-for="letterhead in availableLetterheads"
									:key="letterhead"
									:value="letterhead"
								>
									{{ letterhead }}
								</option>
							</select>
						</div>

						<div v-if="branding_mode === 'logo'">
							<p class="settings-pane__hint">
								{{ __("Logo is anchored to top-left using #place().") }}
							</p>
							<p
								v-if="selected_company && !logo_settings.image"
								class="settings-pane__hint"
							>
								{{ __("Selected company has no logo set.") }}
							</p>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Size (mm)")
									}}</label>
									<input
										v-model.number="logo_settings.size"
										type="number"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("dx (mm)")
									}}</label>
									<input
										v-model.number="logo_settings.dx"
										type="number"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("dy (mm)")
									}}</label>
									<input
										v-model.number="logo_settings.dy"
										type="number"
										class="form-control"
									/>
								</div>
							</div>
						</div>
					</SettingsSection>

					<label v-if="!isReportMode" class="settings-pane__checkbox-row">
						<span class="input-area">
							<input
								v-model="qrSettings.enabled"
								type="checkbox"
								autocomplete="off"
								class="input-with-feedback"
								data-fieldtype="Check"
								data-fieldname="qr_enabled"
							/>
						</span>
						<span class="disp-area" style="display: none">
							<input type="checkbox" disabled class="disabled-deselected" />
						</span>
						<span class="label-area settings-pane__label">{{
							__("Enable QR Code")
						}}</span>
						<span class="ml-1 help"></span>
					</label>

					<div v-if="!isReportMode && qrSettings.enabled" class="settings-pane__section">
						<SettingsSection v-model="isQrExpanded" :title="__('QR-Code')">
							<p class="settings-pane__hint">
								{{ __("QR Code is anchored to bottom-left using #place().") }}
							</p>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Symbology")
								}}</label>
								<select v-model="qrSettings.symbology" class="form-control">
									<option value="QR Code">{{ __("QR Code") }}</option>
									<option value="DataMatrix">{{ __("DataMatrix") }}</option>
								</select>
							</div>
							<div
								v-if="qrSettings.symbology !== 'DataMatrix'"
								class="settings-pane__field"
							>
								<label class="settings-pane__sublabel">{{
									__("Error correction")
								}}</label>
								<select v-model="qrSettings.errorCorrection" class="form-control">
									<option value="Low">{{ __("Low") }}</option>
									<option value="Medium">{{ __("Medium") }}</option>
									<option value="Quartile">{{ __("Quartile") }}</option>
									<option value="High">{{ __("High") }}</option>
								</select>
							</div>
							<div
								v-if="qrSettings.symbology === 'DataMatrix'"
								class="settings-pane__field"
							>
								<label class="settings-pane__sublabel">{{
									__("DataMatrix encodation")
								}}</label>
								<select
									v-model="qrSettings.datamatrixEncodation"
									class="form-control"
								>
									<option value="">{{ __("Auto") }}</option>
									<option value="ascii">ASCII</option>
									<option value="c40">C40</option>
									<option value="text">Text</option>
									<option value="x12">X12</option>
									<option value="edifact">EDIFACT</option>
									<option value="base256">Base256</option>
								</select>
							</div>
							<div
								v-if="qrSettings.symbology === 'DataMatrix'"
								class="settings-pane__field"
							>
								<label class="settings-pane__sublabel">{{
									__("DataMatrix symbols")
								}}</label>
								<select
									v-model="qrSettings.datamatrixSymbols"
									class="form-control"
								>
									<option value="">{{ __("Square") }}</option>
									<option value="rect">{{ __("Rectangular") }}</option>
									<option value="rect-ext">DMRE</option>
								</select>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Size (mm)")
								}}</label>
								<input
									v-model.number="qrSettings.size"
									type="number"
									class="form-control"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Quiet zone")
								}}</label>
								<input
									v-model.number="qrSettings.quietZone"
									type="number"
									min="0"
									class="form-control"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("Module size")
								}}</label>
								<input
									v-model.number="qrSettings.moduleSize"
									type="number"
									min="0"
									class="form-control"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{ __("dx (mm)") }}</label>
								<input
									v-model.number="qrSettings.dx"
									type="number"
									class="form-control"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{ __("dy (mm)") }}</label>
								<input
									v-model.number="qrSettings.dy"
									type="number"
									class="form-control"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{
									__("QR source")
								}}</label>
								<select v-model="qrSettings.sourceMode" class="form-control">
									<option value="">
										{{ __("Inherit branding default") }}
									</option>
									<option value="basic">{{ __("Basic QR") }}</option>
									<option value="document_code_profile">
										{{ __("Document Code Profile") }}
									</option>
								</select>
								<p class="settings-pane__hint">
									{{
										__(
											"Use Basic QR for the current field-list payload, or Document Code Profile to resolve regulated QR output from backend document-code configuration."
										)
									}}
								</p>
							</div>
							<div
								v-if="qrSettings.sourceMode !== 'document_code_profile'"
								class="settings-pane__field"
							>
								<label class="settings-pane__sublabel">{{
									__("QR fields")
								}}</label>
								<div class="settings-pane__qr-row">
									<button
										type="button"
										class="btn btn-default btn-xs settings-pane__qr-btn"
										@click="showQrDialog = true"
									>
										{{ __("Select fields") }}
									</button>
									<span class="settings-pane__qr-summary">{{
										qrFieldsSummary
									}}</span>
								</div>
							</div>
							<p v-else class="settings-pane__hint">
								{{
									__(
										"QR payload fields are ignored in Document Code Profile mode because the backend resolves the final encoded value."
									)
								}}
							</p>
						</SettingsSection>
					</div>
				</template>
			</div>
		</div>
		<QrFieldsDialog
			v-if="is_custom_profile && showQrDialog"
			:fields="qrAvailableFields"
			:model-value="qrSettings.fields"
			@update:model-value="updateQrFields"
			@close="showQrDialog = false"
		/>
	</div>
</template>
<script setup lang="ts">
import { ref, watch, onMounted, computed } from "vue";
import {
	ensure_logo_settings,
	ensure_qr_settings,
	ensure_table_settings,
	ensure_typography,
	type PresentationSettings,
	type TableSettings,
	type TypographySettings,
} from "../utils/presentation_settings";
import ColorInput from "./ColorInput.vue";
import TypographyStyleEditor from "./TypographyStyleEditor.vue";
import SettingsSection from "./SettingsSection.vue";
import BoxSidesEditor from "./BoxSidesEditor.vue";
import { fetchTypstFonts } from "../utils/typstTypography";
import { useBrandingData } from "../composables/useBrandingData";
import { useStore } from "../composables/useStore";
import QrFieldsDialog from "./QrFieldsDialog.vue";
import { getLogger } from "../logger";
import { getBrandingProfiles, type CrispyBrandingProfileOption } from "../api/crispy";
import { getDefaultReportBuilderConfig } from "../utils/reportBuilder";
import { FONT_WEIGHT_OPTIONS } from "../utils/typographyOptions";
import { __ } from "../utils/i18n";

interface Props {
	presentation_settings: PresentationSettings;
	markDirty: () => void;
}

const props = defineProps<Props>();
const logger = getLogger({ component: "SettingsPane" });

const availableFonts = ref<string[]>([]);
const loadingFonts = ref(false);
const branding_profiles = ref<CrispyBrandingProfileOption[]>([]);
const loading_branding_profiles = ref(false);
const {
	availableLetterheads,
	loadingLetterheads,
	availableCompanies,
	loadingCompanies,
	resolveCompanyLogo,
	fetchLetterheads,
	fetchCompanies,
} = useBrandingData();
const isPresentationSettingsExpanded = ref(false);
const isTypographyExpanded = ref(false);
const isTableExpanded = ref(false);
const isReportTemplateExpanded = ref(false);
const isChartExpanded = ref(false);
const isPrintBehaviorExpanded = ref(false);
const isBrandingExpanded = ref(false);
const isQrExpanded = ref(false);
const store = useStore();
const showQrDialog = ref(false);
const fallbackReportBuilder = ref(getDefaultReportBuilderConfig());
const isReportMode = computed(() => Boolean(store.isReportMode?.value));
const reportBuilderConfig = computed({
	get: () => store.reportBuilderConfig?.value || fallbackReportBuilder.value,
	set: (nextValue) => {
		if (store.reportBuilderConfig?.value) {
			store.reportBuilderConfig.value = nextValue;
		} else {
			fallbackReportBuilder.value = nextValue;
		}
	},
});
const reportBasicReadOnly = computed(() => Boolean(store.reportBasicReadOnly?.value));
const weightOptions = FONT_WEIGHT_OPTIONS;
const compactItemPrint = computed<boolean>({
	get: () => Boolean(store.crispyFormat.value?.compact_item_print),
	set: (value) => updatePrintBehavior("compact_item_print", value),
});
const printUomAfterQuantity = computed<boolean>({
	get: () => Boolean(store.crispyFormat.value?.print_uom_after_quantity),
	set: (value) => updatePrintBehavior("print_uom_after_quantity", value),
});
const printTaxesWithZeroAmount = computed<boolean>({
	get: () => Boolean(store.crispyFormat.value?.print_taxes_with_zero_amount),
	set: (value) => updatePrintBehavior("print_taxes_with_zero_amount", value),
});
const logo_settings = computed(() => ensure_logo_settings(props.presentation_settings));
const selected_company = computed<string>({
	get: () =>
		props.presentation_settings.branding.company ||
		props.presentation_settings.branding.logo?.company ||
		"",
	set: (value) => {
		props.presentation_settings.branding.company = value || "";
		logo_settings.value.company = value || "";
		logo_settings.value.image = resolveCompanyLogo(value || "");
		props.presentation_settings.branding.profile = "";
		if (props.presentation_settings.source === "branding_profile") {
			props.presentation_settings.source = "custom";
		}
		props.markDirty();
	},
});
const is_custom_profile = computed(() => props.presentation_settings.source === "custom");
const branding_profile_selection = computed<string>({
	get: () => {
		if (props.presentation_settings.source === "custom") return "custom";
		if (props.presentation_settings.source === "branding_profile") {
			return props.presentation_settings.branding.profile || "";
		}
		return "";
	},
	set: (value) => {
		if (value === "custom") {
			props.presentation_settings.source = "custom";
			props.presentation_settings.branding.profile = "";
		} else if (value) {
			props.presentation_settings.source = "branding_profile";
			props.presentation_settings.branding.profile = value;
			const selectedProfile = branding_profiles.value.find(
				(profile) => profile.name === value
			);
			if (selectedProfile?.company) {
				props.presentation_settings.branding.company = selectedProfile.company;
				logo_settings.value.company = selectedProfile.company;
				logo_settings.value.image = resolveCompanyLogo(selectedProfile.company);
			}
		} else {
			props.presentation_settings.source = "";
			props.presentation_settings.branding.profile = "";
		}
		props.markDirty();
	},
});

// Initialize typography with defaults if not present
const typography = computed<TypographySettings>(() => {
	return ensure_typography(props.presentation_settings);
});

const tableSettings = ref<TableSettings>(ensure_table_settings(props.presentation_settings));
const syncedTableRef = ref(false);

const qrSettings = computed(() => ensure_qr_settings(props.presentation_settings));

const qrAvailableFields = computed(() => store.fields.value || []);

const qrFieldsSummary = computed(() => {
	const count = qrSettings.value.fields?.length || 0;
	if (!count) return __("No fields selected");
	if (count === 1) return __("1 field selected");
	return __("{0} fields selected", [count]);
});

const updateQrFields = (fields: string[]) => {
	qrSettings.value.fields = fields;
	props.markDirty();
};

function updatePrintBehavior(
	fieldname: "compact_item_print" | "print_uom_after_quantity" | "print_taxes_with_zero_amount",
	value: boolean
) {
	if (!store.crispyFormat.value) return;
	store.crispyFormat.value[fieldname] = value ? 1 : 0;
	props.markDirty();
}

const branding_mode = computed<string>({
	get: () => {
		const mode = props.presentation_settings.branding.mode;
		if (
			mode === "letterhead" ||
			mode === "logo" ||
			mode === "logo_letterhead" ||
			mode === "none"
		) {
			return mode;
		}
		if (
			props.presentation_settings.branding.logo?.company ||
			props.presentation_settings.branding.logo?.image
		) {
			return "logo";
		}
		if (props.presentation_settings.branding.letterhead) {
			return "letterhead";
		}
		return "none";
	},
	set: (value) => {
		props.presentation_settings.branding.mode = value as
			| "letterhead"
			| "logo"
			| "logo_letterhead"
			| "none";
	},
});

// Fetch available fonts from Typst
async function fetchFonts() {
	loadingFonts.value = true;
	try {
		availableFonts.value = await fetchTypstFonts({ logger });
	} finally {
		loadingFonts.value = false;
	}
}

async function fetch_branding_profiles() {
	loading_branding_profiles.value = true;
	try {
		branding_profiles.value = await getBrandingProfiles({
			company: selected_company.value || null,
		});
		if (!props.presentation_settings.source && !props.presentation_settings.branding.profile) {
			const default_profile = branding_profiles.value.find((profile) =>
				Number(profile.is_default)
			);
			if (default_profile) {
				props.presentation_settings.source = "branding_profile";
				props.presentation_settings.branding.profile = default_profile.name;
				if (default_profile.company) {
					props.presentation_settings.branding.company = default_profile.company;
					logo_settings.value.company = default_profile.company;
					logo_settings.value.image = resolveCompanyLogo(default_profile.company);
				}
				props.markDirty();
			}
		}
	} catch (error) {
		logger.warn("Failed to load Crispy Branding Profiles", error);
		branding_profiles.value = [];
	} finally {
		loading_branding_profiles.value = false;
	}
}

onMounted(() => {
	fetchFonts();
	fetchScopedLetterheads();
	fetchCompanies({ include_current: selected_company.value || null });
	fetch_branding_profiles();
});

function fetchScopedLetterheads() {
	return fetchLetterheads({
		company: selected_company.value || null,
		include_current: props.presentation_settings.branding.letterhead || null,
	});
}

watch(
	() => props.presentation_settings,
	(nextSettings) => {
		if (syncedTableRef.value && nextSettings.table === tableSettings.value) {
			return;
		}
		tableSettings.value = ensure_table_settings(nextSettings);
		syncedTableRef.value = true;
	},
	{ immediate: true }
);

watch(
	() => props.presentation_settings,
	() => {
		// Don't mark dirty during initial load
		if (!store.loading.value && !store.initializing.value) {
			props.markDirty();
		}
	},
	{ deep: true }
);

watch(
	() => logo_settings.value.company,
	(newCompany) => {
		props.presentation_settings.branding.company =
			props.presentation_settings.branding.company || newCompany || "";
		logo_settings.value.image = resolveCompanyLogo(newCompany);
	}
);

watch(availableCompanies, () => {
	if (!selected_company.value) return;
	logo_settings.value.company = selected_company.value;
	logo_settings.value.image = resolveCompanyLogo(selected_company.value);
});

watch(
	() => selected_company.value,
	() => {
		fetchScopedLetterheads();
		fetch_branding_profiles();
	}
);

watch(branding_profiles, (profiles) => {
	const currentProfile = props.presentation_settings.branding.profile;
	if (!currentProfile) return;
	if (profiles.some((profile) => profile.name === currentProfile)) return;
	props.presentation_settings.branding.profile = "";
	if (props.presentation_settings.source === "branding_profile") {
		props.presentation_settings.source = "custom";
	}
});
</script>

<style scoped>
/* SettingsPane.vue */
.settings-pane {
	display: flex;
	border: 1px solid #e2e8f0;
	flex-direction: column;
	overflow-y: auto;
	background: #fff;
}

.settings-pane__header {
	margin: 12px 16px 0;
	padding: 0;
	border: none;
	box-shadow: none;
}

.settings-pane__header :deep(.section-head-content) {
	padding: 0 0 18px;
	border-bottom: none;
}

.settings-pane__header-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.settings-pane__title {
	margin: 0;
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
	border-color: transparent !important;
	background: transparent !important;
	box-shadow: none !important;
	color: #334155;
	font-size: 13px;
	font-weight: 500;
	transition: color 0.15s ease, font-size 0.15s ease, font-weight 0.15s ease;
}

.settings-pane__header-row {
	align-items: center;
}

.settings-pane__help-btn:hover,
.settings-pane__help-btn:focus-visible {
	border-color: transparent !important;
	background: transparent !important;
	color: #0f172a;
	font-size: 14px;
	font-weight: 700;
}

.settings-pane__help-popover {
	margin-top: 8px;
	border-radius: 12px;
	padding: 12px;
	font-size: 12px;
	line-height: 1.6;
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
	padding: 14px 16px 12px;
}

.settings-pane__form {
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.settings-pane__identity-row {
	display: grid;
	grid-template-columns: minmax(0, 1fr);
	gap: 8px;
	align-items: end;
	margin: 4px 0 2px;
}

.settings-pane__field {
	display: flex;
	flex-direction: column;
	gap: 0px;
}

.settings-pane__field--inline {
	flex-direction: row;
	align-items: center;
	justify-content: flex-start;
	gap: 12px;
}

.settings-pane__checkbox-row {
	display: inline-flex;
	align-items: center;
	gap: 8px;
	margin: 0;
}

.settings-pane__checkbox-row .input-area {
	display: inline-flex;
	align-items: center;
}

.settings-pane__checkbox-row .label-area {
	display: inline-flex;
	align-items: center;
	line-height: 1.2;
}

.settings-pane__field--span {
	grid-column: 1 / -1;
}

.settings-pane__label {
	font-size: 13px;
	font-weight: 600;
}

.settings-pane__checkbox {
	width: 16px;
	height: 16px;
	margin: 0;
}

.settings-pane__hint {
	margin: 0;
	font-size: 12px;
}

.settings-pane__qr-row {
	display: flex;
	align-items: center;
	gap: 12px;
}

.settings-pane__qr-btn {
	padding: 6px 10px;
	border-radius: 8px;
	font-size: 12px;
	cursor: pointer;
}

.settings-pane__qr-summary {
	font-size: 12px;
}

.settings-pane__section {
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.settings-pane__subsection {
	display: flex;
	flex-direction: column;
	gap: 8px;
}

.settings-pane__grid {
	display: grid;
	grid-template-columns: repeat(2, 1fr);
	gap: 8px;
}

.settings-pane__grid--colors {
	gap: 10px;
}

.settings-pane__grid--stripe {
	align-items: center;
}

.settings-pane__sublabel {
	font-size: 11px;
	font-weight: 500;
	margin-bottom: 0px;
}

.settings-pane__field--toggle {
	gap: 6px;
	align-items: center;
}

.settings-pane__field--color :deep(.pickr .pcr-button) {
	width: 36px;
	height: 36px;
	border-radius: 8px;
}
</style>
