<template>
	<div class="settings-pane">
		<div class="section-head settings-pane__header">
			<div class="section-head-content settings-pane__header-row">
				<slot name="header-actions"></slot>
				<h3 class="section-title settings-pane__title">{{ __("Typst Settings") }}</h3>
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
				<div class="settings-pane__section-card card">
					<button
						type="button"
						class="btn btn-link card-header settings-pane__section-header"
						:class="{ 'is-expanded': isPageSettingsExpanded }"
						@click="isPageSettingsExpanded = !isPageSettingsExpanded"
					>
						<span>{{ __("Page Settings") }}</span>
						<svg
							:class="[
								'settings-pane__chevron',
								{ 'settings-pane__chevron--expanded': isPageSettingsExpanded },
							]"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>

					<div
						v-if="isPageSettingsExpanded"
						class="settings-pane__section-content card-body"
					>
						<div class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Size") }}</label>
							<select v-model="pageSettings.pageSize" class="form-control">
								<option value="A3">{{ __("A3 (297 × 420 mm)") }}</option>
								<option value="A4">{{ __("A4 (210 × 297 mm)") }}</option>
								<option value="A5">{{ __("A5 (148 × 210 mm)") }}</option>
								<option value="Letter">{{ __("Letter (8.5 × 11 in)") }}</option>
								<option value="Legal">{{ __("Legal (8.5 × 14 in)") }}</option>
								<option value="Tabloid">{{ __("Tabloid (11 × 17 in)") }}</option>
								<option value="Executive">
									{{ __("Executive (7.25 × 10.5 in)") }}
								</option>
							</select>
						</div>

						<div class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Orientation") }}</label>
							<select v-model="pageSettings.orientation" class="form-control">
								<option value="portrait">{{ __("Portrait") }}</option>
								<option value="landscape">{{ __("Landscape") }}</option>
							</select>
						</div>

						<div class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Margins (mm)") }}</label>
							<div class="settings-pane__margins">
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">{{
										__("Top")
									}}</span>
									<input
										v-model.number="pageSettings.margins.top"
										type="number"
										:placeholder="__('Top')"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">{{
										__("Bottom")
									}}</span>
									<input
										v-model.number="pageSettings.margins.bottom"
										type="number"
										:placeholder="__('Bottom')"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">{{
										__("Left")
									}}</span>
									<input
										v-model.number="pageSettings.margins.left"
										type="number"
										:placeholder="__('Left')"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">{{
										__("Right")
									}}</span>
									<input
										v-model.number="pageSettings.margins.right"
										type="number"
										:placeholder="__('Right')"
										class="form-control settings-pane__input"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>
				<div class="settings-pane__section-card card">
					<button
						v-if="isReportMode"
						type="button"
						class="btn btn-link card-header settings-pane__section-header"
						:class="{ 'is-expanded': isReportTemplateExpanded }"
						@click="isReportTemplateExpanded = !isReportTemplateExpanded"
					>
						<span>{{ __("Report Template") }}</span>
						<svg
							:class="[
								'settings-pane__chevron',
								{ 'settings-pane__chevron--expanded': isReportTemplateExpanded },
							]"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
					<div
						v-if="isReportMode && isReportTemplateExpanded"
						class="settings-pane__section-content card-body"
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
					</div>
				</div>
				<div v-if="isReportMode" class="settings-pane__section-card card">
					<button
						type="button"
						class="btn btn-link card-header settings-pane__section-header"
						:class="{ 'is-expanded': isChartExpanded }"
						@click="isChartExpanded = !isChartExpanded"
					>
						<span>{{ __("Chart Settings") }}</span>
						<svg
							:class="[
								'settings-pane__chevron',
								{ 'settings-pane__chevron--expanded': isChartExpanded },
							]"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>
					<div v-if="isChartExpanded" class="settings-pane__section-content card-body">
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
					</div>
				</div>
				<div v-if="!isReportMode" class="settings-pane__section-card card">
					<button
						type="button"
						class="btn btn-link card-header settings-pane__section-header"
						:class="{ 'is-expanded': isTypographyExpanded }"
						@click="isTypographyExpanded = !isTypographyExpanded"
					>
						<span>{{ __("Typography") }}</span>
						<svg
							:class="[
								'settings-pane__chevron',
								{ 'settings-pane__chevron--expanded': isTypographyExpanded },
							]"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>

					<div
						v-if="isTypographyExpanded"
						class="settings-pane__section-content card-body"
					>
						<!-- Section Labels -->
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">{{ __("Section Labels") }}</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Family")
									}}</label>
									<select
										v-model="typography.sectionLabel.fontFamily"
										class="form-control"
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
										__("Size (pt)")
									}}</label>
									<input
										v-model.number="sectionLabelFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Style")
									}}</label>
									<select
										v-model="typography.sectionLabel.fontStyle"
										class="form-control"
									>
										<option value="normal">{{ __("Normal") }}</option>
										<option value="italic">{{ __("Italic") }}</option>
										<option value="oblique">{{ __("Oblique") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Weight")
									}}</label>
									<select
										v-model="typography.sectionLabel.fontWeight"
										class="form-control"
									>
										<option value="thin">{{ __("Thin") }}</option>
										<option value="extralight">{{ __("Extralight") }}</option>
										<option value="light">{{ __("Light") }}</option>
										<option value="regular">{{ __("Regular") }}</option>
										<option value="medium">{{ __("Medium") }}</option>
										<option value="semibold">{{ __("Semibold") }}</option>
										<option value="bold">{{ __("Bold") }}</option>
										<option value="extrabold">{{ __("Extrabold") }}</option>
										<option value="black">{{ __("Black") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Color")
									}}</label>
									<ColorInput v-model="typography.sectionLabel.color" />
								</div>
							</div>
						</div>
						<!-- Field Labels -->
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">{{ __("Field Labels") }}</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Family")
									}}</label>
									<select
										v-model="typography.fieldLabel.fontFamily"
										class="form-control"
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
										__("Size (pt)")
									}}</label>
									<input
										v-model.number="fieldLabelFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Style")
									}}</label>
									<select
										v-model="typography.fieldLabel.fontStyle"
										class="form-control"
									>
										<option value="normal">{{ __("Normal") }}</option>
										<option value="italic">{{ __("Italic") }}</option>
										<option value="oblique">{{ __("Oblique") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Weight")
									}}</label>
									<select
										v-model="typography.fieldLabel.fontWeight"
										class="form-control"
									>
										<option value="thin">{{ __("Thin") }}</option>
										<option value="extralight">{{ __("Extralight") }}</option>
										<option value="light">{{ __("Light") }}</option>
										<option value="regular">{{ __("Regular") }}</option>
										<option value="medium">{{ __("Medium") }}</option>
										<option value="semibold">{{ __("Semibold") }}</option>
										<option value="bold">{{ __("Bold") }}</option>
										<option value="extrabold">{{ __("Extrabold") }}</option>
										<option value="black">{{ __("Black") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Color")
									}}</label>
									<ColorInput v-model="typography.fieldLabel.color" />
								</div>
							</div>
						</div>
						<!-- Field Values -->
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">{{ __("Field Values") }}</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Family")
									}}</label>
									<select
										v-model="typography.fieldValue.fontFamily"
										class="form-control"
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
										__("Size (pt)")
									}}</label>
									<input
										v-model.number="fieldValueFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Style")
									}}</label>
									<select
										v-model="typography.fieldValue.fontStyle"
										class="form-control"
									>
										<option value="normal">{{ __("Normal") }}</option>
										<option value="italic">{{ __("Italic") }}</option>
										<option value="oblique">{{ __("Oblique") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Weight")
									}}</label>
									<select
										v-model="typography.fieldValue.fontWeight"
										class="form-control"
									>
										<option value="thin">{{ __("Thin") }}</option>
										<option value="extralight">{{ __("Extralight") }}</option>
										<option value="light">{{ __("Light") }}</option>
										<option value="regular">{{ __("Regular") }}</option>
										<option value="medium">{{ __("Medium") }}</option>
										<option value="semibold">{{ __("Semibold") }}</option>
										<option value="bold">{{ __("Bold") }}</option>
										<option value="extrabold">{{ __("Extrabold") }}</option>
										<option value="black">{{ __("Black") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Color")
									}}</label>
									<ColorInput v-model="typography.fieldValue.color" />
								</div>
							</div>
						</div>
					</div>
				</div>
				<div class="settings-pane__section-card card">
					<button
						type="button"
						class="btn btn-link card-header settings-pane__section-header"
						:class="{ 'is-expanded': isTableExpanded }"
						@click="isTableExpanded = !isTableExpanded"
					>
						<span>{{ __("Table Settings") }}</span>
						<svg
							:class="[
								'settings-pane__chevron',
								{ 'settings-pane__chevron--expanded': isTableExpanded },
							]"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>

					<div v-if="isTableExpanded" class="settings-pane__section-content card-body">
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">{{ __("Spacing (pt)") }}</label>
							<div class="settings-pane__margins">
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">{{
										__("Top")
									}}</span>
									<input
										v-model.number="tableSettings.inset.top"
										type="number"
										:placeholder="__('Top')"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">{{
										__("Bottom")
									}}</span>
									<input
										v-model.number="tableSettings.inset.bottom"
										type="number"
										:placeholder="__('Bottom')"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">{{
										__("Left")
									}}</span>
									<input
										v-model.number="tableSettings.inset.left"
										type="number"
										:placeholder="__('Left')"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">{{
										__("Right")
									}}</span>
									<input
										v-model.number="tableSettings.inset.right"
										type="number"
										:placeholder="__('Right')"
										class="form-control settings-pane__input"
									/>
								</div>
							</div>
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
								__("Header Typography")
							}}</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Header Family")
									}}</label>
									<select
										v-model="tableSettings.typography.header.fontFamily"
										class="form-control"
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
										__("Header Size (pt)")
									}}</label>
									<input
										v-model.number="tableHeaderFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Header Style")
									}}</label>
									<select
										v-model="tableSettings.typography.header.fontStyle"
										class="form-control"
									>
										<option value="normal">{{ __("Normal") }}</option>
										<option value="italic">{{ __("Italic") }}</option>
										<option value="oblique">{{ __("Oblique") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Header Weight")
									}}</label>
									<select
										v-model="tableSettings.typography.header.fontWeight"
										class="form-control"
									>
										<option value="thin">{{ __("Thin") }}</option>
										<option value="extralight">{{ __("Extralight") }}</option>
										<option value="light">{{ __("Light") }}</option>
										<option value="regular">{{ __("Regular") }}</option>
										<option value="medium">{{ __("Medium") }}</option>
										<option value="semibold">{{ __("Semibold") }}</option>
										<option value="bold">{{ __("Bold") }}</option>
										<option value="extrabold">{{ __("Extrabold") }}</option>
										<option value="black">{{ __("Black") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Header Color")
									}}</label>
									<ColorInput v-model="tableSettings.typography.header.color" />
								</div>
							</div>
						</div>

						<div class="settings-pane__subsection">
							<label class="settings-pane__label">{{ __("Body Typography") }}</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Body Family")
									}}</label>
									<select
										v-model="tableSettings.typography.body.fontFamily"
										class="form-control"
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
										__("Body Size (pt)")
									}}</label>
									<input
										v-model.number="tableBodyFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Body Style")
									}}</label>
									<select
										v-model="tableSettings.typography.body.fontStyle"
										class="form-control"
									>
										<option value="normal">{{ __("Normal") }}</option>
										<option value="italic">{{ __("Italic") }}</option>
										<option value="oblique">{{ __("Oblique") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Body Weight")
									}}</label>
									<select
										v-model="tableSettings.typography.body.fontWeight"
										class="form-control"
									>
										<option value="thin">{{ __("Thin") }}</option>
										<option value="extralight">{{ __("Extralight") }}</option>
										<option value="light">{{ __("Light") }}</option>
										<option value="regular">{{ __("Regular") }}</option>
										<option value="medium">{{ __("Medium") }}</option>
										<option value="semibold">{{ __("Semibold") }}</option>
										<option value="bold">{{ __("Bold") }}</option>
										<option value="extrabold">{{ __("Extrabold") }}</option>
										<option value="black">{{ __("Black") }}</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("Body Color")
									}}</label>
									<ColorInput v-model="tableSettings.typography.body.color" />
								</div>
							</div>
						</div>
					</div>
				</div>

				<div class="settings-pane__section-card card">
					<button
						type="button"
						class="btn btn-link card-header settings-pane__section-header"
						:class="{ 'is-expanded': isBrandingExpanded }"
						@click="isBrandingExpanded = !isBrandingExpanded"
					>
						<span>{{ __("Branding") }}</span>
						<svg
							:class="[
								'settings-pane__chevron',
								{ 'settings-pane__chevron--expanded': isBrandingExpanded },
							]"
							xmlns="http://www.w3.org/2000/svg"
							viewBox="0 0 20 20"
							fill="currentColor"
						>
							<path
								fill-rule="evenodd"
								d="M5.23 7.21a.75.75 0 011.06.02L10 11.168l3.71-3.938a.75.75 0 111.08 1.04l-4.25 4.5a.75.75 0 01-1.08 0l-4.25-4.5a.75.75 0 01.02-1.06z"
								clip-rule="evenodd"
							/>
						</svg>
					</button>

					<div
						v-if="isBrandingExpanded"
						class="settings-pane__section-content card-body"
					>
						<div class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Type") }}</label>
							<select v-model="brandingMode" class="form-control">
								<option value="none">{{ __("None") }}</option>
								<option value="letterhead">{{ __("Letterhead") }}</option>
								<option value="logo">{{ __("Logo") }}</option>
							</select>
						</div>

						<div v-if="brandingMode === 'letterhead'" class="settings-pane__field">
							<label class="settings-pane__label">{{ __("Letterhead") }}</label>
							<select v-model="pageSettings.letterhead" class="form-control">
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

						<div v-if="brandingMode === 'logo'">
							<p class="settings-pane__hint">
								{{ __("Logo is anchored to top-left using #place().") }}
							</p>
							<div class="settings-pane__field">
								<label class="settings-pane__label">{{ __("Company") }}</label>
								<select v-model="logoSettings.company" class="form-control">
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
							<p
								v-if="logoSettings.company && !logoSettings.image"
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
										v-model.number="logoSettings.size"
										type="number"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("dx (mm)")
									}}</label>
									<input
										v-model.number="logoSettings.dx"
										type="number"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">{{
										__("dy (mm)")
									}}</label>
									<input
										v-model.number="logoSettings.dy"
										type="number"
										class="form-control"
									/>
								</div>
							</div>
						</div>
					</div>
				</div>

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
					<span class="label-area settings-pane__label">{{ __("Enable QR Code") }}</span>
					<span class="ml-1 help"></span>
				</label>

				<div v-if="!isReportMode && qrSettings.enabled" class="settings-pane__section">
					<div class="settings-pane__section-card card">
						<button
							type="button"
							class="btn btn-link card-header settings-pane__section-header"
							:class="{ 'is-expanded': isQrExpanded }"
							@click="isQrExpanded = !isQrExpanded"
						>
							<span>{{ __("QR-Code") }}</span>
							<svg
								class="settings-pane__chevron"
								:class="{ 'settings-pane__chevron--expanded': isQrExpanded }"
								viewBox="0 0 20 20"
								fill="none"
								stroke="currentColor"
								stroke-width="2"
							>
								<path d="M6 8l4 4 4-4" />
							</svg>
						</button>
						<div v-if="isQrExpanded" class="settings-pane__section-content card-body">
							<p class="settings-pane__hint">
								{{ __("QR Code is anchored to bottom-left using #place().") }}
							</p>
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
						</div>
					</div>
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
	ensureLogoSettings,
	ensureQrSettings,
	ensureTableSettings,
	ensureTypography,
	type PageSettings,
	type TableSettings,
	type TypographySettings,
} from "../utils/pageSettings";
import ColorInput from "./ColorInput.vue";
import { fetchTypstFonts, formatPt, parseSize } from "../utils/typstTypography";
import { useBrandingData } from "../composables/useBrandingData";
import { useStore } from "../composables/useStore";
import QrFieldsDialog from "./QrFieldsDialog.vue";
import { getLogger } from "../logger";
import { getDefaultReportBuilderConfig } from "../utils/reportBuilder";
import { __ } from "../utils/i18n";

