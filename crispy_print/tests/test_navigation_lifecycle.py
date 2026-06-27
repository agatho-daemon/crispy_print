# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import json
import re
import unittest
from pathlib import Path
from unittest.mock import call, patch

import frappe

from crispy_print import install

APP_ROOT = Path(__file__).resolve().parents[1]


def scrub(value: str) -> str:
	return re.sub(r"[^\w]+", "_", value.lower()).strip("_")


class TestNavigationLifecycle(unittest.TestCase):
	def setUp(self):
		frappe.set_user("Administrator")
		self.test_desktop_icons = [
			"Test Crispy App Icon",
			"Test Crispy Link Icon",
		]
		self.test_sidebars = [
			"Test Crispy Auto Sidebar",
			"Test Crispy Standard Sidebar",
			"Test Crispy Link Icon",
		]
		self._cleanup_test_records()

	def tearDown(self):
		self._cleanup_test_records()

	def _cleanup_test_records(self):
		for name in self.test_desktop_icons:
			if frappe.db.exists("Desktop Icon", name):
				frappe.delete_doc(
					"Desktop Icon",
					name,
					force=True,
					ignore_permissions=True,
					ignore_on_trash=True,
				)
		for name in self.test_sidebars:
			if frappe.db.exists("Workspace Sidebar", name):
				frappe.delete_doc(
					"Workspace Sidebar",
					name,
					force=True,
					ignore_permissions=True,
					ignore_on_trash=True,
				)

	def _insert_workspace_sidebar(self, name: str, *, app: str | None, standard: int):
		doc = frappe.get_doc(
			{
				"doctype": "Workspace Sidebar",
				"name": name,
				"title": name,
				"module": "Crispy Print",
				"app": app,
				"standard": standard,
				"header_icon": "crispy-print-logo",
			}
		)
		self._insert_without_developer_export(doc)
		return doc

	def _insert_desktop_icon(self, name: str, *, icon_type: str):
		data = {
			"doctype": "Desktop Icon",
			"name": name,
			"label": name,
			"icon_type": icon_type,
			"app": "crispy_print",
			"standard": 1,
		}
		if icon_type == "App":
			data.update(
				{
					"hidden": 1,
					"link_type": "External",
					"link": "/desk/crispy-print",
					"logo_url": "/assets/crispy_print/icons/crispy-print-logo.svg",
				}
			)
		else:
			data.update(
				{
					"hidden": 0,
					"icon": "crispy_print",
					"link_type": "Workspace Sidebar",
					"link_to": name,
				}
			)
		doc = frappe.get_doc(data)
		self._insert_without_developer_export(doc)
		return doc

	def _insert_without_developer_export(self, doc):
		original_developer_mode = frappe.conf.get("developer_mode")
		try:
			frappe.conf.developer_mode = 0
			doc.insert(ignore_permissions=True)
		finally:
			frappe.conf.developer_mode = original_developer_mode

	def test_navigation_json_contracts_match_erpnext_style_names(self):
		app_icon_path = APP_ROOT / "desktop_icon" / "crispy_print.json"
		studio_icon_path = APP_ROOT / "desktop_icon" / "crispy_studio.json"
		studio_sidebar_path = APP_ROOT / "workspace_sidebar" / "crispy_studio.json"
		workspace_path = APP_ROOT / "crispy_print" / "workspace" / "crispy_print" / "crispy_print.json"
		old_sidebar_path = APP_ROOT / "workspace_sidebar" / "crispy_print.json"
		studio_icon_asset_paths = [
			APP_ROOT / "public" / "icons" / "desktop_icons" / variant / "crispy_studio.svg"
			for variant in ("solid", "subtle")
		]

		app_icon = json.loads(app_icon_path.read_text())
		studio_icon = json.loads(studio_icon_path.read_text())
		studio_sidebar = json.loads(studio_sidebar_path.read_text())
		workspace = json.loads(workspace_path.read_text())

		self.assertFalse(old_sidebar_path.exists())
		for asset_path in studio_icon_asset_paths:
			self.assertTrue(asset_path.exists(), f"Missing desktop icon asset: {asset_path}")
		self.assertEqual(app_icon_path.name, f"{scrub(app_icon['label'])}.json")
		self.assertEqual(studio_icon_path.name, f"{scrub(studio_icon['label'])}.json")
		self.assertEqual(studio_sidebar_path.name, f"{scrub(studio_sidebar['title'])}.json")
		self.assertEqual(workspace_path.name, f"{scrub(workspace['label'])}.json")

		self.assertEqual(app_icon["name"], "Crispy Print")
		self.assertEqual(app_icon["icon_type"], "App")
		self.assertEqual(app_icon["link_type"], "External")
		self.assertEqual(app_icon["link"], "/desk/crispy-print")
		self.assertEqual(app_icon["logo_url"], "/assets/crispy_print/icons/crispy-print-logo.svg")

		self.assertEqual(studio_icon["name"], "Crispy Studio")
		self.assertEqual(studio_icon["icon_type"], "Link")
		self.assertEqual(studio_icon["link_type"], "Workspace Sidebar")
		self.assertEqual(studio_icon["link_to"], "Crispy Studio")
		self.assertEqual(studio_icon["parent_icon"], "Crispy Print")

		self.assertEqual(studio_sidebar["name"], "Crispy Studio")
		self.assertEqual(studio_sidebar["title"], "Crispy Studio")
		self.assertEqual(studio_sidebar["app"], "crispy_print")
		self.assertEqual(studio_sidebar["standard"], 1)
		self.assertEqual(studio_sidebar["header_icon"], "crispy-print-logo")

		home_item = studio_sidebar["items"][0]
		self.assertEqual(home_item["label"], "Home")
		self.assertEqual(home_item["link_type"], "URL")
		self.assertEqual(home_item["url"], "/desk/crispy-print?sidebar=Crispy%20Studio")

		self.assertEqual(
			[item["label"] for item in studio_sidebar["items"][:11]],
			[
				"Home",
				"Formats",
				"Branding Profiles",
				"Crispy Formats",
				"Templates",
				"Typst Blocks",
				"Builders",
				"Branding Builder",
				"Format Builder",
				"Typst Block Builder",
				"Print Preview",
			],
		)
		self.assertNotIn("Branding", [item["label"] for item in studio_sidebar["items"]])
		issued_documents_section = next(
			item
			for item in studio_sidebar["items"]
			if item["type"] == "Section Break" and item["label"] == "Issued Documents"
		)
		self.assertEqual(issued_documents_section["keep_closed"], 1)

		workspace_content = json.loads(workspace["content"])
		self.assertEqual(
			[block["data"]["shortcut_name"] for block in workspace_content[:4]],
			["Crispy Formats", "Format Builder", "Branding Profiles", "Branding Builder"],
		)

	def test_after_sync_removes_local_auto_generated_crispy_print_sidebar(self):
		self._insert_workspace_sidebar("Test Crispy Auto Sidebar", app=None, standard=0)

		with (
			patch.object(install, "AUTO_WORKSPACE_SIDEBAR_NAME", "Test Crispy Auto Sidebar"),
			patch.object(install, "APP_DESKTOP_ICON_NAME", "Test Crispy App Icon"),
		):
			install.cleanup_auto_generated_navigation_records()

		self.assertFalse(frappe.db.exists("Workspace Sidebar", "Test Crispy Auto Sidebar"))

	def test_after_sync_preserves_standard_crispy_studio_sidebar(self):
		self._insert_workspace_sidebar("Test Crispy Standard Sidebar", app="crispy_print", standard=1)

		with (
			patch.object(install, "AUTO_WORKSPACE_SIDEBAR_NAME", "Test Crispy Standard Sidebar"),
			patch.object(install, "APP_DESKTOP_ICON_NAME", "Test Crispy App Icon"),
		):
			install.cleanup_auto_generated_navigation_records()

		self.assertTrue(frappe.db.exists("Workspace Sidebar", "Test Crispy Standard Sidebar"))

	def test_after_sync_removes_non_app_desktop_icon_named_crispy_print(self):
		self._insert_workspace_sidebar("Test Crispy Link Icon", app=None, standard=0)
		self._insert_desktop_icon("Test Crispy Link Icon", icon_type="Link")

		with (
			patch.object(install, "APP_DESKTOP_ICON_NAME", "Test Crispy Link Icon"),
			patch.object(install, "AUTO_WORKSPACE_SIDEBAR_NAME", "Test Crispy Auto Sidebar"),
		):
			install.cleanup_auto_generated_navigation_records()

		self.assertFalse(frappe.db.exists("Desktop Icon", "Test Crispy Link Icon"))

	def test_after_sync_preserves_app_desktop_icon_named_crispy_print(self):
		self._insert_desktop_icon("Test Crispy App Icon", icon_type="App")

		with (
			patch.object(install, "APP_DESKTOP_ICON_NAME", "Test Crispy App Icon"),
			patch.object(install, "AUTO_WORKSPACE_SIDEBAR_NAME", "Test Crispy Auto Sidebar"),
		):
			install.cleanup_auto_generated_navigation_records()

		self.assertTrue(frappe.db.exists("Desktop Icon", "Test Crispy App Icon"))

	def test_before_uninstall_deletes_navigation_records_without_on_trash(self):
		with (
			patch.object(install.frappe.db, "exists", return_value=True),
			patch.object(install.frappe, "delete_doc") as delete_doc,
		):
			install.cleanup_crispy_print_navigation_records()

		self.assertEqual(delete_doc.call_count, 4)
		delete_doc.assert_has_calls(
			[
				call(
					"Desktop Icon",
					"Crispy Print",
					force=True,
					ignore_permissions=True,
					ignore_on_trash=True,
					ignore_missing=True,
				),
				call(
					"Desktop Icon",
					"Crispy Studio",
					force=True,
					ignore_permissions=True,
					ignore_on_trash=True,
					ignore_missing=True,
				),
				call(
					"Workspace Sidebar",
					"Crispy Studio",
					force=True,
					ignore_permissions=True,
					ignore_on_trash=True,
					ignore_missing=True,
				),
				call(
					"Workspace Sidebar",
					"Crispy Print",
					force=True,
					ignore_permissions=True,
					ignore_on_trash=True,
					ignore_missing=True,
				),
			]
		)
