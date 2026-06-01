// Crispy Print API wrappers (typed).

import { call, getDoc, getList, setValue } from "./frappe"
import type { PresentationSettings } from "../utils/presentation_settings"
import type { CrispyLayout } from "../utils/layout"

export interface CrispyFormatDoc {
	name: string
	doc_type?: string
	crispy_format_type?: string
	report?: string
	contract?: string
	is_default?: number
	is_generic?: number
	is_advanced?: number
	generic_report_type?: string
	doc_header?: string
	doc_footer?: string
	raw_typst?: number
	layout_json?: string
	presentation_settings?: string
	typst_code?: string
	typst_preamble?: string
	pdf_standard?: string
	__onload?: any
}

export interface CompanyOption {
	name: string
	abbr?: string
	company_logo?: string
}

export interface ExportPayload {
	schema_version: number
	exported_at: string
	app: string
	format: CrispyFormatDoc
}

export interface ConflictResult {
	schema_version: number
	name: string
	exists: boolean
	conflict: boolean
}

export interface ImportResult {
	success: boolean
	name: string
	warnings: string[]
	conflict_action: "copy" | "overwrite"
}

export interface ReportBuilderDefaults {
	mode: "basic" | "advanced"
	preset: "grid" | "tree" | "summary" | "minimal"
	show_filters: boolean
	show_summary: boolean
	include_total_row: boolean
	show_footer_total: boolean
	chart_enabled: boolean
	chart_width_percent: number
	chart_max_height_pt: number
	chart_card_border: boolean
	chart_spacing_top_pt: number
	chart_spacing_bottom_pt: number
	header_fill: string
	header_text_weight: string
	font_family: string
	font_size_pt: number
	row_striping: boolean
	row_stripe_fill: string
	column_align_strategy: "auto" | "left" | "center" | "right"
	table_inset_x_pt: number
	table_inset_y_pt: number
	table_stroke_top_pt: number
	table_stroke_body_pt: number
	raw_signature: string | null
	report_table_sync_signature: string | null
}

export interface FiscalCredentialPublicInfo {
	name: string
	credential_name?: string
	enabled?: number
	company?: string
	country?: string
	authority_code?: string
	regulatory_profile?: string
	environment?: "Sandbox" | "Production"
	valid_from?: string | null
	valid_until?: string | null
	modified?: string
	expired?: boolean
	not_yet_valid?: boolean
}

export interface FiscalCredentialStatus {
	exists: boolean
	valid: boolean
	credential: FiscalCredentialPublicInfo | null
	warnings: string[]
}

export interface DocumentCodeResolved {
	profile_name: string
	company: string
	environment: "Sandbox" | "Production"
	code_purpose: string
	document_role?: string | null
	code_format?: string
	code_symbology?: string | null
	payload_format?: string
	output_encoding?: string
	error_correction?: string | null
	content_source?: string
	payload_template?: string | null
	selected_fields?: string[] | Record<string, string>
	field_mapping?: Record<string, string>
	encoder_key?: string
	encoder_settings?: Record<string, unknown>
	requires_signature?: boolean
	signature_method?: string | null
	include_hash?: boolean
	hash_method?: string | null
	requires_verification_url?: boolean
	verification_url_template?: string | null
	presentation?: Record<string, unknown>
	matched_rules?: string[]
	document?: { doctype: string; name: string }
	regulatory_profile?: Record<string, unknown> | null
	fiscal_credential?: Record<string, unknown> | null
}

export interface DocumentCodeGenerated extends DocumentCodeResolved {
	payload: unknown
	encoded_value: string
}

export interface QRRegulatoryProfile {
	name: string
	profile_name?: string
	enabled?: number
	country?: string | null
	authority_code?: string | null
	standard?: string
	version?: string | null
	payload_format?: "Custom" | "TLV" | "JSON" | "XML" | "URL" | "Text"
	output_encoding?: "Plain Text" | "Base64" | "URL Encoded"
	error_correction?: "Low" | "Medium" | "Quartile" | "High"
	include_signature?: number
	include_hash?: number
	requires_online_verification?: number
	verification_url_template?: string | null
	encoder_key?: string
	encoder_settings_json?: string | Record<string, unknown> | null
}