interface Props {
	pageSettings: PageSettings;
	markDirty: () => void;
}

const props = defineProps<Props>();
const logger = getLogger({ component: "SettingsPane" });

const availableFonts = ref<string[]>([]);
const loadingFonts = ref(false);
const {
	availableLetterheads,
	loadingLetterheads,
	availableCompanies,
	loadingCompanies,
	resolveCompanyLogo,
	fetchLetterheads,
	fetchCompanies,
} = useBrandingData();
const isPageSettingsExpanded = ref(false);
const isTypographyExpanded = ref(false);
const isTableExpanded = ref(false);
const isReportTemplateExpanded = ref(false);
const isChartExpanded = ref(false);
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

// Initialize typography with defaults if not present
const typography = computed<TypographySettings>(() => {
	return ensureTypography(props.pageSettings);
});

const tableSettings = ref<TableSettings>(ensureTableSettings(props.pageSettings));
const syncedTableRef = ref(false);

const logoSettings = computed(() => ensureLogoSettings(props.pageSettings));

const qrSettings = computed(() => ensureQrSettings(props.pageSettings));

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

const brandingMode = computed<string>({
	get: () => {
		const mode = props.pageSettings.brandingMode;
		if (mode === "letterhead" || mode === "logo" || mode === "none") {
			return mode;
		}
		if (props.pageSettings.logo?.company || props.pageSettings.logo?.image) {
			return "logo";
		}
		if (props.pageSettings.letterhead) {
			return "letterhead";
		}
		return "none";
	},
	set: (value) => {
		props.pageSettings.brandingMode = value as "letterhead" | "logo" | "none";
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

const sectionLabelFontSizePt = computed<number>({
	get: () => Math.max(1, parseSize(typography.value.sectionLabel.fontSize).value || 0),
	set: (value) => {
		typography.value.sectionLabel.fontSize = formatPt(value);
	},
});

const fieldLabelFontSizePt = computed<number>({
	get: () => Math.max(1, parseSize(typography.value.fieldLabel.fontSize).value || 0),
	set: (value) => {
		typography.value.fieldLabel.fontSize = formatPt(value);
	},
});

const fieldValueFontSizePt = computed<number>({
	get: () => Math.max(1, parseSize(typography.value.fieldValue.fontSize).value || 0),
	set: (value) => {
		typography.value.fieldValue.fontSize = formatPt(value);
	},
});

const tableHeaderFontSizePt = computed<number>({
	get: () => Math.max(1, parseSize(tableSettings.value.typography.header.fontSize).value || 0),
	set: (value) => {
		tableSettings.value.typography.header.fontSize = formatPt(value);
	},
});

const tableBodyFontSizePt = computed<number>({
	get: () => Math.max(1, parseSize(tableSettings.value.typography.body.fontSize).value || 0),
	set: (value) => {
		tableSettings.value.typography.body.fontSize = formatPt(value);
	},
});

onMounted(() => {
	fetchFonts();
	fetchLetterheads();
	fetchCompanies();
});

watch(
	() => props.pageSettings,
	(nextSettings) => {
		if (syncedTableRef.value && nextSettings.table === tableSettings.value) {
			return;
		}
		tableSettings.value = ensureTableSettings(nextSettings);
		syncedTableRef.value = true;
	},
	{ immediate: true }
);

watch(
	() => props.pageSettings,
	() => {
		// Don't mark dirty during initial load
		if (!store.loading.value && !store.initializing.value) {
			props.markDirty();
		}
	},
	{ deep: true }
);

watch(
	() => logoSettings.value.company,
	(newCompany) => {
		logoSettings.value.image = resolveCompanyLogo(newCompany);
	}
);

watch(availableCompanies, () => {
	if (!logoSettings.value.company) return;
	logoSettings.value.image = resolveCompanyLogo(logoSettings.value.company);
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
	padding: 0 0 8px;
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
	padding: 12px 16px;
}

.settings-pane__form {
	display: flex;
	flex-direction: column;
	gap: 16px;
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

.settings-pane__margins {
	display: grid;
	grid-template-columns: repeat(2, minmax(0, 1fr));
	gap: 8px;
}

.settings-pane__margin-input {
	position: relative;
}

.settings-pane__margin-prefix {
	position: absolute;
	left: 10px;
	top: 50%;
	transform: translateY(-50%);
	font-size: 10px;
	font-weight: 600;
	pointer-events: none;
}

.settings-pane__margin-input .settings-pane__input {
	padding-left: 50px;
}

.settings-pane__margin-input .form-control {
	padding-left: 50px;
}

.settings-pane__section {
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.settings-pane__section-card {
	border: 1px solid #e2e8f0;
	border-radius: 12px;
	overflow: hidden;
	background: #fff;
}

.settings-pane__section-header {
	display: flex;
	align-items: center;
	justify-content: space-between;
	width: 100%;
	cursor: pointer;
	margin: 0;
	padding: 10px 12px;
	text-align: left;
	background: #fff;
	color: #334155;
	border: none;
	text-decoration: none;
}

.settings-pane__section-header.is-expanded {
	border-left: 0;
	padding-left: 12px;
}

.settings-pane__section-header:hover {
	background: #f8fafc;
	color: #334155;
	text-decoration: none;
}

.settings-pane__section-header:focus {
	background: #fff;
	color: #334155;
	text-decoration: none;
	outline: none;
	box-shadow: none;
}

.settings-pane__section-header:focus-visible {
	background: #f8fafc;
	outline: 2px solid #cbd5e1;
	outline-offset: -2px;
}

.settings-pane__chevron {
	width: 16px;
	height: 16px;
	/* transform-origin: right center; */
	transition: transform 0.2s ease;
}

.settings-pane__chevron--expanded {
	transform: rotate(-180deg);
}

.settings-pane__section-content {
	display: flex;
	flex-direction: column;
	gap: 12px;
	padding: 12px;
	border-top: 1px solid #e2e8f0;
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
