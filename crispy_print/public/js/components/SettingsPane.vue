<template>
	<div class="settings-pane">
		<div class="section-head settings-pane__header">
			<div class="section-head-content settings-pane__header-row">
				<h3 class="section-title settings-pane__title">Typst Settings</h3>
				<div class="settings-pane__spacer"></div>
				<div>
					<button
						type="button"
						class="btn btn-default btn-xs settings-pane__help-btn"
						popovertarget="settings-help"
						popovertargetaction="toggle"
						title="Toggle help"
						aria-haspopup="dialog"
						aria-controls="settings-help"
					>
						?
					</button>
					<div id="settings-help" popover class="settings-pane__help-popover">
						<ul class="settings-pane__help-list">
							<li>Configure page size, margins, and typography for Typst.</li>
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
						<span>Page Settings</span>
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
							<label class="settings-pane__label">Size</label>
							<select v-model="pageSettings.pageSize" class="form-control">
								<option value="A3">A3 (297 × 420 mm)</option>
								<option value="A4">A4 (210 × 297 mm)</option>
								<option value="A5">A5 (148 × 210 mm)</option>
								<option value="Letter">Letter (8.5 × 11 in)</option>
								<option value="Legal">Legal (8.5 × 14 in)</option>
								<option value="Tabloid">Tabloid (11 × 17 in)</option>
								<option value="Executive">Executive (7.25 × 10.5 in)</option>
							</select>
						</div>

						<div class="settings-pane__field">
							<label class="settings-pane__label">Orientation</label>
							<select v-model="pageSettings.orientation" class="form-control">
								<option value="portrait">Portrait</option>
								<option value="landscape">Landscape</option>
							</select>
						</div>

						<div class="settings-pane__field">
							<label class="settings-pane__label">Margins (mm)</label>
							<div class="settings-pane__margins">
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">top</span>
									<input
										v-model.number="pageSettings.margins.top"
										type="number"
										placeholder="Top"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">bottom</span>
									<input
										v-model.number="pageSettings.margins.bottom"
										type="number"
										placeholder="Bottom"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">left</span>
									<input
										v-model.number="pageSettings.margins.left"
										type="number"
										placeholder="Left"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">right</span>
									<input
										v-model.number="pageSettings.margins.right"
										type="number"
										placeholder="Right"
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
						<span>Report Template</span>
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
							<label class="settings-pane__label">Preset</label>
							<select
								v-model="reportBuilderConfig.preset"
								class="form-control"
								:disabled="reportBasicReadOnly"
							>
								<option value="grid">Grid</option>
								<option value="tree">Tree</option>
								<option value="summary">Summary</option>
								<option value="minimal">Minimal</option>
							</select>
						</div>
						<div class="settings-pane__grid">
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">Font Family</label>
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
								<label class="settings-pane__sublabel">Font Size (pt)</label>
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
								<label class="settings-pane__sublabel">Show Filters</label>
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
								<label class="settings-pane__sublabel">Show Summary</label>
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
								<label class="settings-pane__sublabel">Show Total Row</label>
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
						<span>Chart Settings</span>
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
								<label class="settings-pane__sublabel">Enable Chart</label>
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
								<label class="settings-pane__sublabel">Card Border</label>
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
								<label class="settings-pane__sublabel">Chart Width (%)</label>
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
								<label class="settings-pane__sublabel">Max Height (pt)</label>
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
								<label class="settings-pane__sublabel">Spacing Top (pt)</label>
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
								<label class="settings-pane__sublabel">Spacing Bottom (pt)</label>
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
						<span>Typography</span>
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
							<label class="settings-pane__label">Section Labels</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Family</label>
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
									<label class="settings-pane__sublabel">Size (pt)</label>
									<input
										v-model.number="sectionLabelFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Style</label>
									<select
										v-model="typography.sectionLabel.fontStyle"
										class="form-control"
									>
										<option value="normal">Normal</option>
										<option value="italic">Italic</option>
										<option value="oblique">Oblique</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Weight</label>
									<select
										v-model="typography.sectionLabel.fontWeight"
										class="form-control"
									>
										<option value="thin">Thin</option>
										<option value="extralight">Extralight</option>
										<option value="light">Light</option>
										<option value="regular">Regular</option>
										<option value="medium">Medium</option>
										<option value="semibold">Semibold</option>
										<option value="bold">Bold</option>
										<option value="extrabold">Extrabold</option>
										<option value="black">Black</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Color</label>
									<ColorInput v-model="typography.sectionLabel.color" />
								</div>
							</div>
						</div>
						<!-- Field Labels -->
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Field Labels</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Family</label>
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
									<label class="settings-pane__sublabel">Size (pt)</label>
									<input
										v-model.number="fieldLabelFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Style</label>
									<select
										v-model="typography.fieldLabel.fontStyle"
										class="form-control"
									>
										<option value="normal">Normal</option>
										<option value="italic">Italic</option>
										<option value="oblique">Oblique</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Weight</label>
									<select
										v-model="typography.fieldLabel.fontWeight"
										class="form-control"
									>
										<option value="thin">Thin</option>
										<option value="extralight">Extralight</option>
										<option value="light">Light</option>
										<option value="regular">Regular</option>
										<option value="medium">Medium</option>
										<option value="semibold">Semibold</option>
										<option value="bold">Bold</option>
										<option value="extrabold">Extrabold</option>
										<option value="black">Black</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Color</label>
									<ColorInput v-model="typography.fieldLabel.color" />
								</div>
							</div>
						</div>
						<!-- Field Values -->
						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Field Values</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Family</label>
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
									<label class="settings-pane__sublabel">Size (pt)</label>
									<input
										v-model.number="fieldValueFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Style</label>
									<select
										v-model="typography.fieldValue.fontStyle"
										class="form-control"
									>
										<option value="normal">Normal</option>
										<option value="italic">Italic</option>
										<option value="oblique">Oblique</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Weight</label>
									<select
										v-model="typography.fieldValue.fontWeight"
										class="form-control"
									>
										<option value="thin">Thin</option>
										<option value="extralight">Extralight</option>
										<option value="light">Light</option>
										<option value="regular">Regular</option>
										<option value="medium">Medium</option>
										<option value="semibold">Semibold</option>
										<option value="bold">Bold</option>
										<option value="extrabold">Extrabold</option>
										<option value="black">Black</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Color</label>
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
						<span>Table Settings</span>
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
							<label class="settings-pane__label">Spacing (pt)</label>
							<div class="settings-pane__margins">
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">top</span>
									<input
										v-model.number="tableSettings.inset.top"
										type="number"
										placeholder="Top"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">bottom</span>
									<input
										v-model.number="tableSettings.inset.bottom"
										type="number"
										placeholder="Bottom"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">left</span>
									<input
										v-model.number="tableSettings.inset.left"
										type="number"
										placeholder="Left"
										class="form-control settings-pane__input"
									/>
								</div>
								<div class="settings-pane__margin-input">
									<span class="settings-pane__margin-prefix">right</span>
									<input
										v-model.number="tableSettings.inset.right"
										type="number"
										placeholder="Right"
										class="form-control settings-pane__input"
									/>
								</div>
							</div>
						</div>

						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Borders</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Stroke (pt)</label>
									<input
										v-model.number="tableSettings.stroke.width"
										type="number"
										min="0"
										step="0.1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Color</label>
									<ColorInput v-model="tableSettings.stroke.color" />
								</div>
							</div>
						</div>

						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Colors</label>
							<div class="settings-pane__grid settings-pane__grid--colors">
								<div class="settings-pane__field settings-pane__field--span">
									<label class="settings-pane__sublabel"
										>Header Background</label
									>
									<ColorInput v-model="tableSettings.header.backgroundColor" />
								</div>
							</div>
							<div class="settings-pane__grid settings-pane__grid--stripe">
								<div class="settings-pane__field settings-pane__field--toggle">
									<label class="settings-pane__sublabel">Striping</label>
									<div class="settings-pane__checkbox-wrap">
										<input
											v-model="tableSettings.stripe.enabled"
											type="checkbox"
											class="form-check-input settings-pane__checkbox settings-pane__checkbox--inline"
										/>
									</div>
								</div>
								<div class="settings-pane__field settings-pane__field--color">
									<label class="settings-pane__sublabel">Stripe Color</label>
									<ColorInput
										v-model="tableSettings.stripe.color"
										:disabled="!tableSettings.stripe.enabled"
									/>
								</div>
							</div>
						</div>

						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Header Typography</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Header Family</label>
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
									<label class="settings-pane__sublabel">Header Size (pt)</label>
									<input
										v-model.number="tableHeaderFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Header Style</label>
									<select
										v-model="tableSettings.typography.header.fontStyle"
										class="form-control"
									>
										<option value="normal">Normal</option>
										<option value="italic">Italic</option>
										<option value="oblique">Oblique</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Header Weight</label>
									<select
										v-model="tableSettings.typography.header.fontWeight"
										class="form-control"
									>
										<option value="thin">Thin</option>
										<option value="extralight">Extralight</option>
										<option value="light">Light</option>
										<option value="regular">Regular</option>
										<option value="medium">Medium</option>
										<option value="semibold">Semibold</option>
										<option value="bold">Bold</option>
										<option value="extrabold">Extrabold</option>
										<option value="black">Black</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Header Color</label>
									<ColorInput v-model="tableSettings.typography.header.color" />
								</div>
							</div>
						</div>

						<div class="settings-pane__subsection">
							<label class="settings-pane__label">Body Typography</label>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Body Family</label>
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
									<label class="settings-pane__sublabel">Body Size (pt)</label>
									<input
										v-model.number="tableBodyFontSizePt"
										type="number"
										min="1"
										step="1"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Body Style</label>
									<select
										v-model="tableSettings.typography.body.fontStyle"
										class="form-control"
									>
										<option value="normal">Normal</option>
										<option value="italic">Italic</option>
										<option value="oblique">Oblique</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Body Weight</label>
									<select
										v-model="tableSettings.typography.body.fontWeight"
										class="form-control"
									>
										<option value="thin">Thin</option>
										<option value="extralight">Extralight</option>
										<option value="light">Light</option>
										<option value="regular">Regular</option>
										<option value="medium">Medium</option>
										<option value="semibold">Semibold</option>
										<option value="bold">Bold</option>
										<option value="extrabold">Extrabold</option>
										<option value="black">Black</option>
									</select>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Body Color</label>
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
						<span>Branding</span>
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
							<label class="settings-pane__label">Type</label>
							<select v-model="brandingMode" class="form-control">
								<option value="none">None</option>
								<option value="letterhead">Letterhead</option>
								<option value="logo">Logo</option>
							</select>
						</div>

						<div v-if="brandingMode === 'letterhead'" class="settings-pane__field">
							<label class="settings-pane__label">Letterhead</label>
							<select v-model="pageSettings.letterhead" class="form-control">
								<option value="">None</option>
								<option v-if="loadingLetterheads" disabled>
									Loading letterheads...
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
								Logo is anchored to top-left using #place().
							</p>
							<div class="settings-pane__field">
								<label class="settings-pane__label">Company</label>
								<select v-model="logoSettings.company" class="form-control">
									<option value="">Select company</option>
									<option v-if="loadingCompanies" disabled>
										Loading companies...
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
								Selected company has no logo set.
							</p>
							<div class="settings-pane__grid">
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">Size (mm)</label>
									<input
										v-model.number="logoSettings.size"
										type="number"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">dx (mm)</label>
									<input
										v-model.number="logoSettings.dx"
										type="number"
										class="form-control"
									/>
								</div>
								<div class="settings-pane__field">
									<label class="settings-pane__sublabel">dy (mm)</label>
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
					<span class="label-area settings-pane__label">Enable QR Code</span>
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
							<span>QR-Code</span>
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
								QR Code is anchored to bottom-left using #place().
							</p>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">Size (mm)</label>
								<input
									v-model.number="qrSettings.size"
									type="number"
									class="form-control"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">dx (mm)</label>
								<input
									v-model.number="qrSettings.dx"
									type="number"
									class="form-control"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">dy (mm)</label>
								<input
									v-model.number="qrSettings.dy"
									type="number"
									class="form-control"
								/>
							</div>
							<div class="settings-pane__field">
								<label class="settings-pane__sublabel">QR fields</label>
								<div class="settings-pane__qr-row">
									<button
										type="button"
										class="btn btn-default btn-xs settings-pane__qr-btn"
										@click="showQrDialog = true"
									>
										Select fields
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
	if (!count) return "No fields selected";
	if (count === 1) return "1 field selected";
	return `${count} fields selected`;
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
}

.settings-pane__header-row {
	align-items: center;
}

.settings-pane__help-btn:hover {
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
