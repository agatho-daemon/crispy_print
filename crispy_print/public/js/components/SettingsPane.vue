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
						<select
							v-model="selected_company"
							class="form-control"
							:disabled="Boolean(formatCompany)"
						>
							<option value="">{{ __("Select company") }}</option>
							<option v-if="loadingCompanies" disabled>
								{{ __("Loading companies...") }}
							</option>
							<option
								v-for="company in availableCompanies"
								:key="company.name"
								:value="company.name"
							>
								{{ company.name }}
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
					v-if="!isReportMode && !isRawTypst"
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

				<SettingsSection
					v-if="!isRawTypst"
					v-model="isPresentationSettingsExpanded"
					:title="__('Page Settings')"
					:readonly="profilePresentationReadOnly"
					:readonly-label="profilePresentationReadOnly ? inheritedProfileLabel : ''"
				>
					<div class="settings-pane__field">
						<label class="settings-pane__label">{{ __("Size") }}</label>
						<select
							v-model="presentation_settings.page.size"
							class="form-control"
							@change="markSettingsDirty('live')"
						>
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
							@change="markSettingsDirty('live')"
						>
							<option value="portrait">{{ __("Portrait") }}</option>
							<option value="landscape">{{ __("Landscape") }}</option>
						</select>
					</div>

					<BoxSidesEditor
						v-model="presentation_settings.page.margins"
						:label="__('Margins (mm)')"
						@update:model-value="markSettingsDirty('debounce')"
					/>
				</SettingsSection>
				<SettingsSection
					v-if="isReportMode"
					v-model="isReportTemplateExpanded"
					:title="__('Report Template')"
				>
					<div class="settings-pane__field">
						<label class="settings-pane__label">{{ __("Layout Style") }}</label>
						<select
							:value="reportBuilderConfig.layout_style"
							class="form-control"
							:disabled="reportBasicReadOnly"
							@change="updateReportSettingFromEvent('layout_style', $event)"
						>
							<option value="Standard">{{ __("Standard") }}</option>
							<option value="Compact">{{ __("Compact") }}</option>
							<option value="Minimal">{{ __("Minimal") }}</option>
							<option value="Summary Focus">{{ __("Summary Focus") }}</option>
						</select>
					</div>
					<div class="settings-pane__grid">
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("Font Family") }}</label>
							<select
								:value="reportBuilderConfig.font_family"
								class="form-control"
								:disabled="reportBasicReadOnly"
								@change="updateReportSettingFromEvent('font_family', $event)"
							>
								<option v-for="font in availableFonts" :key="font" :value="font">
									{{ font }}
								</option>
							</select>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{
								__("Font Size (pt)")
							}}</label>
							<input
								:value="reportBuilderConfig.font_size_pt"
								type="number"
								min="1"
								step="1"
								class="form-control"
								:disabled="reportBasicReadOnly"
								@input="updateReportNumberSettingFromEvent('font_size_pt', $event)"
							/>
						</div>
					</div>
					<div class="settings-pane__grid settings-pane__grid--stripe">
						<div class="settings-pane__field settings-pane__field--toggle">
							<label class="settings-pane__sublabel">{{ __("Show Filters") }}</label>
							<div class="settings-pane__checkbox-wrap">
								<input
									:checked="reportBuilderConfig.show_filters"
									type="checkbox"
									class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
									:disabled="reportBasicReadOnly"
									@change="
										updateReportCheckedSettingFromEvent('show_filters', $event)
									"
								/>
							</div>
						</div>
						<div class="settings-pane__field settings-pane__field--toggle">
							<label class="settings-pane__sublabel">{{ __("Show Summary") }}</label>
							<div class="settings-pane__checkbox-wrap">
								<input
									:checked="reportBuilderConfig.show_summary"
									type="checkbox"
									class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
									:disabled="reportBasicReadOnly"
									@change="
										updateReportCheckedSettingFromEvent('show_summary', $event)
									"
								/>
							</div>
						</div>
						<div class="settings-pane__field settings-pane__field--toggle">
							<label class="settings-pane__sublabel">{{
								__("Show Total Row")
							}}</label>
							<div class="settings-pane__checkbox-wrap">
								<input
									:checked="reportBuilderConfig.include_total_row"
									type="checkbox"
									class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
									:disabled="reportBasicReadOnly"
									@change="
										updateReportCheckedSettingFromEvent(
											'include_total_row',
											$event
										)
									"
								/>
							</div>
						</div>
					</div>
					<div v-if="reportBuilderConfig.sections?.length" class="settings-pane__field">
						<label class="settings-pane__label">{{ __("Report Sections") }}</label>
						<label
							v-for="section in reportBuilderConfig.sections"
							:key="section.key"
							class="settings-pane__checkbox-row"
						>
							<input
								:checked="section.visible"
								type="checkbox"
								:disabled="reportBasicReadOnly || !section.optional"
								@change="updateReportSectionVisibility(section.key, $event)"
							/>
							<span>{{ section.label }}</span>
						</label>
					</div>
				</SettingsSection>
				<SettingsSection
					v-if="isReportMode"
					v-model="isChartExpanded"
					:title="__('Chart Settings')"
				>
					<div class="settings-pane__grid">
						<div class="settings-pane__field settings-pane__field--span">
							<label class="settings-pane__sublabel">{{
								__("Chart Representation")
							}}</label>
							<select
								:value="reportBuilderConfig.chart_representation"
								class="form-control"
								:disabled="
									reportBasicReadOnly || !reportBuilderConfig.chart_enabled
								"
								@change="
									updateReportSettingFromEvent('chart_representation', $event)
								"
							>
								<option value="auto">
									{{ __("Auto — use report chart") }}
								</option>
								<option value="bar">{{ __("Bar") }}</option>
								<option value="line">{{ __("Line") }}</option>
								<option value="horizontal_bar">
									{{ __("Horizontal Bar") }}
								</option>
							</select>
							<small class="settings-pane__hint">{{
								__(
									"Auto preserves the report's intended chart. Incompatible overrides keep the original chart."
								)
							}}</small>
						</div>
						<div class="settings-pane__field settings-pane__field--toggle">
							<label class="settings-pane__sublabel">{{ __("Enable Chart") }}</label>
							<div class="settings-pane__checkbox-wrap">
								<input
									:checked="reportBuilderConfig.chart_enabled"
									type="checkbox"
									class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
									:disabled="reportBasicReadOnly"
									@change="
										updateReportCheckedSettingFromEvent(
											'chart_enabled',
											$event
										)
									"
								/>
							</div>
						</div>
						<div class="settings-pane__field settings-pane__field--toggle">
							<label class="settings-pane__sublabel">{{ __("Card Border") }}</label>
							<div class="settings-pane__checkbox-wrap">
								<input
									:checked="reportBuilderConfig.chart_card_border"
									type="checkbox"
									class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
									:disabled="
										reportBasicReadOnly || !reportBuilderConfig.chart_enabled
									"
									@change="
										updateReportCheckedSettingFromEvent(
											'chart_card_border',
											$event
										)
									"
								/>
							</div>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{
								__("Chart Width (%)")
							}}</label>
							<input
								:value="reportBuilderConfig.chart_width_percent"
								type="number"
								min="10"
								max="100"
								step="1"
								class="form-control"
								:disabled="
									reportBasicReadOnly || !reportBuilderConfig.chart_enabled
								"
								@input="
									updateReportNumberSettingFromEvent(
										'chart_width_percent',
										$event
									)
								"
							/>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{
								__("Max Height (pt)")
							}}</label>
							<input
								:value="reportBuilderConfig.chart_max_height_pt"
								type="number"
								min="60"
								max="600"
								step="1"
								class="form-control"
								:disabled="
									reportBasicReadOnly || !reportBuilderConfig.chart_enabled
								"
								@input="
									updateReportNumberSettingFromEvent(
										'chart_max_height_pt',
										$event
									)
								"
							/>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{
								__("Spacing Top (pt)")
							}}</label>
							<input
								:value="reportBuilderConfig.chart_spacing_top_pt"
								type="number"
								min="0"
								max="120"
								step="1"
								class="form-control"
								:disabled="
									reportBasicReadOnly || !reportBuilderConfig.chart_enabled
								"
								@input="
									updateReportNumberSettingFromEvent(
										'chart_spacing_top_pt',
										$event
									)
								"
							/>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{
								__("Spacing Bottom (pt)")
							}}</label>
							<input
								:value="reportBuilderConfig.chart_spacing_bottom_pt"
								type="number"
								min="0"
								max="120"
								step="1"
								class="form-control"
								:disabled="
									reportBasicReadOnly || !reportBuilderConfig.chart_enabled
								"
								@input="
									updateReportNumberSettingFromEvent(
										'chart_spacing_bottom_pt',
										$event
									)
								"
							/>
						</div>
					</div>
				</SettingsSection>
				<SettingsSection
					v-if="!isReportMode && !isRawTypst"
					v-model="isTypographyExpanded"
					:title="__('Typography')"
					:readonly="profilePresentationReadOnly"
					:readonly-label="profilePresentationReadOnly ? inheritedProfileLabel : ''"
				>
					<TypographyStyleEditor
						v-model="typography.sectionLabel"
						:title="__('Section Labels')"
						:available-fonts="availableFonts"
						:font-faces="fontFaces"
						@update:model-value="markSettingsDirty('debounce')"
					/>
					<TypographyStyleEditor
						v-model="typography.fieldLabel"
						:title="__('Field Labels')"
						:available-fonts="availableFonts"
						:font-faces="fontFaces"
						@update:model-value="markSettingsDirty('debounce')"
					/>
					<TypographyStyleEditor
						v-model="typography.fieldValue"
						:title="__('Field Values')"
						:available-fonts="availableFonts"
						:font-faces="fontFaces"
						@update:model-value="markSettingsDirty('debounce')"
					/>
				</SettingsSection>
				<SettingsSection
					v-if="!isRawTypst"
					v-model="isTableExpanded"
					:title="__('Table Settings')"
					:readonly="profilePresentationReadOnly"
					:readonly-label="profilePresentationReadOnly ? inheritedProfileLabel : ''"
				>
					<div class="settings-pane__subsection">
						<BoxSidesEditor
							v-model="tableSettings.inset"
							:label="__('Spacing (pt)')"
							@update:model-value="markSettingsDirty('debounce')"
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
									@input="markSettingsDirty('debounce')"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{ __("Color") }}</label>
								<ColorInput
									v-model="tableSettings.stroke.color"
									@update:model-value="markSettingsDirty('live')"
								/>
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
								<ColorInput
									v-model="tableSettings.header.backgroundColor"
									@update:model-value="markSettingsDirty('live')"
								/>
							</div>
						</div>
						<div class="settings-pane__grid settings-pane__grid--stripe">
							<div class="settings-pane__field settings-pane__field--toggle">
								<label class="settings-pane__sublabel">{{ __("Striping") }}</label>
								<div class="settings-pane__checkbox-wrap">
									<input
										v-model="tableSettings.stripe.enabled"
										type="checkbox"
										class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										@change="markSettingsDirty('live')"
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
									@update:model-value="markSettingsDirty('live')"
								/>
							</div>
						</div>
					</div>

					<div class="settings-pane__subsection">
						<label class="settings-pane__label">{{ __("Cell Label Settings") }}</label>
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
										@change="markSettingsDirty('live')"
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
									@input="markSettingsDirty('debounce')"
								/>
							</div>
						</div>
						<div class="settings-pane__grid">
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{ __("Weight") }}</label>
								<select
									v-model="tableSettings.cellLabel.fontWeight"
									class="form-control"
									:disabled="!tableSettings.cellLabel.enabled"
									@change="markSettingsDirty('live')"
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
									@input="markSettingsDirty('debounce')"
								/>
							</div>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("Color") }}</label>
							<ColorInput
								v-model="tableSettings.cellLabel.color"
								:disabled="!tableSettings.cellLabel.enabled"
								@update:model-value="markSettingsDirty('live')"
							/>
						</div>
					</div>

					<TypographyStyleEditor
						v-model="tableSettings.typography.header"
						:title="__('Header Typography')"
						:available-fonts="availableFonts"
						:font-faces="fontFaces"
						:family-label="__('Header Family')"
						:size-label="__('Header Size (pt)')"
						:style-label="__('Header Style')"
						:weight-label="__('Header Weight')"
						:color-label="__('Header Color')"
						@update:model-value="markSettingsDirty('debounce')"
					/>

					<TypographyStyleEditor
						v-model="tableSettings.typography.body"
						:title="__('Body Typography')"
						:available-fonts="availableFonts"
						:font-faces="fontFaces"
						:family-label="__('Body Family')"
						:size-label="__('Body Size (pt)')"
						:style-label="__('Body Style')"
						:weight-label="__('Body Weight')"
						:color-label="__('Body Color')"
						@update:model-value="markSettingsDirty('debounce')"
					/>
				</SettingsSection>

				<SettingsSection
					v-if="is_custom_profile && !isRawTypst"
					v-model="isBrandingExpanded"
					:title="__('Branding')"
				>
					<div class="settings-pane__field">
						<label class="settings-pane__label">{{ __("Type") }}</label>
						<select
							v-model="branding_mode"
							class="form-control"
							@change="markSettingsDirty('live')"
						>
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
							@change="markSettingsDirty('live')"
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
									@input="markSettingsDirty('debounce')"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{ __("dx (mm)") }}</label>
								<input
									v-model.number="logo_settings.dx"
									type="number"
									class="form-control"
									@input="markSettingsDirty('debounce')"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">{{ __("dy (mm)") }}</label>
								<input
									v-model.number="logo_settings.dy"
									type="number"
									class="form-control"
									@input="markSettingsDirty('debounce')"
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
							@change="markSettingsDirty('live')"
						/>
					</span>
					<span class="disp-area" style="display: none">
						<input type="checkbox" disabled class="disabled-deselected" />
					</span>
					<span class="label-area settings-pane__label">{{ __("Enable QR Code") }}</span>
					<span class="ml-1 help"></span>
				</label>

				<div v-if="!isReportMode && qrSettings.enabled" class="settings-pane__section">
					<SettingsSection v-model="isQrExpanded" :title="__('QR-Code')">
						<p class="settings-pane__hint">
							{{ __("QR Code is anchored to bottom-left using #place().") }}
						</p>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("Symbology") }}</label>
							<select
								v-model="qrSettings.symbology"
								class="form-control"
								@change="markSettingsDirty('live')"
							>
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
							<select
								v-model="qrSettings.errorCorrection"
								class="form-control"
								@change="markSettingsDirty('live')"
							>
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
								@change="markSettingsDirty('live')"
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
								@change="markSettingsDirty('live')"
							>
								<option value="">{{ __("Square") }}</option>
								<option value="rect">{{ __("Rectangular") }}</option>
								<option value="rect-ext">DMRE</option>
							</select>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("Size (mm)") }}</label>
							<input
								v-model.number="qrSettings.size"
								type="number"
								class="form-control"
								@input="markSettingsDirty('debounce')"
							/>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("Quiet zone") }}</label>
							<input
								v-model.number="qrSettings.quietZone"
								type="number"
								min="0"
								class="form-control"
								@input="markSettingsDirty('debounce')"
							/>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("Module size") }}</label>
							<input
								v-model.number="qrSettings.moduleSize"
								type="number"
								min="0"
								class="form-control"
								@input="markSettingsDirty('debounce')"
							/>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("dx (mm)") }}</label>
							<input
								v-model.number="qrSettings.dx"
								type="number"
								class="form-control"
								@input="markSettingsDirty('debounce')"
							/>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("dy (mm)") }}</label>
							<input
								v-model.number="qrSettings.dy"
								type="number"
								class="form-control"
								@input="markSettingsDirty('debounce')"
							/>
						</div>
						<div class="settings-pane__field">
							<label class="settings-pane__sublabel">{{ __("QR source") }}</label>
							<select
								v-model="qrSettings.sourceMode"
								class="form-control"
								@change="markSettingsDirty('live')"
							>
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
							<label class="settings-pane__sublabel">{{ __("QR fields") }}</label>
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
			</div>
		</div>
		<QrFieldsDialog
			v-if="showQrDialog"
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
	merge_presentation_settings,
	type PresentationSettings,
	type TableSettings,
	type TypographySettings,
} from "../utils/presentation_settings";
import ColorInput from "./ColorInput.vue";
import TypographyStyleEditor from "./TypographyStyleEditor.vue";
import SettingsSection from "./SettingsSection.vue";
import BoxSidesEditor from "./BoxSidesEditor.vue";
import { useBrandingData } from "../composables/useBrandingData";
import { useStore, type MarkDirtyOptions } from "../composables/useStore";
import QrFieldsDialog from "./QrFieldsDialog.vue";
import { getLogger } from "../logger";
import {
	getBrandingProfilePresentationSettings,
	getBrandingProfiles,
	type CrispyBrandingProfileOption,
} from "../api/crispy";
import { getDefaultReportBuilderConfig, type ReportBuilderConfig } from "../utils/reportBuilder";
import { FONT_WEIGHT_OPTIONS } from "../utils/typographyOptions";
import type { TypstFontFamilyFaces } from "../api/crispy";
import { __ } from "../utils/i18n";