export interface CrispyTypstBlockOption {
	name: string
	block_key: string
	block_name: string
	enabled?: number
	category?: string
	description?: string
	typst_code: string
	version?: string
}

export interface CrispyBrandingProfileOption {
	name: string
	profile_name: string
	company: string
	is_default?: number
	branding_mode?: "None" | "Logo Only" | "Letterhead Only" | "Logo + Letterhead"
	modified?: string
}

export interface CrispyBrandingProfileDoc extends CrispyBrandingProfileOption {
	page_size?: string
	orientation?: string
	margin_top_mm?: number
	margin_bottom_mm?: number
	margin_left_mm?: number
	margin_right_mm?: number
	code_only?: number
	custom_typst_code?: string
	section_label_font_family?: string
	section_label_font_size_pt?: number
	section_label_font_style?: string
	section_label_font_weight?: string
	section_label_font_color?: string
	field_label_font_family?: string
	field_label_font_size_pt?: number
	field_label_font_style?: string
	field_label_font_weight?: string
	field_label_font_color?: string
	field_value_font_family?: string
	field_value_font_size_pt?: number
	field_value_font_style?: string
	field_value_font_weight?: string
	field_value_font_color?: string
	table_cell_inset_top_pt?: number
	table_cell_inset_right_pt?: number
	table_cell_inset_bottom_pt?: number
	table_cell_inset_left_pt?: number
	table_border_stroke_width_pt?: number
	table_border_color?: string
	table_header_background_color?: string
	table_row_striping?: number
	table_stripe_color?: string
	table_header_font_family?: string
	table_header_font_size_pt?: number
	table_header_font_style?: string
	table_header_font_weight?: string
	table_header_font_color?: string
	table_body_font_family?: string
	table_body_font_size_pt?: number
	table_body_font_style?: string
	table_body_font_weight?: string
	table_body_font_color?: string
	branding_logo_source?: "Company logo" | "Upload image"
	branding_logo_upload?: string
	branding_logo_width_mm?: number
	branding_logo_offset_x_mm?: number
	branding_logo_offset_y_mm?: number
	branding_letterhead_source?: "Use System Letterhead" | "Upload Letterhead"
	frappe_company_letterhead?: string
	branding_letterhead_upload?: string
	enable_qr_code?: number
	qr_code_size_mm?: number
	qr_dx_mm?: number
	qr_dy_mm?: number
}

export interface CrispyIssuedDocumentArtifact {
	artifact_type:
		| "Archival PDF"
		| "PDF/A"
		| "Rendered SVG"
		| "XML Payload"
		| "JSON Payload"
		| "Signature"
		| "Certificate"
		| "Authority Receipt"
		| "Other"
	file: string
	media_type?: string
	file_hash?: string
	hash_algorithm?: string
	page_number?: number
	is_primary?: number
	generated_at?: string
	notes?: string
}

export interface CrispyIssuedDocumentTrustEvent {
	event_type:
		| "Hash"
		| "Signature"
		| "Timestamp"
		| "Certificate"
		| "Validation"
		| "Revocation Check"
		| "Other"
	signature_format?: "PAdES" | "XAdES" | "CAdES/CMS" | "Detached" | "Embedded PDF" | "Other"
	signature_algorithm?: string
	digest_algorithm?: string
	signer_name?: string
	signer_certificate?: string
	certificate_fingerprint?: string
	certificate_subject?: string
	certificate_issuer?: string
	certificate_serial_number?: string
	signed_at?: string
	timestamp_token?: string
	timestamp_authority?: string
	validation_status?: "Pending" | "Valid" | "Invalid" | "Expired" | "Revoked" | "Unknown" | "Failed"
	validation_message?: string
	related_artifact?: string
}

