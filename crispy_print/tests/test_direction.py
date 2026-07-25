from unittest import TestCase

from crispy_print.direction import get_language_direction, is_ltr_field, normalize_language


class TestDirection(TestCase):
	def test_language_normalization_and_direction(self):
		self.assertEqual(normalize_language("fa_IR"), "fa-IR")
		self.assertEqual(
			get_language_direction("ar-KW"),
			{
				"language": "ar-KW",
				"language_code": "ar",
				"region": "KW",
				"direction": "rtl",
			},
		)
		self.assertEqual(get_language_direction("en-US")["direction"], "ltr")
		self.assertEqual(get_language_direction("he")["direction"], "rtl")
		self.assertEqual(get_language_direction("ur-PK")["direction"], "rtl")

	def test_field_direction_classification_preserves_prose_names(self):
		self.assertTrue(is_ltr_field("Currency", "grand_total"))
		self.assertTrue(is_ltr_field("Data", "tax_id"))
		self.assertTrue(is_ltr_field("Data", "item_code"))
		self.assertTrue(is_ltr_field("Data", "name"))
		self.assertFalse(is_ltr_field("Data", "customer_name"))
		self.assertFalse(is_ltr_field("Text", "description"))
