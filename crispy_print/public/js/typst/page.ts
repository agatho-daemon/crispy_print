const TYPST_PAPER_ALIASES: Record<string, string> = {
	a0: "a0",
	a1: "a1",
	a2: "a2",
	a3: "a3",
	a4: "a4",
	a5: "a5",
	a6: "a6",
	a7: "a7",
	a8: "a8",
	a9: "a9",
	a10: "a10",
	a11: "a11",
	letter: "us-letter",
	legal: "us-legal",
	tabloid: "us-tabloid",
	executive: "us-executive",
	ledger: "us-ledger",
	"foolscap-folio": "us-foolscap-folio",
	statement: "us-statement",
	oficio: "us-oficio",
	"gov-letter": "us-gov-letter",
	"government-letter": "us-gov-letter",
	"gov-legal": "us-gov-legal",
	"government-legal": "us-gov-legal",
	"business-card": "us-business-card",
	digest: "us-digest",
	trade: "us-trade",
	"us-letter": "us-letter",
	"us-legal": "us-legal",
	"us-tabloid": "us-tabloid",
	"us-executive": "us-executive",
	"us-foolscap-folio": "us-foolscap-folio",
	"us-statement": "us-statement",
	"us-ledger": "us-ledger",
	"us-oficio": "us-oficio",
	"us-gov-letter": "us-gov-letter",
	"us-gov-legal": "us-gov-legal",
	"us-business-card": "us-business-card",
	"us-digest": "us-digest",
	"us-trade": "us-trade",
};

export function resolveTypstPaper(value: string | null | undefined, fallback = "a4"): string {
	const normalized = String(value || "")
		.trim()
		.toLowerCase()
		.replace(/[_\s]+/g, "-");
	return TYPST_PAPER_ALIASES[normalized] || normalized || fallback;
}
