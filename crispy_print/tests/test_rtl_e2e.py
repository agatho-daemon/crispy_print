import unittest

from crispy_print.dev_utils.rtl_e2e import (
	_doc_format_values,
	_layout,
	_presentation,
)


class RTLE2EFixtureTestCase(unittest.TestCase):
	def test_language_layouts_never_combine_translations(self):
		expected = {
			"ar": "فاتورة تجريبية",
			"fa": "فاکتور آزمایشی",
			"en": "Test Invoice",
		}
		for language, label in expected.items():
			with self.subTest(language=language):
				layout = _layout(language)
				section = layout["sections"][0]
				self.assertEqual(section["label"], label)
				self.assertNotIn(" / ", section["label"])
				for field in section["columns"][0]["fields"]:
					self.assertNotIn(" / ", field["label"])

	def test_multipage_fixture_repeats_unique_sections(self):
		layout = _layout("ar", repeat_sections=12)
		self.assertEqual(len(layout["sections"]), 12)
		self.assertEqual(len({section["id"] for section in layout["sections"]}), 12)
		self.assertEqual(
			sum(
				field["fieldtype"] == "Table"
				for section in layout["sections"]
				for field in section["columns"][0]["fields"]
			),
			1,
		)

	def test_print_languages_and_qr_payload_are_explicit(self):
		for language in ("ar-KW", "fa-IR", "en"):
			settings = _presentation(language)
			self.assertEqual(settings["language"], language)
			self.assertTrue(settings["qr"]["enabled"])
			self.assertEqual(settings["qr"]["symbology"], "QR Code")
			self.assertEqual(settings["qr"]["anchor"], "end")

	def test_document_fixture_uses_schema_v4(self):
		class Invoice:
			company = "Test Company"

		values = _doc_format_values(Invoice(), "fa-IR")
		self.assertEqual(values["default_print_language"], "fa")
		self.assertIn('"schema_version": 4', values["layout_json"])
		self.assertIn("align(end + horizon)", values["doc_footer"])
		self.assertIn("dir: ltr", values["doc_footer"])


if __name__ == "__main__":
	unittest.main()