export interface CrispyIssuedDocumentRegulatorySubmission {
	regulatory_profile?: string
	authority_code?: string
	environment: "Sandbox" | "Production"
	submission_type:
		| "Initial"
		| "Amendment"
		| "Cancellation"
		| "Credit Note"
		| "Debit Note"
		| "Validation"
		| "Sandbox Validation"
		| "Other"
	submission_status:
		| "Draft"
		| "Pending"
		| "Submitted"
		| "Accepted"
		| "Rejected"
		| "Failed"
		| "Cancelled"
		| "Superseded"
	submitted_at?: string
	authority_submission_id?: string
	authority_reference?: string
	request_payload?: string
	response_payload?: string
	response_code?: string
	response_message?: string
	related_artifact?: string
}

export interface CrispyIssuedDocument {
	name: string
	document_uuid: string
	verification_token: string
	source_doctype: string
	source_docname: string
	crispy_format: string
	issuance_status: "Draft" | "Issued" | "Failed" | "Revoked" | "Superseded"
	business_status: "Active" | "Cancelled" | "Revoked" | "Superseded" | "Expired"
	integrity_status: "Pending" | "Valid" | "Tampered" | "Corrupted" | "Unknown"
	issued_at?: string
	revoked?: number
	revoked_at?: string
	superseded_by?: string
	amended_from?: string
	canonical_payload_json?: string
	canonical_payload_hash?: string
	typst_source?: string
	typst_version?: string
	artifacts?: CrispyIssuedDocumentArtifact[]
	trust_events?: CrispyIssuedDocumentTrustEvent[]
	regulatory_submissions?: CrispyIssuedDocumentRegulatorySubmission[]
	verification_url?: string
}

export interface CrispyIssuedDocumentVerification {
	exists: boolean
	verification_status: "Valid" | "Revoked" | "Superseded" | "Tampered" | "Corrupted" | "Unknown" | "Not Found"
	name?: string
	document_uuid?: string
	issuance_status?: CrispyIssuedDocument["issuance_status"]
	business_status?: CrispyIssuedDocument["business_status"]
	integrity_status?: CrispyIssuedDocument["integrity_status"]
	issued_at?: string
	revoked?: boolean
	revoked_at?: string
	superseded_by?: string
	amended_from?: string
}

export interface TypstCompileResult {
	success: boolean
	format: "svg" | "pdf"
	svg_pages?: string[]
	page_count?: number
	pdf_data?: string
	pdf_url?: string
}

export async function compileTypst(args: {
	typst_source: string
	output_format: "svg" | "pdf"
	pdf_standard?: string | null
	asset_files?: string[]
	chart_svg?: string | null
}): Promise<TypstCompileResult> {
	const res = await call<TypstCompileResult>({
		method: "crispy_print.api.v1.compile_typst",
		args: {
			typst_source: args.typst_source,
			output_format: args.output_format,
			pdf_standard: args.pdf_standard || null,
			asset_files: args.asset_files || [],
			chart_svg: args.chart_svg || null,
		},
	})
	if (!res.message) {
		throw new Error("Missing Typst compile result")
	}
	return res.message
}

export async function compileReportPreview(args: Record<string, any>): Promise<TypstCompileResult & {
	typst_source?: string
	truncation?: Record<string, any>
	asset_files?: string[]
}> {
	const res = await call<TypstCompileResult & {
		typst_source?: string
		truncation?: Record<string, any>
		asset_files?: string[]
	}>({
		method: "crispy_print.api.v1.compile_report_preview",
		args,
	})
	if (!res.message) {
		throw new Error("Missing report preview result")
	}
	return res.message
}

export async function getCrispyFormat(name: string): Promise<CrispyFormatDoc> {
	const res = await call<CrispyFormatDoc>({
		method: "crispy_print.api.v1.get_crispy_format",
		args: { name },
	})
	if (!res.message) {
		throw new Error("Missing Crispy Format")
	}
	return res.message
}

export async function saveCrispyFormat(
	name: string,
	values: {
		layout_json?: string
		presentation_settings?: string
		doc_header?: string
		doc_footer?: string
		typst_code?: string
		typst_preamble?: string
		raw_typst?: number
		is_advanced?: number
	}
): Promise<void> {
	await setValue("Crispy Format", name, values)
}

