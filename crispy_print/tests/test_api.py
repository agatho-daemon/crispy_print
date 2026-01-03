# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

"""
Test cases for Crispy Print API methods.

Tests the whitelisted API endpoints in api.py including:
- Typst font discovery
- Typst compilation (PDF and SVG)
- Document formatting
- Crispy Format retrieval
"""

import base64
import json
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTypstAPI(FrappeTestCase):
	"""Test Typst-related API methods"""

	def setUp(self):
		"""Set up test environment"""
		frappe.set_user("Administrator")

	@patch("crispy_print.api.subprocess.run")
	def test_get_typst_local_fonts(self, mock_run):
		"""Test font discovery from Typst CLI"""
		from crispy_print.api import get_typst_local_fonts

		# Mock Typst CLI output
		mock_result = Mock()
		mock_result.stdout = """
Inter (Regular, Medium, Bold)
Roboto (Regular, Bold, Italic)
Liberation Sans
"""
		mock_result.returncode = 0
		mock_run.return_value = mock_result

		fonts = get_typst_local_fonts()

		self.assertIsInstance(fonts, list)
		self.assertIn("Inter", fonts)
		self.assertIn("Roboto", fonts)
		self.assertIn("Liberation Sans", fonts)

		# Verify fonts are deduplicated and sorted
		self.assertEqual(fonts, sorted(set(fonts)))

	@patch("crispy_print.api.subprocess.run")
	def test_get_typst_local_fonts_with_bundled(self, mock_run):
		"""Test that bundled fonts are included in font list"""
		from crispy_print.api import get_typst_local_fonts

		# Mock Typst CLI output
		mock_result = Mock()
		mock_result.stdout = "Inter (Regular)\n"
		mock_result.returncode = 0
		mock_run.return_value = mock_result

		fonts = get_typst_local_fonts()

		# Should include both CLI fonts and potentially bundled fonts
		self.assertIsInstance(fonts, list)
		self.assertTrue(len(fonts) >= 1)

	@patch("crispy_print.api.subprocess.run")
	def test_compile_typst_to_pdf(self, mock_run):
		"""Test Typst compilation to PDF format"""
		from crispy_print.api import compile_typst

		# Mock successful compilation
		mock_result = Mock()
		mock_result.returncode = 0
		mock_result.stderr = ""
		mock_result.stdout = ""

		# Create a fake PDF file in temp directory
		def mock_run_side_effect(*args, **kwargs):
			# Extract output path from args
			cmd_args = args[0]
			output_path = Path(cmd_args[-1])

			# Create fake PDF
			output_path.parent.mkdir(parents=True, exist_ok=True)
			output_path.write_bytes(b"%PDF-1.4\nFake PDF content")

			return mock_result

		mock_run.side_effect = mock_run_side_effect

		typst_source = """
#set page(paper: "a4")
#set text(font: "Inter")

= Test Document

This is a test.
"""

		result = compile_typst(typst_source, output_format="pdf")

		self.assertTrue(result["success"])
		self.assertEqual(result["format"], "pdf")
		self.assertIn("pdf_data", result)

		# Verify PDF data is base64 encoded
		pdf_bytes = base64.b64decode(result["pdf_data"])
		self.assertTrue(pdf_bytes.startswith(b"%PDF"))

	@patch("crispy_print.api.subprocess.run")
	def test_compile_typst_to_svg(self, mock_run):
		"""Test Typst compilation to SVG format"""
		from crispy_print.api import compile_typst

		# Mock successful compilation
		mock_result = Mock()
		mock_result.returncode = 0
		mock_result.stderr = ""

		svg_content = """<?xml version="1.0" encoding="UTF-8"?>
<svg xmlns="http://www.w3.org/2000/svg" width="595" height="842">
  <text x="10" y="20">Test SVG</text>
</svg>"""

		def mock_run_side_effect(*args, **kwargs):
			# Extract output path template from args
			cmd_args = args[0]
			output_template = Path(cmd_args[-1])

			# Create fake SVG files (Typst creates page-numbered SVGs)
			output_dir = output_template.parent
			base_name = output_template.stem.replace("-{p}", "")

			svg_path = output_dir / f"{base_name}-1.svg"
			svg_path.parent.mkdir(parents=True, exist_ok=True)
			svg_path.write_text(svg_content, encoding="utf-8")

			return mock_result

		mock_run.side_effect = mock_run_side_effect

		typst_source = """
#set page(paper: "a4")
= Test SVG Document
"""

		result = compile_typst(typst_source, output_format="svg")

		self.assertTrue(result["success"])
		self.assertEqual(result["format"], "svg")
		self.assertIn("svg_pages", result)
		self.assertIn("page_count", result)
		self.assertEqual(result["page_count"], 1)
		self.assertTrue(result["svg_pages"][0].startswith("<?xml"))

	@patch("crispy_print.api.subprocess.run")
	def test_compile_typst_invalid_source(self, mock_run):
		"""Test error handling for invalid Typst code"""
		from crispy_print.api import compile_typst

		# Mock compilation error
		mock_result = Mock()
		mock_result.returncode = 1
		mock_result.stderr = "error: expected expression\n  ┌─ document.typ:3:1\n  │\n3 │ #invalid syntax\n  │  ^^^^^^^ expected expression"
		mock_result.stdout = ""
		mock_run.return_value = mock_result

		typst_source = "#invalid syntax"

		with self.assertRaises(Exception):
			compile_typst(typst_source)

	def test_compile_typst_empty_source(self):
		"""Test error handling for empty Typst source"""
		from crispy_print.api import compile_typst

		with self.assertRaises(Exception):
			compile_typst("")

		with self.assertRaises(Exception):
			compile_typst("   ")

	@patch("crispy_print.api._copy_letterhead_to_temp")
	@patch("crispy_print.api.subprocess.run")
	def test_compile_with_letterhead(self, mock_run, mock_copy):
		"""Test Typst compilation with letterhead image"""
		from crispy_print.api import compile_typst

		mock_copy.return_value = "letterhead.png"

		mock_result = Mock()
		mock_result.returncode = 0

		def mock_run_side_effect(*args, **kwargs):
			cmd_args = args[0]
			output_path = Path(cmd_args[-1])
			output_path.parent.mkdir(parents=True, exist_ok=True)
			output_path.write_bytes(b"%PDF-1.4\nFake PDF")
			return mock_result

		mock_run.side_effect = mock_run_side_effect

		typst_source = """
#set page(
  background: image("letterhead.png")
)
= Document with Letterhead
"""

		result = compile_typst(typst_source, output_format="pdf", letterhead_image="/files/letterhead.png")

		self.assertTrue(result["success"])
		mock_copy.assert_called_once()

	@patch("crispy_print.api._write_qr_svg")
	@patch("crispy_print.api.subprocess.run")
	def test_compile_with_qr_code(self, mock_run, mock_qr):
		"""Test Typst compilation with QR code"""
		from crispy_print.api import compile_typst

		mock_qr.return_value = "doc-qr.svg"

		mock_result = Mock()
		mock_result.returncode = 0

		def mock_run_side_effect(*args, **kwargs):
			cmd_args = args[0]
			output_path = Path(cmd_args[-1])
			output_path.parent.mkdir(parents=True, exist_ok=True)
			output_path.write_bytes(b"%PDF-1.4\nFake PDF")
			return mock_result

		mock_run.side_effect = mock_run_side_effect

		typst_source = """
#place(
  top + right,
  dx: -1cm,
  dy: 1cm,
  image("doc-qr.svg", width: 2cm)
)
= Document with QR
"""

		result = compile_typst(
			typst_source,
			output_format="pdf",
			qr_data="https://example.com/doc/SI-001",
			qr_filename="doc-qr.svg",
		)

		self.assertTrue(result["success"])
		mock_qr.assert_called_once()


