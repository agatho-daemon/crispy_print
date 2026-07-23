from types import SimpleNamespace

from frappe.tests.utils import FrappeTestCase


class TestTypstDocSerialization(FrappeTestCase):
	def test_quote_typst_string_escapes_backslashes_and_control_chars(self):
		from crispy_print.api.v1.typst_doc import _quote_typst_string

		out = _quote_typst_string('C:\\Users\\Name\tLine\r\nNext\x00"')

		self.assertEqual(out, '"C:\\\\Users\\\\Name\\tLine\\r\\nNext\\u0000\\""')

	def test_python_to_typst_dict_avoids_scrubbed_key_collisions(self):
		from crispy_print.api.v1.typst_doc import _python_to_typst_dict

		out = _python_to_typst_dict({"Total": 1, "total": 2, "Foo Bar": 3, "foo_bar": 4})

		self.assertIn("total: 1", out)
		self.assertIn('"total": 2', out)
		self.assertIn("foo_bar: 3", out)
		self.assertIn('"foo_bar": 4', out)

	def test_python_to_typst_dict_quotes_typst_keywords_used_as_keys(self):
		from crispy_print.api.v1.typst_doc import _python_to_typst_dict

		out = _python_to_typst_dict(
			{
				"context": {"font_size": "9pt"},
				"if": True,
				"normal_key": "value",
			}
		)

		self.assertIn('"context": (font_size: "9pt")', out)
		self.assertIn('"if": true', out)
		self.assertIn('normal_key: "value"', out)

	def test_quote_typst_string_keeps_existing_fix_for_single_backslashes(self):
		from crispy_print.api.v1.typst_doc import _quote_typst_string

		self.assertEqual(_quote_typst_string(r"C:\tmp\file.txt"), r'"C:\\tmp\\file.txt"')


class TestTypstDocumentAssembly(FrappeTestCase):
	def test_normal_document_places_defaults_before_preamble_and_dedicated_blocks_after_it(self):
		from crispy_print.api.v1.typst_doc import _build_typst_document

		format_doc = SimpleNamespace(
			raw_typst=0,
			typst_preamble="#let header_block = [Preamble Header]",
			doc_header="#let header_block = [Format Header]",
			doc_footer="#let footer_block = [Format Footer]",
			typst_code="#text[#doc.name]",
		)

		source = _build_typst_document(
			format_doc,
			{"name": "SI-1"},
			preamble_override="#let footer_block = [Override Footer]",
			presentation_settings_block="#set page(header: header_block, footer: footer_block)",
		)

		expected_order = [
			'#let doc = (name: "SI-1")',
			"#let header_block = []",
			"#let footer_block = []",
			"#let footer_block = [Override Footer]",
			"#let header_block = [Preamble Header]",
			"#let header_block = [Format Header]",
			"#let footer_block = [Format Footer]",
			"#set page(header: header_block, footer: footer_block)",
			"#text[#doc.name]",
		]
		positions = [source.index(fragment) for fragment in expected_order]

		self.assertEqual(positions, sorted(positions))