interface Props {
	presentation_settings: PresentationSettings;
	markDirty: (options?: MarkDirtyOptions) => void;
	availableFonts?: string[];
	fontFaces?: TypstFontFamilyFaces[];
	loadingFonts?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
	availableFonts: () => [],
	fontFaces: () => [],
	loadingFonts: false,
});
const emit = defineEmits<{
	(event: "branding-profiles-change", profiles: CrispyBrandingProfileOption[]): void;
}>();
const logger = getLogger({ component: "SettingsPane" });

const availableFonts = computed(() => props.availableFonts || []);
const fontFaces = computed(() => props.fontFaces || []);
const loadingFonts = computed(() => props.loadingFonts);
const branding_profiles = ref<CrispyBrandingProfileOption[]>([]);
const branding_profile_baseline = ref<Partial<PresentationSettings> | null>(null);
const loading_branding_profiles = ref(false);
let brandingProfilesRequestSeq = 0;
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
const isRawTypst = computed(() => Boolean(store.rawTypst?.value));
const formatCompany = computed(() => String(store.formatCompany?.value || "").trim());
const formatReady = computed(() =>
	store.crispyFormat ? Boolean(store.crispyFormat.value) : true
);
const reportBuilderConfig = computed({
	get: () => store.reportBuilderConfig?.value || fallbackReportBuilder.value,
	set: (nextValue) => {
		if (store.updateReportBuilderConfig) {
			store.updateReportBuilderConfig(nextValue, { preview: "live" });
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
		formatCompany.value ||
		props.presentation_settings.branding.company ||
		props.presentation_settings.branding.logo?.company ||
		"",
	set: (value) => {
		if (formatCompany.value) return;
		props.presentation_settings.branding.company = value || "";
		logo_settings.value.company = value || "";
		logo_settings.value.image = resolveCompanyLogo(value || "");
		props.presentation_settings.branding.profile = "";
		if (props.presentation_settings.source === "branding_profile") {
			props.presentation_settings.source = "custom";
		}
		markSettingsDirty("live");
	},
});
const is_custom_profile = computed(
	() => props.presentation_settings.source !== "branding_profile"
);
const profilePresentationReadOnly = computed(
	() => !isReportMode.value && props.presentation_settings.source === "branding_profile"
);
const inheritedProfileLabel = __("Inherited from the selected Branding Profile.");
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
			props.presentation_settings.overrides = undefined;
			branding_profile_baseline.value = null;
		} else if (value) {
			props.presentation_settings.source = "branding_profile";
			props.presentation_settings.branding.profile = value;
			if (!isReportMode.value) {
				props.presentation_settings.overrides = undefined;
			}
			const selectedProfile = branding_profiles.value.find(
				(profile) => profile.name === value
			);
			const company = formatCompany.value || selectedProfile?.company || "";
			if (company) {
				props.presentation_settings.branding.company = company;
				logo_settings.value.company = company;
				logo_settings.value.image = resolveCompanyLogo(company);
			}
			void applyBrandingProfileBase(value);
		} else {
			props.presentation_settings.source = "";
			props.presentation_settings.branding.profile = "";
		}
		markSettingsDirty("live", false);
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

function markSettingsDirty(policy: MarkDirtyOptions["preview"] = "live", captureOverrides = true) {
	if (store.loading.value || store.initializing.value) return;
	if (
		captureOverrides &&
		isReportMode.value &&
		props.presentation_settings.source === "branding_profile" &&
		branding_profile_baseline.value
	) {
		props.presentation_settings.overrides =
			deepDifference(
				branding_profile_baseline.value,
				extractOverrideableSettings(props.presentation_settings)
			) || {};
	}
	props.markDirty({ preview: policy });
}

async function applyBrandingProfileBase(profile: string) {
	try {
		const profileSettings = await getBrandingProfilePresentationSettings(profile);
		if (props.presentation_settings.branding.profile !== profile) return;
		const baseline = extractOverrideableSettings(profileSettings as PresentationSettings);
		branding_profile_baseline.value = cloneValue(baseline);
		if (!isReportMode.value) {
			props.presentation_settings.overrides = undefined;
		}
		const effective = merge_presentation_settings(
			profileSettings as PresentationSettings,
			(isReportMode.value
				? props.presentation_settings.overrides || {}
				: {}) as Partial<PresentationSettings>
		);
		for (const key of ["page", "typography", "table", "qr", "reportTheme"] as const) {
			if (effective[key] !== undefined) {
				(props.presentation_settings as any)[key] = cloneValue(effective[key]);
			}
		}
	} catch (error) {
		logger.warn("Failed to load Branding Profile base settings", error);
	}
}

function extractOverrideableSettings(settings: PresentationSettings) {
	return {
		page: cloneValue(settings.page),
		typography: cloneValue(settings.typography),
		table: cloneValue(settings.table),
		qr: cloneValue(settings.qr),
		reportTheme: cloneValue(settings.reportTheme),
	};
}

function deepDifference(base: any, current: any): any {
	if (Array.isArray(base) || Array.isArray(current)) {
		return JSON.stringify(base) === JSON.stringify(current) ? undefined : cloneValue(current);
	}
	if (base && current && typeof base === "object" && typeof current === "object") {
		const out: Record<string, any> = {};
		for (const key of Object.keys(current)) {
			const difference = deepDifference(base[key], current[key]);
			if (difference !== undefined) out[key] = difference;
		}
		return Object.keys(out).length ? out : undefined;
	}
	return Object.is(base, current) ? undefined : current;
}

function cloneValue<T>(value: T): T {
	return value === undefined ? value : JSON.parse(JSON.stringify(value));
}

const updateQrFields = (fields: string[]) => {
	qrSettings.value.fields = fields;
	markSettingsDirty("live");
};

function updatePrintBehavior(
	fieldname: "compact_item_print" | "print_uom_after_quantity" | "print_taxes_with_zero_amount",
	value: boolean
) {
	if (!store.crispyFormat.value) return;
	store.crispyFormat.value[fieldname] = value ? 1 : 0;
	markSettingsDirty("live");
}

function updateReportSetting<K extends keyof ReportBuilderConfig>(
	fieldname: K,
	value: ReportBuilderConfig[K],
	policy: MarkDirtyOptions["preview"] = "live"
) {
	if (store.updateReportBuilderConfig) {
		store.updateReportBuilderConfig({ [fieldname]: value } as Partial<ReportBuilderConfig>, {
			preview: policy,
		});
		return;
	}
	fallbackReportBuilder.value = {
		...fallbackReportBuilder.value,
		[fieldname]: value,
	};
	markSettingsDirty(policy);
}

function updateReportNumberSetting<K extends keyof ReportBuilderConfig>(
	fieldname: K,
	value: string,
	policy: MarkDirtyOptions["preview"] = "debounce"
) {
	const parsed = value === "" ? 0 : Number(value);
	updateReportSetting(
		fieldname,
		(Number.isFinite(parsed) ? parsed : 0) as ReportBuilderConfig[K],
		policy
	);
}

function eventTargetValue(event: Event): string {
	return (event.target as HTMLInputElement | HTMLSelectElement | null)?.value || "";
}

function eventTargetChecked(event: Event): boolean {
	return Boolean((event.target as HTMLInputElement | null)?.checked);
}

function updateReportSettingFromEvent<K extends keyof ReportBuilderConfig>(
	fieldname: K,
	event: Event
) {
	updateReportSetting(fieldname, eventTargetValue(event) as ReportBuilderConfig[K]);
}

function updateReportNumberSettingFromEvent<K extends keyof ReportBuilderConfig>(
	fieldname: K,
	event: Event
) {
	updateReportNumberSetting(fieldname, eventTargetValue(event), "debounce");
}

function updateReportCheckedSettingFromEvent<K extends keyof ReportBuilderConfig>(
	fieldname: K,
	event: Event
) {
	updateReportSetting(fieldname, eventTargetChecked(event) as ReportBuilderConfig[K]);
}

function updateReportSectionVisibility(key: string, event: Event) {
	const visible = eventTargetChecked(event);
	const sections = (reportBuilderConfig.value.sections || []).map((section) =>
		section.key === key ? { ...section, visible } : { ...section }
	);
	updateReportSetting("sections", sections, "live");
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

async function fetch_branding_profiles() {
	const requestSeq = ++brandingProfilesRequestSeq;
	const company = selected_company.value || null;
	loading_branding_profiles.value = true;
	try {
		const profiles = await getBrandingProfiles({
			company,
		});
		if (requestSeq !== brandingProfilesRequestSeq) return;
		branding_profiles.value = profiles;
		emit("branding-profiles-change", branding_profiles.value);
		const selectedProfileName = props.presentation_settings.branding.profile;
		if (props.presentation_settings.source === "branding_profile" && selectedProfileName) {
			void applyBrandingProfileBase(selectedProfileName);
		}
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
				void applyBrandingProfileBase(default_profile.name);
				markSettingsDirty("live", false);
			}
		}
	} catch (error) {
		if (requestSeq !== brandingProfilesRequestSeq) return;
		logger.warn("Failed to load Crispy Branding Profiles", error);
		branding_profiles.value = [];
		emit("branding-profiles-change", []);
	} finally {
		if (requestSeq === brandingProfilesRequestSeq) {
			loading_branding_profiles.value = false;
		}
	}
}

onMounted(() => {
	fetchScopedLetterheads();
	fetchCompanies({ include_current: selected_company.value || null });
	if (formatReady.value) fetch_branding_profiles();
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
	formatCompany,
	(company) => {
		if (!company) return;
		props.presentation_settings.branding.company = company;
		logo_settings.value.company = company;
		logo_settings.value.image = resolveCompanyLogo(company);
		void fetchCompanies({ include_current: company });
	},
	{ immediate: true }
);

watch([formatReady, () => selected_company.value], ([ready]) => {
	if (!ready) return;
	fetchScopedLetterheads();
	fetch_branding_profiles();
});

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