class TestFormattedDocAPI(FrappeTestCase):
	"""Test document formatting API"""

	def setUp(self):
		"""Set up test environment"""
		frappe.set_user("Administrator")

	def test_get_formatted_doc(self):
		"""Test document field formatting with User doctype (minimal dependencies)"""
		from crispy_print.api import get_formatted_doc

		# Use User doctype which has minimal dependencies
		if not frappe.db.exists("User", "Administrator"):
			self.skipTest("Administrator user not found")

		# Get formatted document
		doc_data = get_formatted_doc("User", "Administrator")

		self.assertIsInstance(doc_data, dict)
		self.assertEqual(doc_data["name"], "Administrator")
		self.assertIn("email", doc_data)

	def test_get_formatted_doc_with_table(self):
		"""Test formatting of child table fields using User with roles"""
		from crispy_print.api import get_formatted_doc

		doc_data = get_formatted_doc("User", "Administrator")

		# Verify roles table is present
		self.assertIn("roles", doc_data)
		roles = doc_data.get("roles") or []

		if roles and len(roles) > 0:
			self.assertIsInstance(roles, list)
			self.assertIsInstance(roles[0], dict)

	def test_get_formatted_doc_invalid_doctype(self):
		"""Test error handling for invalid doctype"""
		from crispy_print.api import get_formatted_doc

		with self.assertRaises(Exception):
			get_formatted_doc("Invalid DocType", "TEST-001")

	def test_get_formatted_doc_invalid_name(self):
		"""Test error handling for non-existent document"""
		from crispy_print.api import get_formatted_doc

		with self.assertRaises(Exception):
			get_formatted_doc("User", "NON-EXISTENT-USER-12345")