export async function getCrispyFormatsForDoctype(
	doctype: string
): Promise<Array<{ name: string; doc_type: string; is_default?: number }>> {
	const res = await call<Array<{ name: string; doc_type: string; is_default?: number }>>({
		method: "crispy_print.api.v1.get_crispy_formats_for_doctype",
		args: { doctype },
	})
	return res.message || []
}

export async function getDefaultCrispyFormatForDoctype(doctype: string): Promise<string | null> {
	const rows = await getList<{ name: string }>("Crispy Format", {
		filters: { doc_type: doctype, is_default: 1 },
		fields: ["name"],
		limit: 1,
	})
	return rows.length ? rows[0].name : null
}

export async function getLetterheads(): Promise<string[]> {
	const rows = await getList<{ name: string }>("Letter Head", {
		fields: ["name"],
		order_by: "name asc",
	})
	return rows.map((r) => r.name)
}

export async function getLetterheadDoc(name: string): Promise<any> {
	return await getDoc<any>("Letter Head", name)
}

export async function getCompanies(): Promise<CompanyOption[]> {
	return await getList<CompanyOption>("Company", {
		fields: ["name", "abbr", "company_logo"],
		order_by: "name asc",
	})
}

export async function getTypstLocalFonts(): Promise<string[]> {
	const res = await call<string[]>({
		method: "crispy_print.api.v1.get_typst_local_fonts",
	})
	return res.message || []
}

export async function getApplicableTypstBlocks(args: {
	doctype: string
	query?: string | null
	category?: string | null
}): Promise<CrispyTypstBlockOption[]> {
	const res = await call<CrispyTypstBlockOption[]>({
		method: "crispy_print.api.v1.get_applicable_typst_blocks",
		args,
	})
	return res.message || []
}

export async function getBrandingProfiles(args: {
	company?: string | null
} = {}): Promise<CrispyBrandingProfileOption[]> {
	const res = await call<CrispyBrandingProfileOption[]>({
		method: "crispy_print.api.v1.get_branding_profiles",
		args,
	})
	return res.message || []
}

export async function getBrandingProfile(name: string): Promise<CrispyBrandingProfileDoc> {
	return await getDoc<CrispyBrandingProfileDoc>("Crispy Branding Profile", name)
}

export async function saveBrandingProfile(
	name: string,
	values: Partial<CrispyBrandingProfileDoc>
): Promise<void> {
	await setValue("Crispy Branding Profile", name, values)
}

export async function getBrandingProfilePresentationSettings(
	name: string
): Promise<Partial<PresentationSettings>> {
	const res = await call<Partial<PresentationSettings>>({
		method: "crispy_print.api.v1.get_branding_profile_presentation_settings",
		args: { name },
	})
	return res.message || {}
}

export async function compileTypstSvg(args: {
	typst_source: string
	asset_files?: string[]
	chart_svg?: string | null
}): Promise<TypstCompileResult> {
	return await compileTypst({
		...args,
		output_format: "svg",
	})
}

export async function getDefaultReportBuilderConfig(
	genericReportType?: string | null
): Promise<ReportBuilderDefaults> {
	const res = await call<ReportBuilderDefaults>({
		method: "crispy_print.api.v1.get_default_report_builder_config",
		args: { generic_report_type: genericReportType || null },
	})
	if (!res.message) {
		throw new Error("Missing report builder defaults")
	}
	return res.message
}

export async function getFiscalCredentialStatus(args: {
	company: string
	regulatory_profile: string
	environment?: "Sandbox" | "Production"
	authority_code?: string | null
}): Promise<FiscalCredentialStatus> {
	const res = await call<FiscalCredentialStatus>({
		method: "crispy_print.api.v1.get_fiscal_credential_status",
		args,
	})
	if (!res.message) {
		throw new Error("Missing fiscal credential status")
	}
	return res.message
}

export async function resolveDocumentCode(args: {
	doctype: string
	name: string
	code_purpose?: string
	environment?: "Sandbox" | "Production"
	document_role?: string | null
	company?: string | null
	profile_name?: string | null
}): Promise<DocumentCodeResolved> {
	const res = await call<DocumentCodeResolved>({
		method: "crispy_print.api.v1.resolve_document_code",
		args,
	})
	if (!res.message) {
		throw new Error("Missing document code resolution")
	}
	return res.message
}

