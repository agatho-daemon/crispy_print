from pathlib import Path

import frappe
from frappe.tests.utils import FrappeTestCase


class TestPrivateImageFilesAPI(FrappeTestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.created_files: list[str] = []
		self.created_paths: list[Path] = []

	def tearDown(self):
		for name in self.created_files:
			if frappe.db.exists("File", name):
				frappe.delete_doc("File", name, force=True)
		for path in self.created_paths:
			if path.exists():
				path.unlink()

	def make_file(
		self, filename: str, file_url: str, is_private: int = 1, preserve_file_url: bool = False
	) -> str:
		if file_url.startswith("/private/files/"):
			relative = file_url.removeprefix("/private/files/")
			path = Path(frappe.get_site_path("private", "files", *relative.split("/")))
		elif file_url.startswith("/files/"):
			relative = file_url.removeprefix("/files/")
			path = Path(frappe.get_site_path("public", "files", *relative.split("/")))
		else:
			path = Path(frappe.get_site_path("private", "files", Path(file_url).name))
		path.parent.mkdir(parents=True, exist_ok=True)
		path.write_text("x", encoding="utf-8")
		self.created_paths.append(path)
		doc = frappe.get_doc(
			{
				"doctype": "File",
				"file_name": filename,
				"file_url": file_url,
				"is_private": is_private,
			}
		).insert(ignore_permissions=True)
		if preserve_file_url and doc.file_url != file_url:
			doc.db_set("file_url", file_url, update_modified=False)
			doc.file_url = file_url
		self.created_files.append(doc.name)
		return Path(str(doc.file_url)).name

	def test_get_private_image_files_filters_to_private_top_level_images(self):
		from crispy_print.api.v1 import get_private_image_files

		private_logo = self.make_file(
			"crispy-image-test-logo.svg", "/private/files/crispy-image-test-logo.svg"
		)
		public_logo = self.make_file("crispy-image-test-public.svg", "/files/crispy-image-test-public.svg", 0)
		nested_logo = self.make_file(
			"crispy-image-test-nested.svg",
			"/private/files/nested/crispy-image-test-nested.svg",
			preserve_file_url=True,
		)
		text_file = self.make_file("crispy-image-test.txt", "/private/files/crispy-image-test.txt")

		rows = get_private_image_files(query="crispy-image-test", limit=20)
		filenames = {row["filename"] for row in rows}

		self.assertIn(private_logo, filenames)
		self.assertNotIn(public_logo, filenames)
		self.assertNotIn(nested_logo, filenames)
		self.assertNotIn(text_file, filenames)
