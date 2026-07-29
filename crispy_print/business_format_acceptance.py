"""Versioned acceptance contract for the core v1 business-format catalog."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BusinessFormatSpec:
	sample_id: str
	target_type: str
	target: str
	purpose: str
	required_fields: tuple[str, ...] = ()
	required_tables: tuple[str, ...] = ()
	page_size: str = "a4"
	variant: str = ""


CORE_V1_BUSINESS_FORMATS: tuple[BusinessFormatSpec, ...] = (
	BusinessFormatSpec(
		"payment-entry-voucher",
		"DocType",
		"Payment Entry",
		"Customer receipt and supplier payment voucher",
		(
			"payment_type",
			"posting_date",
			"party_name",
			"mode_of_payment",
			"paid_amount",
			"received_amount",
			"reference_no",
			"remarks",
		),
		("references",),
		"a5",
		"receive-or-pay",
	),
	BusinessFormatSpec(
		"remittance-advice",
		"DocType",
		"Payment Entry",
		"Supplier remittance advice with allocated references",
		("posting_date", "party_name", "paid_amount", "reference_no", "reference_date"),
		("references",),
		variant="supplier-remittance",
	),
	BusinessFormatSpec(
		"stock-entry-movement",
		"DocType",
		"Stock Entry",
		"Internal stock movement, issue, receipt, and manufacture entry",
		(
			"stock_entry_type",
			"posting_date",
			"posting_time",
			"from_warehouse",
			"to_warehouse",
			"value_difference",
			"remarks",
		),
		("items",),
	),
	BusinessFormatSpec(
		"material-request-requisition",
		"DocType",
		"Material Request",
		"Purchase, transfer, issue, manufacture, and customer-provided requisition",
		("material_request_type", "transaction_date", "schedule_date", "set_warehouse"),
		("items",),
	),
	BusinessFormatSpec(
		"journal-entry-voucher",
		"DocType",
		"Journal Entry",
		"Journal, cash receipt, cash payment, and petty-cash voucher",
		("voucher_type", "posting_date", "total_debit", "total_credit", "user_remark"),
		("accounts",),
		variant="journal-or-cash",
	),
	BusinessFormatSpec(
		"statement-of-account",
		"Report",
		"General Ledger",
		"Customer or supplier statement of account",
		variant="party-statement",
	),
	BusinessFormatSpec(
		"accounts-receivable-aging",
		"Report",
		"Accounts Receivable",
		"Customer receivables and aging",
		variant="receivable-aging",
	),
	BusinessFormatSpec(
		"accounts-payable-aging",
		"Report",
		"Accounts Payable",
		"Supplier payables and aging",
		variant="payable-aging",
	),
	BusinessFormatSpec(
		"pos-invoice-thermal",
		"DocType",
		"POS Invoice",
		"Point-of-sale thermal receipt",
		("customer_name", "posting_date", "posting_time", "grand_total", "paid_amount"),
		("items", "payments"),
		"80mm",
		"thermal",
	),
	BusinessFormatSpec(
		"pos-invoice-a4",
		"DocType",
		"POS Invoice",
		"Point-of-sale A4 tax invoice",
		("customer_name", "posting_date", "due_date", "grand_total", "in_words"),
		("items", "taxes", "payments"),
		"a4",
		"tax-invoice",
	),
)

CORE_V1_BUSINESS_FORMAT_BY_ID = {spec.sample_id: spec for spec in CORE_V1_BUSINESS_FORMATS}


def core_v1_sample_ids() -> tuple[str, ...]:
	return tuple(spec.sample_id for spec in CORE_V1_BUSINESS_FORMATS)
