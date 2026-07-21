from types import SimpleNamespace
from unittest import mock

from frappe.tests.utils import FrappeTestCase


class TestRawTypstDocumentAssembly(FrappeTestCase):
	def test_raw_typst_document_skips_non_author_presentation_layers(self):
		from crispy_print.api.v1.typst_doc import _build_typst_document

		format_doc = SimpleNamespace(
			raw_typst=1,
			doc_type="Sales Invoice",
			company=None,
			typst_preamble="#set text(size: 99pt)",
			doc_header="#let header_block = [Header]",
			doc_footer="#let footer_block = [Footer]",
			typst_code="#set page(margin: 0mm)\n#text[#doc.name]",
		)

		with mock.patch(
			"crispy_print.api.v1.typst_doc.get_applicable_typst_blocks",
			return_value=[],
		):
			source = _build_typst_document(
				format_doc,
				{"name": "SI-1"},
				presentation_settings_block="#set page(margin: 50mm)",
				preamble_override="#set text(size: 20pt)",
			)

		self.assertIn('#let doc = (name: "SI-1")', source)
		self.assertIn("#let crispy_image", source)
		self.assertIn("#set page(margin: 0mm)", source)
		self.assertNotIn("#set text(size: 99pt)", source)
		self.assertNotIn("#set text(size: 20pt)", source)
		self.assertNotIn("#let header_block = [Header]", source)
		self.assertNotIn("#let footer_block = [Footer]", source)
		self.assertNotIn("#set page(margin: 50mm)", source)

	def test_raw_typst_helpers_only_inline_referenced_blocks(self):
		from crispy_print.api.v1.typst_doc import _build_typst_document

		format_doc = SimpleNamespace(
			raw_typst=1,
			doc_type="Payment Entry",
			company=None,
			typst_preamble="",
			doc_header="",
			doc_footer="",
			typst_code='#text[#doc.name]\n#crispy_block("referenced-v1.0")',
		)

		with mock.patch(
			"crispy_print.api.v1.typst_doc.get_applicable_typst_blocks",
			return_value=[
				{
					"name": "document_title-v1.0",
					"typst_code": "#grid([#doc.doctype], [#doc.name])",
				},
				{
					"name": "referenced-v1.0",
					"typst_code": "#text[Referenced]",
				},
			],
		):
			source = _build_typst_document(format_doc, {"name": "PE-1"})

		self.assertIn('"referenced-v1.0": [', source)
		self.assertIn("#text[Referenced]", source)
		self.assertNotIn('"document_title-v1.0": [', source)
		self.assertNotIn("#grid([#doc.doctype], [#doc.name])", source)
