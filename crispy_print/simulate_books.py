#!/usr/bin/env python3
"""
Production-grade Kuwait business simulation engine.
Based on ChatGPT's lean, audit-safe approach.

Usage:
    bench --site fdev.local execute crispy_print.simulate_books.simulate --kwargs "{'years': 3}"
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import Any, Optional

import frappe
from frappe.utils import getdate


@dataclass(frozen=True)
class SimConfig:
	years: int = 3
	sales_invoices_per_month: int = 18
	purchase_invoices_per_month: int = 10
	customer_payment_probability: float = 0.90
	supplier_payment_probability: float = 0.90
	min_lines: int = 1
	max_lines: int = 4
	min_qty: float = 1.0
	max_qty: float = 8.0
	min_rate: float = 5.0
	max_rate: float = 250.0
	commit_every: int = 50
	seed: int = 20260113
	# HRMS settings
	employees: int = 20
	attendance_probability: float = 0.95  # 95% attendance
	leave_probability: float = 0.02  # 2% on leave
	min_salary: float = 300.0  # KWD
	max_salary: float = 2000.0  # KWD


def simulate(years: int = 3) -> None:
	"""
	Generate a multi-year accounting simulation using existing Customers/Suppliers.

	Run:
	  bench --site fdev.local execute crispy_print.simulate_books.simulate --kwargs "{'years': 3}"
	"""
	frappe.set_user("Administrator")

	cfg = SimConfig(years=int(years))
	random.seed(cfg.seed)

	company = _get_default_company()
	if not company:
		raise RuntimeError("No Company found. Create a Company first.")

	frappe.logger().info("simulate_books: starting for company=%s, years=%s", company, years)

	# Pre-setup: ensure warehouse and items exist
	warehouse = _ensure_warehouse(company)
	items = _ensure_items(company, warehouse)

	# HRMS: ensure employees exist
	employees = _ensure_employees(company, cfg.employees)

	customers = _pluck_names("Customer")
	suppliers = _pluck_names("Supplier")

	if not customers:
		raise RuntimeError("No Customers found. Create at least a few Customers first.")
	if not suppliers:
		raise RuntimeError("No Suppliers found. Create at least a few Suppliers first.")

	# We simulate from the start of the month, N years back, up to the end of last month.
	start = _first_day_of_month(_add_months(_today(), -12 * cfg.years))
	end = _last_day_of_month(_add_months(_today(), -1))

	frappe.logger().info(
		"simulate_books: company=%s start=%s end=%s customers=%s suppliers=%s items=%s warehouse=%s",
		company,
		start,
		end,
		len(customers),
		len(suppliers),
		len(items),
		warehouse,
	)

	print("\n" + "=" * 80)
	print("🏢 KUWAIT BUSINESS SIMULATION (Production Grade)")
	print("=" * 80)
	print("\n📊 Simulation Parameters:")
	print(f"   • Company: {company}")
	print(f"   • Time period: {years} years ({start} to {end})")
	print(f"   • Customers: {len(customers)}")
	print(f"   • Suppliers: {len(suppliers)}")
	print(f"   • Items: {len(items)}")
	print(f"   • Warehouse: {warehouse}")
	print(f"   • Employees: {len(employees)}")
	print(f"   • Sales invoices/month: {cfg.sales_invoices_per_month}")
	print(f"   • Purchase invoices/month: {cfg.purchase_invoices_per_month}")
	print("\n" + "=" * 80)

	payment_helper_customer = _get_customer_payment_helper()
	payment_helper_supplier = _get_supplier_payment_helper()

	created = 0
	current = start
	month_num = 0
	total_months = (end.year - start.year) * 12 + (end.month - start.month) + 1

	while current <= end:
		month_num += 1
		print(f"\n📅 Month {month_num}/{total_months}: {current.strftime('%B %Y')}")

		# Month shape: sales > purchases, and scattered days.
		month_created = _generate_month(
			cfg=cfg,
			company=company,
			month=current,
			customers=customers,
			suppliers=suppliers,
			items=items,
			warehouse=warehouse,
			employees=employees,
			make_customer_payment=payment_helper_customer,
			make_supplier_payment=payment_helper_supplier,
		)

		created += month_created
		print(f"   ✓ Created {month_created} documents this month (total: {created})")

		if created and (created % cfg.commit_every == 0):
			frappe.db.commit()
			frappe.logger().info("simulate_books: committed after %s docs", created)
			print(f"   💾 Database committed at {created} documents")

		current = _add_months(current, 1)

	frappe.db.commit()
	frappe.logger().info("simulate_books: done, created approx %s docs", created)

	print("\n" + "=" * 80)
	print("✅ SIMULATION COMPLETE!")
	print("=" * 80)
	_print_financial_summary(company, start, end)
	print("\n" + "=" * 80 + "\n")


def _ensure_warehouse(company: str) -> str:
	"""Ensure at least one warehouse exists for the company"""
	warehouse = frappe.get_value("Warehouse", {"company": company, "is_group": 0}, "name")

	if warehouse:
		frappe.logger().info("simulate_books: using existing warehouse=%s", warehouse)
		return str(warehouse)

	# Create a warehouse
	frappe.logger().info("simulate_books: creating warehouse for company=%s", company)
	print(f"\n📦 Creating warehouse for {company}...")

	wh_doc = frappe.get_doc(
		{"doctype": "Warehouse", "warehouse_name": "Main Store", "company": company, "is_group": 0}
	)
	wh_doc.insert(ignore_permissions=True)
	frappe.db.commit()

	print(f"   ✓ Created warehouse: {wh_doc.name}")
	return str(wh_doc.name)


def _ensure_items(company: str, warehouse: str) -> list[str]:
	"""Ensure sufficient items exist, create if needed"""
	existing_items = frappe.get_all(
		"Item",
		filters={"disabled": 0},
		fields=["name", "is_stock_item"],
		limit_page_length=5000,
	)

	if len(existing_items) >= 20:
		frappe.logger().info("simulate_books: using %s existing items", len(existing_items))
		return [str(r["name"]) for r in existing_items]

	# Create items
	target_count = 30
	to_create = target_count - len(existing_items)

	frappe.logger().info("simulate_books: creating %s items", to_create)
	print(f"\n📦 Creating {to_create} items...")

	item_groups = ["Products", "Services", "Raw Material", "Consumable"]
	created_items = [str(r["name"]) for r in existing_items]

	for i in range(to_create):
		try:
			# Create mostly non-stock items to avoid stock balance issues
			is_stock = i % 5 == 0  # 20% stock items, 80% services/non-stock

			item_doc = frappe.get_doc(
				{
					"doctype": "Item",
					"item_code": f"SIM-ITEM-{i + 1:04d}",
					"item_name": f"Simulation Item {i + 1:03d}",
					"item_group": random.choice(item_groups),
					"is_stock_item": 1 if is_stock else 0,
					"include_item_in_manufacturing": 0,
					"standard_rate": random.randint(50, 1000),
					"maintain_stock": 0 if not is_stock else 1,
				}
			)

			if is_stock:
				item_doc.append("item_defaults", {"default_warehouse": warehouse, "company": company})

			item_doc.insert(ignore_permissions=True)
			created_items.append(item_doc.name)

			if (i + 1) % 10 == 0:
				print(f"   ✓ Created {i + 1}/{to_create} items")
				frappe.db.commit()

		except Exception as e:
			frappe.log_error(title="simulate_books: item creation failed", message=str(e))

	frappe.db.commit()
	print(f"   ✓ Total items available: {len(created_items)}")

	return created_items


def _ensure_employees(company: str, target_count: int) -> list[str]:
	"""Ensure sufficient employees exist, create if needed"""
	existing_employees = frappe.get_all(
		"Employee",
		filters={"status": "Active", "company": company},
		fields=["name"],
		limit_page_length=5000,
	)

	created_employees = [str(r["name"]) for r in existing_employees]
	to_create = max(target_count - len(existing_employees), 0)

	if to_create:
		frappe.logger().info("simulate_books: creating %s employees", to_create)
		print(f"\n👥 Creating {to_create} employees...")

		# departments = ["Sales", "Operations", "Finance", "HR", "IT", "Warehouse"]
		# designations = ["Manager", "Executive", "Officer", "Assistant", "Supervisor"]

		for i in range(to_create):
			try:
				emp_doc = frappe.get_doc(
					{
						"doctype": "Employee",
						"first_name": "Employee",
						"last_name": f"{len(created_employees) + i + 1:03d}",
						"gender": random.choice(["Male", "Female"]),
						"date_of_birth": f"{random.randint(1980, 2000)}-{random.randint(1, 12):02d}-{random.randint(1, 28):02d}",
						"date_of_joining": _add_months(_today(), -random.randint(6, 60)).isoformat(),
						"company": company,
						"status": "Active",
					}
				)

				# Set department and designation if they exist
				dept = frappe.db.exists("Department", {"company": company})
				if dept:
					emp_doc.department = dept

				desig = frappe.db.exists("Designation", {})
				if desig:
					emp_doc.designation = desig

				emp_doc.insert(ignore_permissions=True)
				created_employees.append(emp_doc.name)

				if (i + 1) % 5 == 0:
					print(f"   ✓ Created {i + 1}/{to_create} employees")
					frappe.db.commit()

			except Exception as e:
				frappe.log_error(title="simulate_books: employee creation failed", message=str(e))

		frappe.db.commit()
		print(f"   ✓ Total employees available: {len(created_employees)}")
	else:
		frappe.logger().info("simulate_books: using %s existing employees", len(created_employees))

	# Ensure salary components exist and assignments are created for all employees
	_ensure_salary_components()
	print("\n💼 Ensuring salary assignments for all employees...")
	assigned_count = 0
	for emp_name in created_employees:
		existing_assignment = frappe.db.exists(
			"Salary Structure Assignment", {"employee": emp_name, "docstatus": 1}
		)
		if not existing_assignment:
			try:
				_create_salary_assignment(emp_name, company)
				assigned_count += 1
			except Exception as e:
				frappe.log_error(title="simulate_books: salary assignment failed", message=str(e))

	if assigned_count > 0:
		frappe.db.commit()
		print(f"   ✓ Created {assigned_count} new salary assignments")

	return created_employees


def _ensure_salary_components() -> None:
	"""Ensure basic salary components exist"""
	components = [
		{"name": "Basic Salary", "type": "Earning"},
		{"name": "Housing Allowance", "type": "Earning"},
		{"name": "Transport Allowance", "type": "Earning"},
	]

	for comp in components:
		if not frappe.db.exists("Salary Component", comp["name"]):
			try:
				sc = frappe.get_doc(
					{"doctype": "Salary Component", "salary_component": comp["name"], "type": comp["type"]}
				)
				sc.insert(ignore_permissions=True)
			except Exception:
				pass  # May already exist


def _create_salary_assignment(employee: str, company: str) -> None:
	"""Create salary structure assignment for employee"""
	try:
		# Use a dedicated simulation salary structure to avoid altering existing payroll
		ss_name = "WSQG Monthly Payroll (Sim)"

		# If it doesn't exist, create one with formula-based components
		if not frappe.db.exists("Salary Structure", ss_name):
			ss = frappe.get_doc(
				{
					"doctype": "Salary Structure",
					"name": ss_name,
					"company": company,
					"payroll_frequency": "Monthly",
					"earnings": [
						{"salary_component": "Basic Salary", "amount": 600},
						{"salary_component": "Housing Allowance", "amount": 250},
						{"salary_component": "Transport Allowance", "amount": 150},
					],
				}
			)
			ss.insert(ignore_permissions=True)
			ss.submit()

		# Get base salary from Employee document (or use random if not set)
		employee_doc = frappe.get_doc("Employee", employee)
		base_salary = employee_doc.get("ctc") or round(random.uniform(300, 2000), 2)
		if base_salary <= 0:
			base_salary = round(random.uniform(300, 2000), 2)
		join_date = getdate(employee_doc.get("date_of_joining") or _today())
		min_from_date = _add_months(_today(), -120)
		from_date = join_date if join_date > min_from_date else min_from_date

		ssa = frappe.get_doc(
			{
				"doctype": "Salary Structure Assignment",
				"employee": employee,
				"salary_structure": ss_name,
				"from_date": from_date,
				"company": company,
				"base": base_salary,
			}
		)
		ssa.insert(ignore_permissions=True)
		ssa.submit()
	except Exception as e:
		frappe.log_error(title="simulate_books: salary assignment failed", message=str(e))


def _create_opening_stock(item_code: str, warehouse: str, company: str) -> None:
	"""Create opening stock to prevent negative stock issues"""
	try:
		stock_entry = frappe.get_doc(
			{
				"doctype": "Stock Entry",
				"stock_entry_type": "Material Receipt",
				"company": company,
				"to_warehouse": warehouse,
				"items": [
					{
						"item_code": item_code,
						"qty": random.randint(100, 500),
						"basic_rate": random.randint(10, 200),
						"t_warehouse": warehouse,
					}
				],
			}
		)
		stock_entry.insert(ignore_permissions=True)
		stock_entry.submit()
	except Exception as e:
		frappe.log_error(title="simulate_books: opening stock failed", message=str(e))


def _generate_month(
	cfg: SimConfig,
	company: str,
	month: date,
	customers: list[str],
	suppliers: list[str],
	items: list[str],
	warehouse: str,
	employees: list[str],
	make_customer_payment: Callable[[str, str, date], str | None] | None,
	make_supplier_payment: Callable[[str, str, date], str | None] | None,
) -> int:
	created = 0
	month_start = _first_day_of_month(month)
	month_end = _last_day_of_month(month)

	# Sales invoices
	for _ in range(cfg.sales_invoices_per_month):
		posting_date = _random_day(month_start, month_end)
		customer = random.choice(customers)
		sinv_name = _create_sales_invoice(
			cfg=cfg,
			company=company,
			customer=customer,
			posting_date=posting_date,
			items=items,
			warehouse=warehouse,
		)
		if sinv_name:
			created += 1

			if make_customer_payment and random.random() < cfg.customer_payment_probability:
				pay_date = _clamp_date(
					posting_date + timedelta(days=random.randint(0, 20)), month_start, month_end
				)
				pe = make_customer_payment(sinv_name, company, pay_date)
				if pe:
					created += 1

	# Purchase invoices
	for _ in range(cfg.purchase_invoices_per_month):
		posting_date = _random_day(month_start, month_end)
		supplier = random.choice(suppliers)
		pinv_name = _create_purchase_invoice(
			cfg=cfg,
			company=company,
			supplier=supplier,
			posting_date=posting_date,
			items=items,
			warehouse=warehouse,
		)
		if pinv_name:
			created += 1

			if make_supplier_payment and random.random() < cfg.supplier_payment_probability:
				pay_date = _clamp_date(
					posting_date + timedelta(days=random.randint(0, 25)), month_start, month_end
				)
				pe = make_supplier_payment(pinv_name, company, pay_date)
				if pe:
					created += 1

	# HRMS: Attendance and Payroll
	if employees:
		hrms_created = _process_monthly_payroll(cfg, company, employees, month_start, month_end)
		created += hrms_created

	return created


def _create_sales_invoice(
	cfg: SimConfig,
	company: str,
	customer: str,
	posting_date: date,
	items: list[str],
	warehouse: str,
) -> str | None:
	lines = _random_lines(cfg, items, warehouse, company)

	doc = frappe.get_doc(
		{
			"doctype": "Sales Invoice",
			"company": company,
			"customer": customer,
			"posting_date": posting_date.isoformat(),
			"set_posting_time": 1,
			"items": lines,
			# Do NOT force taxes here; rely on Kuwait VAT defaults
		}
	)

	try:
		doc.insert(ignore_permissions=True)
		doc.submit()
		return str(doc.name)
	except Exception:
		frappe.log_error(title="simulate_books: Sales Invoice failed", message=frappe.get_traceback())
		return None


def _create_purchase_invoice(
	cfg: SimConfig,
	company: str,
	supplier: str,
	posting_date: date,
	items: list[str],
	warehouse: str,
) -> str | None:
	lines = _random_lines(cfg, items, warehouse, company)

	doc = frappe.get_doc(
		{
			"doctype": "Purchase Invoice",
			"company": company,
			"supplier": supplier,
			"posting_date": posting_date.isoformat(),
			"set_posting_time": 1,
			"items": lines,
		}
	)

	try:
		doc.insert(ignore_permissions=True)
		doc.submit()
		return str(doc.name)
	except Exception:
		frappe.log_error(title="simulate_books: Purchase Invoice failed", message=frappe.get_traceback())
		return None


def _random_lines(cfg: SimConfig, items: list[str], warehouse: str, company: str) -> list[dict[str, Any]]:
	n = random.randint(cfg.min_lines, cfg.max_lines)
	out: list[dict[str, Any]] = []

	for _ in range(n):
		item_code = random.choice(items)

		# Get item UOM and check if it requires whole numbers
		item_uom, is_stock = frappe.get_value("Item", item_code, ["stock_uom", "is_stock_item"])
		uom_must_be_whole = frappe.get_value("UOM", item_uom, "must_be_whole_number") or 0

		# Generate quantity - use whole numbers if UOM requires it
		if uom_must_be_whole:
			qty = random.randint(int(cfg.min_qty), int(cfg.max_qty))
		else:
			qty = round(random.uniform(cfg.min_qty, cfg.max_qty), 2)

		rate = round(random.uniform(cfg.min_rate, cfg.max_rate), 3)

		line = {
			"item_code": item_code,
			"qty": qty,
			"rate": rate,
		}

		# Only add warehouse for stock items
		if is_stock:
			line["warehouse"] = warehouse

		out.append(line)

	return out


# -----------------------------
# HRMS (Payroll & Attendance)
# -----------------------------


def _process_monthly_payroll(
	cfg: SimConfig,
	company: str,
	employees: list[str],
	month_start: date,
	month_end: date,
) -> int:
	"""Process attendance and payroll for the month"""
	created = 0

	# Mark attendance for all employees (working days only)
	for emp in employees:
		try:
			# Typical working days in a month (skip Fridays/Saturdays for Kuwait)
			current_day = month_start
			while current_day <= month_end:
				# Skip weekends (Friday=4, Saturday=5 in weekday())
				if current_day.weekday() not in [4, 5]:
					# Determine attendance status
					rand = random.random()
					if rand < cfg.attendance_probability:
						status = "Present"
					elif rand < (cfg.attendance_probability + cfg.leave_probability):
						status = "On Leave"
					else:
						status = "Absent"

					# Check if attendance already exists
					if not frappe.db.exists("Attendance", {"employee": emp, "attendance_date": current_day}):
						try:
							att = frappe.get_doc(
								{
									"doctype": "Attendance",
									"employee": emp,
									"attendance_date": current_day.isoformat(),
									"status": status,
									"company": company,
								}
							)
							att.insert(ignore_permissions=True)
							att.submit()
						except Exception:
							pass  # Attendance may already exist

				current_day = current_day + timedelta(days=1)
		except Exception as e:
			frappe.log_error(title="simulate_books: attendance failed", message=str(e))

	# Create salary slips for all employees
	try:
		for emp in employees:
			try:
				# Check if salary slip already exists
				existing = frappe.db.exists(
					"Salary Slip", {"employee": emp, "start_date": month_start, "end_date": month_end}
				)

				if existing:
					continue

				# Ensure a salary structure assignment exists
				existing_assignment = frappe.db.exists(
					"Salary Structure Assignment", {"employee": emp, "docstatus": 1}
				)
				if not existing_assignment:
					_create_salary_assignment(emp, company)

				# Get salary structure assignment
				ssa = frappe.get_value(
					"Salary Structure Assignment",
					{"employee": emp, "docstatus": 1},
					["salary_structure", "base"],
					as_dict=True,
					order_by="from_date desc",
				)

				if not ssa:
					continue

				ss = _create_salary_slip(
					employee=emp,
					company=company,
					salary_structure=ssa.salary_structure,
					base_amount=float(ssa.base or 1000),
					start_date=month_start,
					end_date=month_end,
				)
				if ss:
					created += 1
			except Exception as e:
				frappe.log_error(title="simulate_books: salary slip failed", message=str(e))
	except Exception as e:
		frappe.log_error(title="simulate_books: payroll processing failed", message=str(e))

	return created


# -----------------------------
# Salary Slip Helper
# -----------------------------


def _create_salary_slip(
	employee: str,
	company: str,
	salary_structure: str,
	base_amount: float,
	start_date: date,
	end_date: date,
) -> str | None:
	try:
		from hrms.payroll.doctype.salary_slip.salary_slip import make_salary_slip

		ss = make_salary_slip(salary_structure, employee, for_preview=0, ignore_permissions=True)
		ss.start_date = start_date
		ss.end_date = end_date
		ss.posting_date = end_date
		# Ensure a non-zero net pay for simulation data
		if not ss.earnings or (ss.net_pay or 0) <= 0:
			ss.salary_structure = None
			ss.set("earnings", [])
			ss.append("earnings", {"salary_component": "Basic Salary", "amount": base_amount})
			ss.calculate_net_pay(skip_tax_breakup_computation=True)
		ss.save(ignore_permissions=True)
		prev_flag = getattr(frappe.flags, "via_payroll_entry", False)
		frappe.flags.via_payroll_entry = True
		try:
			ss.submit()
		finally:
			frappe.flags.via_payroll_entry = prev_flag
		return str(ss.name)
	except ImportError:
		employee_doc = frappe.get_doc("Employee", employee)
		currency = (
			frappe.db.get_value("Company", company, "default_currency")
			or employee_doc.get("salary_currency")
			or "USD"
		)
		total_days = (end_date - start_date).days + 1
		ss = frappe.get_doc(
			{
				"doctype": "Salary Slip",
				"employee": employee,
				"employee_name": employee_doc.employee_name,
				"company": company,
				"currency": currency,
				"salary_structure": salary_structure,
				"posting_date": end_date,
				"start_date": start_date,
				"end_date": end_date,
				"total_working_days": total_days,
				"payment_days": total_days,
				"exchange_rate": 1,
				"earnings": [{"salary_component": "Basic Salary", "amount": base_amount}],
			}
		)
		ss.calculate_net_pay(skip_tax_breakup_computation=True)
		ss.insert(ignore_permissions=True)
		prev_flag = getattr(frappe.flags, "via_payroll_entry", False)
		frappe.flags.via_payroll_entry = True
		try:
			ss.submit()
		finally:
			frappe.flags.via_payroll_entry = prev_flag
		return str(ss.name)
	except Exception:
		raise


# -----------------------------
# Payments (best effort)
# -----------------------------


def _get_customer_payment_helper() -> Callable[[str, str, date], str | None] | None:
	"""
	Returns a function that creates & submits a Payment Entry allocating the Sales Invoice,
	or None if we cannot find the helper in this ERPNext version.
	"""
	try:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		def _pay(sinv_name: str, company: str, posting_date: date) -> str | None:
			try:
				pe = get_payment_entry("Sales Invoice", sinv_name)
				pe.posting_date = posting_date.isoformat()
				pe.reference_date = posting_date.isoformat()
				_ensure_payment_reference(pe, posting_date)
				pe.insert(ignore_permissions=True)
				pe.submit()
				return str(pe.name)
			except Exception:
				frappe.log_error(
					title="simulate_books: customer payment failed", message=frappe.get_traceback()
				)
				return None

		return _pay
	except Exception:
		return None


def _get_supplier_payment_helper() -> Callable[[str, str, date], str | None] | None:
	"""
	Returns a function that creates & submits a Payment Entry allocating the Purchase Invoice,
	or None if we cannot find the helper in this ERPNext version.
	"""
	try:
		from erpnext.accounts.doctype.payment_entry.payment_entry import get_payment_entry

		def _pay(pinv_name: str, company: str, posting_date: date) -> str | None:
			try:
				pe = get_payment_entry("Purchase Invoice", pinv_name)
				pe.posting_date = posting_date.isoformat()
				pe.reference_date = posting_date.isoformat()
				_ensure_payment_reference(pe, posting_date)
				pe.insert(ignore_permissions=True)
				pe.submit()
				return str(pe.name)
			except Exception:
				frappe.log_error(
					title="simulate_books: supplier payment failed", message=frappe.get_traceback()
				)
				return None

		return _pay
	except Exception:
		return None


# -----------------------------
# Lookup helpers
# -----------------------------


def _get_default_company() -> str | None:
	# Prefer Global Defaults, else first Company.
	default_company = frappe.db.get_single_value("Global Defaults", "default_company")
	if default_company:
		return str(default_company)
	return frappe.get_value("Company", {}, "name")


def _pluck_names(doctype: str) -> list[str]:
	rows = frappe.get_all(doctype, fields=["name"], limit_page_length=20000)
	return [str(r["name"]) for r in rows]


def _ensure_payment_reference(pe: frappe.model.document.Document, posting_date: date) -> None:
	account = pe.paid_to or pe.paid_from
	account_type = None
	if account:
		account_type = frappe.db.get_value("Account", account, "account_type")

	if account_type == "Bank":
		if not pe.reference_no:
			pe.reference_no = f"SIM-PAY-{frappe.generate_hash(length=8)}"
		if not pe.reference_date:
			pe.reference_date = posting_date.isoformat()

	if not pe.mode_of_payment:
		pe.mode_of_payment = frappe.db.get_value("Mode of Payment", {}, "name")


# -----------------------------
# Date helpers (pure python)
# -----------------------------


def _today() -> date:
	return datetime.now().date()


def _first_day_of_month(d: date) -> date:
	return date(d.year, d.month, 1)


def _last_day_of_month(d: date) -> date:
	next_month = _add_months(date(d.year, d.month, 1), 1)
	return next_month - timedelta(days=1)


def _add_months(d: date, months: int) -> date:
	# Pure stdlib month add.
	y = d.year + (d.month - 1 + months) // 12
	m = (d.month - 1 + months) % 12 + 1
	day = min(d.day, _days_in_month(y, m))
	return date(y, m, day)


def _days_in_month(year: int, month: int) -> int:
	if month == 12:
		next_month = date(year + 1, 1, 1)
	else:
		next_month = date(year, month + 1, 1)
	return (next_month - timedelta(days=1)).day


def _random_day(start: date, end: date) -> date:
	delta = (end - start).days
	return start + timedelta(days=random.randint(0, max(delta, 0)))


def _clamp_date(d: date, lo: date, hi: date) -> date:
	if d < lo:
		return lo
	if d > hi:
		return hi
	return d


def _print_financial_summary(company: str, from_date: date, to_date: date) -> None:
	"""Print financial summary of generated data"""
	try:
		from frappe.utils import flt

		print("\n📊 Financial Summary:")

		# Sales
		sales = frappe.db.sql(
			"""
			SELECT COUNT(*) as count, SUM(grand_total) as total
			FROM `tabSales Invoice`
			WHERE company = %s AND docstatus = 1
			AND posting_date BETWEEN %s AND %s
		""",
			(company, from_date, to_date),
			as_dict=1,
		)[0]
		print(f"   • Sales Invoices: {sales.count} documents ({flt(sales.total, 2)} KWD)")

		# Purchases
		purchases = frappe.db.sql(
			"""
			SELECT COUNT(*) as count, SUM(grand_total) as total
			FROM `tabPurchase Invoice`
			WHERE company = %s AND docstatus = 1
			AND posting_date BETWEEN %s AND %s
		""",
			(company, from_date, to_date),
			as_dict=1,
		)[0]
		print(f"   • Purchase Invoices: {purchases.count} documents ({flt(purchases.total, 2)} KWD)")

		# Payments
		payments = frappe.db.sql(
			"""
			SELECT COUNT(*) as count, SUM(paid_amount) as total
			FROM `tabPayment Entry`
			WHERE company = %s AND docstatus = 1
			AND posting_date BETWEEN %s AND %s
		""",
			(company, from_date, to_date),
			as_dict=1,
		)[0]
		print(f"   • Payment Entries: {payments.count} documents ({flt(payments.total, 2)} KWD)")

		# GL Entries
		gl_count = frappe.db.count(
			"GL Entry", {"company": company, "posting_date": ["between", [from_date, to_date]]}
		)
		print(f"   • GL Entries: {gl_count} ledger lines")

		# HRMS Data
		salary_slips = frappe.db.count(
			"Salary Slip",
			{"company": company, "docstatus": 1, "start_date": ["between", [from_date, to_date]]},
		)
		if salary_slips:
			salary_total = frappe.db.sql(
				"""
				SELECT SUM(net_pay) as total
				FROM `tabSalary Slip`
				WHERE company = %s AND docstatus = 1
				AND start_date BETWEEN %s AND %s
			""",
				(company, from_date, to_date),
				as_dict=1,
			)[0]
			print(f"   • Salary Slips: {salary_slips} documents ({flt(salary_total.total or 0, 2)} KWD)")

		attendance_count = frappe.db.count(
			"Attendance", {"company": company, "attendance_date": ["between", [from_date, to_date]]}
		)
		if attendance_count:
			print(f"   • Attendance Records: {attendance_count} days")

		# Net position
		net = flt(sales.total or 0) - flt(purchases.total or 0)
		print(f"   • Net Revenue: {flt(net, 2)} KWD")

	except Exception as e:
		print(f"   ⚠ Could not generate summary: {e!s}")


# Convenience functions


def quick_sim():
	"""1 year simulation - Quick test
	Usage: bench --site fdev.local execute crispy_print.simulate_books.quick_sim
	"""
	simulate(years=1)


def full_sim():
	"""3 year simulation - Full Kuwait books
	Usage: bench --site fdev.local execute crispy_print.simulate_books.full_sim
	"""
	simulate(years=3)
