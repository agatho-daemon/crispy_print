# Copyright (c) 2026, Agathodaemon and Contributors
# See license.txt

import json
import unittest
from pathlib import Path
from unittest.mock import patch

import frappe

from crispy_print.setup import desk

APP_ROOT = Path(__file__).resolve().parents[1]


class TestNavigationCompatibility(unittest.TestCase):
	def test_workspace_exports_have_expected_visibility_defaults(self):
		classic_workspace_path = APP_ROOT / "crispy_print" / "workspace" / "crispy" / "crispy.json"
		studio_workspace_path = (
			APP_ROOT / "crispy_print" / "workspace" / "crispy_studio" / "crispy_studio.json"
		)

		classic_workspace = json.loads(classic_workspace_path.read_text())
		studio_workspace = json.loads(studio_workspace_path.read_text())

		self.assertEqual(classic_workspace["name"], "Crispy")
		self.assertEqual(classic_workspace["label"], "Crispy")
		self.assertEqual(classic_workspace["is_hidden"], 0)

		self.assertEqual(studio_workspace["name"], "Crispy Studio")
		self.assertEqual(studio_workspace["label"], "Crispy Studio")
		self.assertEqual(studio_workspace["is_hidden"], 0)

	def test_setup_desk_compatibility_sets_v15_workspace_visibility(self):
		self._assert_setup_desk_compatibility(
			frappe_major=15,
			expected={
				"Crispy": 0,
				"Crispy Studio": 1,
			},
		)

	def test_setup_desk_compatibility_sets_v16_workspace_visibility(self):
		self._assert_setup_desk_compatibility(
			frappe_major=16,
			expected={
				"Crispy": 1,
				"Crispy Studio": 0,
			},
		)

	def _assert_setup_desk_compatibility(self, frappe_major: int, expected: dict[str, int]):
		original_values = self._get_workspace_visibility(expected)
		try:
			with patch.object(desk, "get_frappe_major", return_value=frappe_major):
				desk.setup_desk_compatibility()

			for workspace, is_hidden in expected.items():
				self.assertEqual(
					frappe.db.get_value("Workspace", workspace, "is_hidden"),
					is_hidden,
					f"{workspace} visibility mismatch for Frappe v{frappe_major}",
				)
		finally:
			self._restore_workspace_visibility(original_values)

	def _get_workspace_visibility(self, workspaces: dict[str, int]) -> dict[str, int | None]:
		return {
			workspace: frappe.db.get_value("Workspace", workspace, "is_hidden") for workspace in workspaces
		}

	def _restore_workspace_visibility(self, original_values: dict[str, int | None]) -> None:
		for workspace, is_hidden in original_values.items():
			if is_hidden is not None:
				frappe.db.set_value(
					"Workspace",
					workspace,
					"is_hidden",
					is_hidden,
					update_modified=False,
				)
		frappe.clear_cache()