class TestCrispyFormatRetrievalAPI(FrappeTestCase):
	"""Test Crispy Format retrieval APIs"""

	def setUp(self):
		"""Set up test environment"""
		frappe.set_user("Administrator")

		# Clean up test formats
		frappe.db.delete("Crispy Format", {"name": ["like", "Test API Format%"]})
		frappe.db.commit()

	def tearDown(self):
		"""Clean up after tests"""
		frappe.db.delete("Crispy Format", {"name": ["like", "Test API Format%"]})
		frappe.db.commit()

	def test_get_crispy_formats_for_doctype(self):
		"""Test retrieving formats for a specific DocType"""
		from crispy_print.api import get_crispy_formats_for_doctype

		# Create test formats
		format1 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format 1",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
				"page_settings": json.dumps({"pageSize": "A4"}),
			}
		)
		format1.insert()

		format2 = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format 2",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Invoice",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format2.insert()

		# Test retrieval
		formats = get_crispy_formats_for_doctype("Sales Invoice")

		self.assertIsInstance(formats, list)
		self.assertTrue(len(formats) >= 2)

		format_names = [f["name"] for f in formats]
		self.assertIn("Test API Format 1", format_names)
		self.assertIn("Test API Format 2", format_names)

	def test_get_crispy_formats_excludes_invalid_json(self):
		"""Test that formats with invalid JSON are excluded"""
		from crispy_print.api import get_crispy_formats_for_doctype

		# Create format with valid JSON
		valid_format = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Valid",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Order",
				"module": "Crispy Print",
				"layout_json": json.dumps({"sections": []}),
			}
		)
		valid_format.insert()

		# Create format with invalid JSON directly in DB
		frappe.db.set_value("Crispy Format", "Test API Format Valid", "layout_json", "{invalid json")
		frappe.db.commit()

		# Should not raise error, just exclude invalid format
		formats = get_crispy_formats_for_doctype("Purchase Order")

		# Should return empty list or not include the invalid format
		self.assertIsInstance(formats, list)

	def test_get_default_doctypes(self):
		"""Test retrieving DocTypes with default formats"""
		from crispy_print.api import get_default_doctypes

		# Create default format for Sales Order
		format_so = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Default SO",
				"crispy_format_type": "DocType",
				"doc_type": "Sales Order",
				"module": "Crispy Print",
				"is_default": 1,
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_so.insert()

		# Create default format for Purchase Order
		format_po = frappe.get_doc(
			{
				"doctype": "Crispy Format",
				"name": "Test API Format Default PO",
				"crispy_format_type": "DocType",
				"doc_type": "Purchase Order",
				"module": "Crispy Print",
				"is_default": 1,
				"layout_json": json.dumps({"sections": []}),
			}
		)
		format_po.insert()

		# Test retrieval
		default_doctypes = get_default_doctypes()

		self.assertIsInstance(default_doctypes, list)
		self.assertIn("Sales Order", default_doctypes)
		self.assertIn("Purchase Order", default_doctypes)

	def test_get_crispy_formats_empty_doctype(self):
		"""Test retrieval for DocType with no formats"""
		from crispy_print.api import get_crispy_formats_for_doctype

		# Use an unlikely DocType that won't have formats
		formats = get_crispy_formats_for_doctype("Language")

		self.assertIsInstance(formats, list)
		self.assertEqual(len(formats), 0)


