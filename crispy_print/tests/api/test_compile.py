# Copyright (c) 2025, Agathodaemon and Contributors
# See license.txt

import base64
import os
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import ANY, MagicMock, Mock, patch

import frappe
from frappe.tests.utils import FrappeTestCase


class TestTypstAPI(FrappeTestCase):
	"""Test Typst-related API methods"""

	def setUp(self):
		"""Set up test environment"""
		frappe.set_user("Administrator")
		frappe.cache().delete_value("crispy_print:typst_local_fonts:v3")
		from crispy_print.install import ensure_site_font_directory

		ensure_site_font_directory()

	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_get_typst_local_fonts(self, mock_run):
		"""Test font discovery from Typst CLI"""
		from crispy_print.api.v1 import get_typst_local_fonts
		from crispy_print.api.v1.compile import TYPST_FONT_DIR, _site_font_dir

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
		cmd_args = mock_run.call_args.args[0]
		self.assertIn("--font-path", cmd_args)
		font_path = cmd_args[cmd_args.index("--font-path") + 1]
		self.assertIn(str(TYPST_FONT_DIR), font_path.split(os.pathsep))
		self.assertIn(str(_site_font_dir()), font_path.split(os.pathsep))

	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_get_typst_local_fonts_with_bundled(self, mock_run):
		"""Test that bundled fonts are included in font list"""
		from crispy_print.api.v1 import get_typst_local_fonts

		# Mock Typst CLI output
		mock_result = Mock()
		mock_result.stdout = "Inter (Regular)\n"
		mock_result.returncode = 0
		mock_run.return_value = mock_result

		fonts = get_typst_local_fonts()

		# Should include both CLI fonts and potentially bundled fonts
		self.assertIsInstance(fonts, list)
		self.assertTrue(len(fonts) >= 1)

	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_typst_to_pdf(self, mock_run):
		"""Test Typst compilation to PDF format"""
		from crispy_print.api.v1 import compile_typst

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

		cmd_args = mock_run.call_args.args[0]
		self.assertIn("--pdf-standard", cmd_args)
		self.assertEqual(cmd_args[cmd_args.index("--pdf-standard") + 1], "a-2u")

	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_typst_pdf_standard_mapping(self, mock_run):
		"""Test PDF standard options are mapped to Typst CLI flags."""
		from crispy_print.api.v1 import compile_typst

		mock_result = Mock()
		mock_result.returncode = 0
		mock_result.stderr = ""
		mock_result.stdout = ""

		def mock_run_side_effect(*args, **kwargs):
			cmd_args = args[0]
			output_path = Path(cmd_args[-1])
			output_path.parent.mkdir(parents=True, exist_ok=True)
			output_path.write_bytes(b"%PDF-1.7\nFake PDF")
			return mock_result

		mock_run.side_effect = mock_run_side_effect

		compile_typst("= PDF/A-3u", output_format="pdf", pdf_standard="PDF/A-3u")
		cmd_args = mock_run.call_args.args[0]
		self.assertIn("--pdf-standard", cmd_args)
		self.assertEqual(cmd_args[cmd_args.index("--pdf-standard") + 1], "a-3u")

		compile_typst("= PDF/A-4", output_format="pdf", pdf_standard="PDF/A-4")
		cmd_args = mock_run.call_args.args[0]
		self.assertIn("--pdf-standard", cmd_args)
		self.assertEqual(cmd_args[cmd_args.index("--pdf-standard") + 1], "a-4")

		compile_typst("= Plain PDF", output_format="pdf", pdf_standard="PDF 1.7")
		cmd_args = mock_run.call_args.args[0]
		self.assertIn("--pdf-standard", cmd_args)
		self.assertEqual(cmd_args[cmd_args.index("--pdf-standard") + 1], "1.7")

		compile_typst("= PDF 2.0", output_format="pdf", pdf_standard="PDF 2.0")
		cmd_args = mock_run.call_args.args[0]
		self.assertIn("--pdf-standard", cmd_args)
		self.assertEqual(cmd_args[cmd_args.index("--pdf-standard") + 1], "2.0")

		compile_typst("= PDF/A + UA", output_format="pdf", pdf_standard="a-2u,ua-1")
		cmd_args = mock_run.call_args.args[0]
		self.assertIn("--pdf-standard", cmd_args)
		self.assertEqual(cmd_args[cmd_args.index("--pdf-standard") + 1], "a-2u,ua-1")

	def test_compile_typst_rejects_invalid_pdf_standard(self):
		from crispy_print.api.v1 import compile_typst

		with self.assertRaises(Exception):
			compile_typst("= Test", output_format="pdf", pdf_standard="PDF/X")

		with self.assertRaises(Exception):
			compile_typst("= Test", output_format="pdf", pdf_standard="PDF")

	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_typst_to_svg(self, mock_run):
		"""Test Typst compilation to SVG format"""
		from crispy_print.api.v1 import compile_typst

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

	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_typst_invalid_source(self, mock_run):
		"""Test error handling for invalid Typst code"""
		from crispy_print.api.v1 import compile_typst

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
		from crispy_print.api.v1 import compile_typst

		with self.assertRaises(Exception):
			compile_typst("")

		with self.assertRaises(Exception):
			compile_typst("   ")

	@patch("crispy_print.api.v1.compile._copy_asset_files_to_temp")
	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_with_letterhead(self, mock_run, mock_copy):
		"""Test Typst compilation with letterhead image"""
		from crispy_print.api.v1 import compile_typst

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

		result = compile_typst(
			typst_source,
			output_format="pdf",
			asset_files=["/files/letterhead.png"],
		)

		self.assertTrue(result["success"])
		mock_copy.assert_called_once()

	def test_compile_typst_rejects_deprecated_params(self):
		from crispy_print.api.v1 import compile_typst

		with self.assertRaises(Exception):
			compile_typst("= Test", letterhead_image="/files/legacy.png")

		with self.assertRaises(Exception):
			compile_typst("= Test", logo_image="/files/legacy.png")

	def test_compile_typst_rejects_invalid_asset_files_shape(self):
		from crispy_print.api.v1 import compile_typst

		with self.assertRaises(Exception):
			compile_typst("= Test", asset_files="not-a-list")

		with self.assertRaises(Exception):
			compile_typst("= Test", asset_files=["http://example.com/a.png"])

		with self.assertRaises(Exception):
			compile_typst("= Test", asset_files=["logo.svg"])

	@patch("crispy_print.api.v1.compile._copy_asset_files_to_temp")
	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_typst_accepts_rpc_json_asset_files(self, mock_run, mock_copy):
		from crispy_print.api.v1 import compile_typst

		mock_result = MagicMock(returncode=0, stderr="", stdout="")

		def mock_run_side_effect(*args, **kwargs):
			cmd_args = args[0]
			output_template = Path(cmd_args[-1])
			output_dir = output_template.parent
			base_name = output_template.stem.replace("-{p}", "")
			svg_path = output_dir / f"{base_name}-1.svg"
			svg_path.parent.mkdir(parents=True, exist_ok=True)
			svg_path.write_text("<svg></svg>", encoding="utf-8")
			return mock_result

		mock_run.side_effect = mock_run_side_effect

		with patch("crispy_print.api.v1.compile.Path.exists") as mock_exists:
			mock_exists.return_value = True
			result = compile_typst(
				'#image("ManagerLogo.svg")',
				output_format="svg",
				asset_files='["/private/files/ManagerLogo.svg"]',
			)

		self.assertTrue(result["success"])
		mock_copy.assert_called_once()

	@patch("crispy_print.api.v1.compile._write_qr_svg")
	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_with_qr_code(self, mock_run, mock_qr):
		"""Test Typst compilation with QR code"""
		from crispy_print.api.v1 import compile_typst

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
		self.assertEqual(mock_qr.call_args.args[3], {})

	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_typst_uses_package_path_when_vendor_packages_exist(self, mock_run):
		from crispy_print.api.v1 import compile_typst
		from crispy_print.api.v1.compile import TYPST_FONT_DIR, TYPST_PACKAGE_DIR, _site_font_dir

		mock_result = Mock()
		mock_result.returncode = 0
		mock_result.stderr = ""

		def mock_run_side_effect(*args, **kwargs):
			cmd_args = args[0]
			output_template = Path(cmd_args[-1])
			output_dir = output_template.parent
			base_name = output_template.stem.replace("-{p}", "")
			(output_dir / f"{base_name}-1.svg").write_text("<svg/>", encoding="utf-8")
			return mock_result

		mock_run.side_effect = mock_run_side_effect

		result = compile_typst("= Test", output_format="svg")

		self.assertTrue(result["success"])
		cmd_args = mock_run.call_args.args[0]
		self.assertIn("--font-path", cmd_args)
		font_path = cmd_args[cmd_args.index("--font-path") + 1]
		self.assertIn(str(TYPST_FONT_DIR), font_path.split(os.pathsep))
		self.assertIn(str(_site_font_dir()), font_path.split(os.pathsep))
		self.assertIn("--package-path", cmd_args)
		self.assertEqual(cmd_args[cmd_args.index("--package-path") + 1], str(TYPST_PACKAGE_DIR))

	def test_compile_cache_key_includes_barcode_options(self):
		from crispy_print.api.v1.compile import _compile_cache_key

		common = {
			"typst_source": "= Test",
			"output_format": "svg",
			"pdf_standard": "",
			"asset_files": [],
			"chart_svg": None,
			"qr_data": "payload",
			"qr_filename": "qr.svg",
			"typst_bin": "typst",
		}

		first = _compile_cache_key(**common, barcode_options={"symbology": "QR Code", "quiet_zone": 1})
		second = _compile_cache_key(**common, barcode_options={"symbology": "QR Code", "quiet_zone": 4})

		self.assertNotEqual(first, second)


