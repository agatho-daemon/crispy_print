# Copyright (c) 2025, Agathodaemon and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document
from frappe.query_builder import DocType


class CrispyFormat(Document):
	def validate(self):
		"""Clear other defaults when this format is set as default"""
		if self.is_default:
			old_default = self.get_current_default()
			self.clear_other_defaults()

			if old_default:
				message = f"Replaced {frappe.bold(old_default)} as default for {frappe.bold(self.doc_type)}"

				frappe.msgprint(message, indicator="blue")

	def get_current_default(self):
		"""Get the current default format name for this DocType"""
		CrispyFormat = DocType("Crispy Format")

		result = (
			frappe.qb.from_(CrispyFormat)
			.select(CrispyFormat.name)
			.where(CrispyFormat.doc_type == self.doc_type)
			.where(CrispyFormat.name != self.name)
			.where(CrispyFormat.is_default == 1)
			.run(as_dict=True)
		)

		return result[0].name if result else None

	def clear_other_defaults(self):
		"""Clear is_default on other formats for this DocType"""
		CrispyFormat = DocType("Crispy Format")

		(
			frappe.qb.update(CrispyFormat)
			.set(CrispyFormat.is_default, 0)
			.where(CrispyFormat.doc_type == self.doc_type)
			.where(CrispyFormat.name != self.name)
			.run()
		)


@frappe.whitelist()
def make_default(name: str):
	"""Set Crispy Format as default for its DocType"""
	try:
		doc = frappe.get_doc("Crispy Format", name)
		doc.check_permission("write")

		doc.is_default = 1
		doc.save()

		frappe.db.commit()  # Explicit commit for safety

		return {"success": True, "message": f"Set {doc.name} as default"}
	except frappe.PermissionError:
		frappe.throw(frappe._("You don't have permission to modify this format"))
	except Exception as e:
		frappe.log_error(f"Failed to set default format: {e}")
		return {"success": False, "error": str(e)}