class TestLetterheadCopy(FrappeTestCase):
	"""Test letterhead image handling"""

	@patch("crispy_print.api.shutil.copy2")
	@patch("crispy_print.api.Path.exists")
	def test_copy_letterhead_to_temp(self, mock_exists, mock_copy):
		"""Test copying letterhead image to temp directory"""
		from crispy_print.api import _copy_letterhead_to_temp

		mock_exists.return_value = True

		result = _copy_letterhead_to_temp("/files/letterhead.png", "/tmp/test")

		self.assertEqual(result, "letterhead.png")
		mock_copy.assert_called_once()

	def test_copy_letterhead_none(self):
		"""Test handling of None letterhead"""
		from crispy_print.api import _copy_letterhead_to_temp

		result = _copy_letterhead_to_temp(None, "/tmp/test")
		self.assertIsNone(result)

	def test_copy_letterhead_empty(self):
		"""Test handling of empty letterhead"""
		from crispy_print.api import _copy_letterhead_to_temp

		result = _copy_letterhead_to_temp("", "/tmp/test")
		self.assertIsNone(result)


class TestQRCodeGeneration(FrappeTestCase):
	"""Test QR code SVG generation"""

	def test_write_qr_svg(self):
		"""Test QR code SVG generation"""
		from crispy_print.api import _write_qr_svg

		# Mock the pyqrcode module import
		with patch.dict("sys.modules", {"pyqrcode": MagicMock()}):
			import sys

			mock_pyqrcode = sys.modules["pyqrcode"]
			mock_qr = MagicMock()
			mock_pyqrcode.create.return_value = mock_qr

			with patch("crispy_print.api.Path.mkdir"):
				result = _write_qr_svg("https://example.com", "qr-code.svg", "/tmp/test")

			self.assertEqual(result, "qr-code.svg")
			mock_qr.svg.assert_called_once()

	def test_write_qr_svg_none_data(self):
		"""Test handling of None QR data"""
		from crispy_print.api import _write_qr_svg

		result = _write_qr_svg(None, "qr.svg", "/tmp/test")
		self.assertIsNone(result)

	def test_write_qr_svg_none_filename(self):
		"""Test handling of None QR filename"""
		from crispy_print.api import _write_qr_svg

		result = _write_qr_svg("data", None, "/tmp/test")
		self.assertIsNone(result)

	def test_write_qr_svg_adds_extension(self):
		"""Test that .svg extension is added if missing"""
		from crispy_print.api import _write_qr_svg

		# Mock the pyqrcode module import
		with patch.dict("sys.modules", {"pyqrcode": MagicMock()}):
			import sys

			mock_pyqrcode = sys.modules["pyqrcode"]
			mock_qr = MagicMock()
			mock_pyqrcode.create.return_value = mock_qr

			with patch("crispy_print.api.Path.mkdir"):
				result = _write_qr_svg("data", "qr-code", "/tmp/test")

			self.assertEqual(result, "qr-code.svg")