class TestAssetCopy(FrappeTestCase):
	"""Test image asset handling"""

	def test_copy_asset_file_to_temp(self):
		"""Test copying image file to temp directory"""
		from crispy_print.api.v1.compile import _copy_file_to_temp

		with TemporaryDirectory() as tmpdir:
			site = Path(tmpdir) / "site"
			letterhead_path = site / "public" / "files" / "letterhead.png"
			letterhead_path.parent.mkdir(parents=True, exist_ok=True)
			letterhead_path.write_text("fake", encoding="utf-8")
			out_dir = Path(tmpdir) / "out"
			with patch("crispy_print.api.v1.compile.frappe.get_site_path", return_value=str(site)):
				result = _copy_file_to_temp("/files/letterhead.png", str(out_dir), "Asset file")

			self.assertEqual(result, "letterhead.png")
			self.assertTrue((out_dir / "letterhead.png").exists())
			self.assertEqual((out_dir / "letterhead.png").read_text(encoding="utf-8"), "fake")

	def test_copy_asset_none(self):
		"""Test handling of None asset"""
		from crispy_print.api.v1.compile import _copy_file_to_temp

		result = _copy_file_to_temp(None, "/tmp/test", "Asset file")
		self.assertIsNone(result)

	def test_copy_asset_empty(self):
		"""Test handling of empty asset"""
		from crispy_print.api.v1.compile import _copy_file_to_temp

		result = _copy_file_to_temp("", "/tmp/test", "Asset file")
		self.assertIsNone(result)

	def test_copy_file_rejects_bare_filename_lookup(self):
		from crispy_print.api.v1.compile import _copy_file_to_temp

		with TemporaryDirectory() as tmpdir:
			site = Path(tmpdir) / "site"
			(site / "private" / "files").mkdir(parents=True, exist_ok=True)
			with patch("crispy_print.api.v1.compile.frappe.get_site_path", return_value=str(site)):
				with self.assertRaises(Exception):
					_copy_file_to_temp("logo.svg", str(Path(tmpdir) / "out"), "Asset file")

	def test_copy_file_raises_when_missing_filename(self):
		from crispy_print.api.v1.compile import _copy_file_to_temp

		with TemporaryDirectory() as tmpdir:
			site = Path(tmpdir) / "site"
			(site / "private" / "files").mkdir(parents=True, exist_ok=True)
			(site / "public" / "files").mkdir(parents=True, exist_ok=True)
			with patch("crispy_print.api.v1.compile.frappe.get_site_path", return_value=str(site)):
				with self.assertRaises(Exception):
					_copy_file_to_temp("/files/missing.png", str(Path(tmpdir) / "out"), "Asset file")

	def test_copy_file_does_not_fallback_when_explicit_path_missing(self):
		from crispy_print.api.v1.compile import _copy_file_to_temp

		with TemporaryDirectory() as tmpdir:
			site = Path(tmpdir) / "site"
			private_file = site / "private" / "files" / "brand" / "ManagerLogo.svg"
			private_file.parent.mkdir(parents=True, exist_ok=True)
			private_file.write_text("private", encoding="utf-8")
			with patch("crispy_print.api.v1.compile.frappe.get_site_path", return_value=str(site)):
				with self.assertRaises(Exception):
					_copy_file_to_temp(
						"/private/files/missing/ManagerLogo.svg",
						str(Path(tmpdir) / "out"),
						"Letterhead image",
					)

	def test_copy_file_supports_private_files_path(self):
		from crispy_print.api.v1.compile import _copy_file_to_temp, _resolve_source_path

		with TemporaryDirectory() as tmpdir:
			site = Path(tmpdir) / "site"
			logo_path = site / "private" / "files" / "logo.svg"
			logo_path.parent.mkdir(parents=True, exist_ok=True)
			logo_path.write_text("private", encoding="utf-8")
			out_dir = Path(tmpdir) / "out"
			with patch("crispy_print.api.v1.compile.frappe.get_site_path", return_value=str(site)):
				resolved = _resolve_source_path("/private/files/logo.svg", "Asset file")
				result = _copy_file_to_temp("/private/files/logo.svg", str(out_dir), "Asset file")

			self.assertEqual(resolved, logo_path.resolve())
			self.assertEqual(result, "logo.svg")
			self.assertEqual((out_dir / "logo.svg").read_text(encoding="utf-8"), "private")

	def test_copy_file_rejects_path_traversal(self):
		from crispy_print.api.v1.compile import _copy_file_to_temp

		with TemporaryDirectory() as tmpdir:
			site = Path(tmpdir) / "site"
			(site / "private" / "files").mkdir(parents=True, exist_ok=True)
			with patch("crispy_print.api.v1.compile.frappe.get_site_path", return_value=str(site)):
				with self.assertRaises(Exception):
					_copy_file_to_temp("../outside/logo.png", str(Path(tmpdir) / "out"), "Asset file")

	def test_copy_file_rejects_symlink_sources(self):
		from crispy_print.api.v1.compile import _copy_file_to_temp

		with TemporaryDirectory() as tmpdir:
			site = Path(tmpdir) / "site"
			target_file = site / "public" / "files" / "actual.svg"
			target_file.parent.mkdir(parents=True, exist_ok=True)
			target_file.write_text("<svg/>", encoding="utf-8")
			symlink_path = site / "public" / "files" / "linked.svg"
			os.symlink(target_file, symlink_path)
			with patch("crispy_print.api.v1.compile.frappe.get_site_path", return_value=str(site)):
				with self.assertRaises(Exception):
					_copy_file_to_temp("/files/linked.svg", str(Path(tmpdir) / "out"), "Asset file")

	@patch("crispy_print.api.v1.compile._copy_asset_files_to_temp")
	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_with_asset_files(self, mock_run, mock_copy_assets):
		from crispy_print.api.v1 import compile_typst

		mock_result = Mock()
		mock_result.returncode = 0

		def mock_run_side_effect(*args, **kwargs):
			cmd_args = args[0]
			output_template = Path(cmd_args[-1])
			output_dir = output_template.parent
			base_name = output_template.stem.replace("-{p}", "")
			svg_path = output_dir / f"{base_name}-1.svg"
			svg_path.parent.mkdir(parents=True, exist_ok=True)
			svg_path.write_text("<svg/>", encoding="utf-8")
			return mock_result

		mock_run.side_effect = mock_run_side_effect

		result = compile_typst(
			"= Test",
			output_format="svg",
			asset_files=["/files/logo.svg", "/files/image.png"],
		)

		self.assertTrue(result["success"])
		mock_copy_assets.assert_called_once()

	def test_compile_rejects_traversal_in_typst_image_literal_paths(self):
		from crispy_print.api.v1 import compile_typst

		typst_source = '#image("../../../../../private/var/folders/tmp/wsqg_address.svg", width: 50%)'
		with self.assertRaises(Exception):
			compile_typst(typst_source, output_format="svg")

	def test_compile_rejects_oversized_source(self):
		from crispy_print.api.v1 import compile_typst
		from crispy_print.api.v1.compile import MAX_TYPST_SOURCE_BYTES

		with self.assertRaises(Exception):
			compile_typst("=" + ("x" * MAX_TYPST_SOURCE_BYTES), output_format="svg")

	@patch("crispy_print.api.v1.compile._copy_file_to_temp")
	@patch("crispy_print.api.v1.compile.subprocess.run")
	def test_compile_retries_after_typst_missing_file_error(self, mock_run, mock_copy_file):
		from crispy_print.api.v1 import compile_typst

		first = Mock()
		first.returncode = 1
		first.stderr = (
			"error: file not found " "(searched at /private/var/folders/.../tmpabcd/wsqg_address.svg)"
		)
		first.stdout = ""

		second = Mock()
		second.returncode = 0
		second.stderr = ""
		second.stdout = ""

		def mock_run_side_effect(*args, **kwargs):
			cmd_args = args[0]
			output_template = Path(cmd_args[-1])
			if mock_run.call_count >= 2:
				output_dir = output_template.parent
				base_name = output_template.stem.replace("-{p}", "")
				svg_path = output_dir / f"{base_name}-1.svg"
				svg_path.parent.mkdir(parents=True, exist_ok=True)
				svg_path.write_text("<svg/>", encoding="utf-8")
			return first if mock_run.call_count == 1 else second

		mock_run.side_effect = mock_run_side_effect
		mock_copy_file.return_value = "wsqg_address.svg"

		result = compile_typst("= Test", output_format="svg", asset_files=["/files/wsqg_address.svg"])

		self.assertTrue(result["success"])
		self.assertEqual(mock_run.call_count, 2)
		mock_copy_file.assert_called_with("/files/wsqg_address.svg", ANY, "Asset file")


class TestQRCodeGeneration(FrappeTestCase):
	"""Test QR code SVG generation"""

	def test_write_qr_svg(self):
		"""Test QR code SVG generation"""
		from crispy_print.api.v1.compile import _write_qr_svg

		# Mock the segno module import
		with patch.dict("sys.modules", {"segno": MagicMock()}):
			import sys

			sys.modules["segno"].make = MagicMock()
			qr_obj = MagicMock()
			sys.modules["segno"].make.return_value = qr_obj
			qr_obj.save = MagicMock()

			result = _write_qr_svg("total: د.ك 32,000.000", "test.svg", "/tmp")

			self.assertEqual(result, "test.svg")
			sys.modules["segno"].make.assert_called_once_with("total: د.ك 32,000.000", error="m")
			qr_obj.save.assert_called_once()

	def test_write_qr_svg_rejects_datamatrix_fallback(self):
		from crispy_print.api.v1.compile import _write_qr_svg

		with self.assertRaises(frappe.ValidationError):
			_write_qr_svg(
				"payload",
				"dm.svg",
				"/tmp",
				{"symbology": "DataMatrix"},
			)
