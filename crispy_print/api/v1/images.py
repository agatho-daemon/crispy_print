from pathlib import Path

import frappe
from frappe import _

IMAGE_EXTENSIONS = {
	".png",
	".jpg",
	".jpeg",
	".svg",
	".gif",
	".webp",
	".bmp",
	".tif",
	".tiff",
	".avif",
}


def _is_supported_private_image(file_url: str | None) -> bool:
	clean = str(file_url or "").strip()
	if not clean.startswith("/private/files/"):
		return False
	filename = clean.removeprefix("/private/files/")
	if not filename or filename != Path(filename).name:
		return False
	return Path(filename).suffix.lower() in IMAGE_EXTENSIONS


def _private_file_exists(filename: str) -> bool:
	path = Path(frappe.get_site_path("private", "files", filename)).resolve()
	root = Path(frappe.get_site_path("private", "files")).resolve()
	try:
		path.relative_to(root)
	except ValueError:
		return False
	return path.exists() and path.is_file()


def get_private_image_files(query: str | None = None, limit: int | None = 100) -> list[dict]:
	if not frappe.has_permission("File", "read"):
		frappe.throw(_("Not permitted to read files."), frappe.PermissionError)

	search = str(query or "").strip().lower()
	page_length = max(1, min(int(limit or 100), 500))
	rows = frappe.get_list(
		"File",
		filters={"is_private": 1},
		fields=["name", "file_name", "file_url", "modified"],
		order_by="modified desc",
		limit_page_length=page_length * 3,
	)

	images: list[dict] = []
	seen: set[str] = set()
	for row in rows:
		file_url = row.get("file_url")
		if not _is_supported_private_image(file_url):
			continue
		filename = Path(str(file_url).removeprefix("/private/files/")).name
		if not _private_file_exists(filename):
			continue
		if filename in seen:
			continue
		if (
			search
			and search not in filename.lower()
			and search not in str(row.get("file_name") or "").lower()
		):
			continue
		seen.add(filename)
		images.append(
			{
				"name": row.get("name"),
				"filename": filename,
				"file_name": row.get("file_name") or filename,
				"file_url": file_url,
				"modified": row.get("modified"),
			}
		)
		if len(images) >= page_length:
			break
	return images
