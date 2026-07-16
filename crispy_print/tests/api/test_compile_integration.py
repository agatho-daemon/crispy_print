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

		self.assertIsNotNone(result)
		assert result is not None
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

		self.assertIsNotNone(result)
		assert result is not None
		self.assertTrue(result["success"])
		self.assertEqual(result["format"], "svg")
		self.assertGreaterEqual(result["page_count"], 1)
		self.assertIn("<svg", str(result["svg_pages"][0]))

	def test_compile_six_series_lilaq_chart_with_accessibility_markers(self):
		from crispy_print.api.v1 import compile_typst

		series = ",\n".join(
			f'(name: "Series {index}", kind: "line", values: ({index}, {index + 2}, {index + 1}))'
			for index in range(1, 7)
		)
		typst_source = f"""
#import "@local/crispy-charts:0.1.1": crispy-chart
#set page(width: 180mm, height: 110mm, margin: 10mm)
#crispy-chart(
  (
    kind: "line",
    labels: ("Q1", "Q2", "Q3"),
    series: ({series}),
    options: (:),
    accessibility: (summary: "Six-series marker regression specimen."),
  ),
  theme: (accessibility_mode: true),
  width: 100%,
  height: 75mm,
)
"""

		result = compile_typst(typst_source, output_format="svg")

		self.assertIsNotNone(result)
		assert result is not None
		self.assertTrue(result["success"])
		self.assertIn("<svg", str(result["svg_pages"][0]))

	def test_lilaq_grid_theme_switches_control_rendered_grid_strokes(self):
		from crispy_print.api.v1 import compile_typst

		def render(horizontal: bool, vertical: bool, minor: bool) -> str:
			typst_source = f"""
#import "@local/crispy-charts:0.1.1": crispy-chart
#set page(width: 180mm, height: 110mm, margin: 10mm)
#crispy-chart(
  (
    kind: "line",
    labels: ("Q1", "Q2", "Q3", "Q4"),
    series: ((name: "Series", kind: "line", values: (18, 24, 20, 29)),),
    options: (:),
    accessibility: (summary: "Grid-control regression specimen."),
  ),
  theme: (
    horizontal_grid: {str(horizontal).lower()},
    vertical_grid: {str(vertical).lower()},
    minor_grid: {str(minor).lower()},
    grid_color: "#ff00ff",
  ),
  width: 100%,
  height: 75mm,
)
"""
			result = compile_typst(typst_source, output_format="svg")
			self.assertIsNotNone(result)
			assert result is not None
			self.assertTrue(result["success"])
			return str(result["svg_pages"][0]).lower()

		off = render(False, False, False)
		horizontal = render(True, False, False)
		vertical = render(False, True, False)
		major = render(True, True, False)
		minor = render(True, True, True)

		self.assertNotIn("#ff00ff", off)
		self.assertIn("#ff00ff", horizontal)
		self.assertIn("#ff00ff", vertical)
		self.assertNotEqual(horizontal, vertical)
		self.assertNotIn("#ff59ff", major)
		self.assertIn("#ff59ff", minor)
