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
