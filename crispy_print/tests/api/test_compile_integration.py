# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

import base64
import os
import shutil
import unittest

from frappe.tests.utils import FrappeTestCase

RUN_TYPST_INTEGRATION = os.environ.get("CRISPY_PRINT_RUN_TYPST_INTEGRATION") == "1"
HAS_TYPST_CLI = shutil.which("typst") is not None


@unittest.skipUnless(
	RUN_TYPST_INTEGRATION and HAS_TYPST_CLI,
	"Typst integration tests require CRISPY_PRINT_RUN_TYPST_INTEGRATION=1 and typst CLI",
)
class TestTypstCLIIntegration(FrappeTestCase):
	"""Optional integration tests using the real Typst CLI binary."""

	def test_compile_typst_to_pdf_with_real_cli(self):
		from crispy_print.api.v1 import compile_typst

		typst_source = """
#set page(paper: "a4")
= Integration PDF

This is a Typst CLI integration test.
"""

		result = compile_typst(typst_source, output_format="pdf")

		self.assertTrue(result["success"])
		self.assertEqual(result["format"], "pdf")
		pdf_bytes = base64.b64decode(result["pdf_data"])
		self.assertTrue(pdf_bytes.startswith(b"%PDF"))

	def test_compile_typst_to_svg_with_real_cli(self):
		from crispy_print.api.v1 import compile_typst

		typst_source = """
#set page(paper: "a4")
= Integration SVG

This is a Typst CLI integration test.
"""

		result = compile_typst(typst_source, output_format="svg")

		self.assertTrue(result["success"])
		self.assertEqual(result["format"], "svg")
		self.assertGreaterEqual(result["page_count"], 1)
		self.assertIn("<svg", result["svg_pages"][0])
