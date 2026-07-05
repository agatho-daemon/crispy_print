# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import frappe
from frappe.tests.utils import FrappeTestCase

from crispy_print.crispy_print.doctype.crispy_print_settings.crispy_print_settings import (
	apply_settings_defaults,
	get_bundled_font_directory,
	get_font_search_paths_display,
	get_render_timeout_seconds,
	get_typst_font_dirs,
	get_uploaded_font_directory,
	validate_document_print_policy,
)


class TestCrispyPrintSettings(FrappeTestCase):
	def test_defaults_and_timeout_are_applied(self):
		settings = frappe._dict({})

		apply_settings_defaults(settings)

		self.assertEqual(settings.enable_uploaded_fonts, 1)
		self.assertEqual(settings.enable_system_fonts, 0)
		self.assertEqual(settings.render_timeout_seconds, 60)
		self.assertEqual(get_render_timeout_seconds(settings), 60)

	def test_font_paths_respect_uploaded_toggle(self):
		settings = frappe._dict({"enable_uploaded_fonts": 0, "enable_system_fonts": 0})

		dirs = get_typst_font_dirs(settings, existing_only=False)
		display = get_font_search_paths_display(settings)

		self.assertIn(get_bundled_font_directory(), dirs)
		self.assertIn("Bundled fonts:\ncrispy_print/public/vendor/fonts", display)
		self.assertIn("Uploaded fonts:\nDisabled", display)
		self.assertNotIn(str(get_bundled_font_directory()), display)

	def test_uploaded_font_directory_is_absolute_for_typst_cli(self):
		settings = frappe._dict({"enable_uploaded_fonts": 1, "enable_system_fonts": 0})

		dirs = get_typst_font_dirs(settings, existing_only=False)

		self.assertTrue(get_uploaded_font_directory().is_absolute())
		self.assertIn(get_uploaded_font_directory(), dirs)
		for font_dir in dirs:
			self.assertTrue(font_dir.is_absolute())

	def test_draft_and_cancelled_policy(self):
		settings = frappe.get_single("Crispy Print Settings")
		original = {
			"allow_print_for_draft": settings.allow_print_for_draft,
			"always_add_draft_heading": settings.always_add_draft_heading,
			"allow_print_for_cancelled": settings.allow_print_for_cancelled,
		}
		try:
			settings.db_set("allow_print_for_draft", 1, update_modified=False)
			settings.db_set("always_add_draft_heading", 1, update_modified=False)
			settings.db_set("allow_print_for_cancelled", 0, update_modified=False)

			result = validate_document_print_policy(frappe._dict({"docstatus": 0}))
			self.assertTrue(result["show_draft_heading"])

			with self.assertRaises(frappe.ValidationError):
				validate_document_print_policy(frappe._dict({"docstatus": 2}))
		finally:
			for fieldname, value in original.items():
				settings.db_set(fieldname, value, update_modified=False)