export async function generateDocumentCode(args: {
	doctype: string
	name: string
	code_purpose?: string
	environment?: "Sandbox" | "Production"
	document_role?: string | null
	company?: string | null
	profile_name?: string | null
}): Promise<DocumentCodeGenerated> {
	const res = await call<DocumentCodeGenerated>({
		method: "crispy_print.api.v1.generate_document_code",
		args,
	})
	if (!res.message) {
		throw new Error("Missing generated document code")
	}
	return res.message
}

export async function getQRRegulatoryProfiles(args: {
	country?: string | null
	authority_code?: string | null
	enabled_only?: boolean | number
} = {}): Promise<QRRegulatoryProfile[]> {
	const res = await call<QRRegulatoryProfile[]>({
		method: "crispy_print.api.v1.get_qr_regulatory_profiles",
		args,
	})
	return res.message || []
}

export async function getQRRegulatoryProfile(name: string): Promise<QRRegulatoryProfile> {
	const res = await call<QRRegulatoryProfile>({
		method: "crispy_print.api.v1.get_qr_regulatory_profile",
		args: { name },
	})
	if (!res.message) {
		throw new Error("Missing QR regulatory profile")
	}
	return res.message
}

export async function getIssuedDocument(name: string): Promise<CrispyIssuedDocument> {
	const res = await call<CrispyIssuedDocument>({
		method: "crispy_print.api.v1.get_issued_document",
		args: { name },
	})
	if (!res.message) {
		throw new Error("Missing Crispy Issued Document")
	}
	return res.message
}

export async function getIssuedDocumentByToken(
	verificationToken: string
): Promise<CrispyIssuedDocument> {
	const res = await call<CrispyIssuedDocument>({
		method: "crispy_print.api.v1.get_issued_document_by_token",
		args: { verification_token: verificationToken },
	})
	if (!res.message) {
		throw new Error("Missing Crispy Issued Document")
	}
	return res.message
}

export async function verifyIssuedDocumentToken(
	verificationToken: string
): Promise<CrispyIssuedDocumentVerification> {
	const res = await call<CrispyIssuedDocumentVerification>({
		method: "crispy_print.api.v1.verify_issued_document_token",
		args: { verification_token: verificationToken },
	})
	if (!res.message) {
		throw new Error("Missing issued document verification result")
	}
	return res.message
}

export async function createIssuedDocumentSnapshot(args: {
	source_doctype: string
	source_docname: string
	crispy_format: string
}): Promise<CrispyIssuedDocument> {
	const res = await call<CrispyIssuedDocument>({
		method: "crispy_print.api.v1.create_issued_document_snapshot",
		args,
	})
	if (!res.message) {
		throw new Error("Missing issued document snapshot result")
	}
	return res.message
}

export function encodePresentationSettings(settings: PresentationSettings): string {
	return JSON.stringify(settings)
}

export function encodeLayout(layoutJson: CrispyLayout): string {
	return JSON.stringify(layoutJson)
}

export async function exportCrispyFormat(name: string): Promise<ExportPayload> {
	const res = await call<ExportPayload>({
		method: "crispy_print.api.v1.export_crispy_format",
		args: { name },
	})
	if (!res.message) {
		throw new Error("Missing export payload")
	}
	return res.message
}

export async function checkImportConflicts(payload: unknown): Promise<ConflictResult> {
	const res = await call<ConflictResult>({
		method: "crispy_print.api.v1.check_import_conflicts",
		args: { payload: typeof payload === "string" ? payload : JSON.stringify(payload) },
	})
	if (!res.message) {
		throw new Error("Missing conflict response")
	}
	return res.message
}

export async function importCrispyFormat(
	payload: unknown,
	onConflict: "copy" | "overwrite"
): Promise<ImportResult> {
	const res = await call<ImportResult>({
		method: "crispy_print.api.v1.import_crispy_format",
		args: {
			payload: typeof payload === "string" ? payload : JSON.stringify(payload),
			on_conflict: onConflict,
		},
	})
	if (!res.message) {
		throw new Error("Missing import response")
	}
	return res.message
}
