from frappe.tests.utils import FrappeTestCase

from crispy_print.api.v1.compile import sanitize_chart_svg
from crispy_print.api.v1.reports import _is_basic_report_format, _prepare_basic_chart_source
from crispy_print.report_charts import (
	MAX_NATIVE_CHART_POINTS,
	apply_chart_representation,
	normalize_chart_theme,
	normalize_report_chart,
	resolve_chart_render,
)


class TestReportChartNormalization(FrappeTestCase):
	def test_applies_safe_chart_representation_overrides(self):
		spec = normalize_report_chart(
			{
				"type": "axis-mixed",
				"data": {
					"labels": ["Jan", "Feb"],
					"datasets": [
						{"name": "Actual", "chartType": "bar", "values": [10, 12]},
						{"name": "Rate", "chartType": "line", "values": [2, 3]},
					],
				},
			}
		)

		as_bars = apply_chart_representation(spec, "bar")
		self.assertEqual(as_bars["kind"], "grouped_bar")
		self.assertEqual([item["kind"] for item in as_bars["series"]], ["bar", "bar"])
		self.assertTrue(as_bars["representation"]["applied"])

		as_lines = apply_chart_representation(spec, "line")
		self.assertEqual(as_lines["kind"], "line")
		self.assertEqual([item["kind"] for item in as_lines["series"]], ["line", "line"])
		self.assertEqual(spec["kind"], "mixed")

	def test_rejects_incompatible_chart_representation_overrides(self):
		grouped = normalize_report_chart(
			{
				"type": "bar",
				"data": {
					"labels": ["Jan"],
					"datasets": [
						{"name": "Actual", "values": [10]},
						{"name": "Budget", "values": [12]},
					],
				},
			}
		)
		rejected = apply_chart_representation(grouped, "horizontal_bar")
		self.assertEqual(rejected["kind"], "grouped_bar")
		self.assertFalse(rejected["representation"]["applied"])
		self.assertEqual(rejected["diagnostic"]["code"], "incompatible_chart_representation")

		aging = normalize_report_chart(
			{
				"type": "percentage",
				"data": {
					"labels": ["Current"],
					"datasets": [{"name": "Customer", "values": [100]}],
				},
			}
		)
		protected = apply_chart_representation(aging, "line")
		self.assertEqual(protected["kind"], "percentage_stacked")
		self.assertFalse(protected["representation"]["applied"])

	def test_normalizes_grouped_bar_and_preserves_zero_and_missing_values(self):
		spec = normalize_report_chart(
			{
				"type": "bar",
				"data": {
					"labels": ["Jan", "Feb", "Mar"],
					"datasets": [
						{"name": "Actual", "values": [0, None, 12]},
						{"name": "Budget", "values": [10, 11, 12]},
					],
				},
			},
			"Budget Variance",
		)
		self.assertEqual(spec["status"], "ready")
		self.assertEqual(spec["kind"], "grouped_bar")
		self.assertEqual(spec["series"][0]["values"], [0, None, 12])
		self.assertIn("Budget Variance chart", spec["accessibility"]["summary"])

	def test_normalizes_axis_mixed_series_kinds(self):
		spec = normalize_report_chart(
			{
				"type": "axis-mixed",
				"data": {
					"labels": ["A", "B"],
					"datasets": [
						{"name": "Revenue", "chartType": "bar", "values": [10, 12]},
						{"name": "Rate", "chartType": "line", "values": [2, 3]},
					],
				},
			}
		)
		self.assertEqual(spec["kind"], "mixed")
		self.assertEqual([series["kind"] for series in spec["series"]], ["bar", "line"])

	def test_percentage_aging_is_aggregated_and_negative_values_fallback(self):
		raw = {
			"type": "percentage",
			"data": {
				"labels": ["Current", "30 days"],
				"datasets": [
					{"name": "Customer A", "values": [40, 10]},
					{"name": "Customer B", "values": [25, 25]},
				],
			},
		}
		spec = normalize_report_chart(raw)
		self.assertEqual(spec["kind"], "percentage_stacked")
		self.assertEqual([series["values"] for series in spec["series"]], [[65], [35]])

		raw["data"]["datasets"][1]["values"][0] = -1
		invalid = normalize_report_chart(raw)
		self.assertEqual(invalid["status"], "invalid")
		self.assertEqual(invalid["diagnostic"]["code"], "negative_percentage_value")

	def test_rejects_non_finite_mismatch_and_oversized_data(self):
		base = {"type": "line", "data": {"labels": ["A"], "datasets": []}}
		base["data"]["datasets"] = [{"values": [float("nan")]}]
		self.assertEqual(normalize_report_chart(base)["diagnostic"]["code"], "non_finite_value")

		base["data"]["datasets"] = [{"values": [1, 2]}]
		self.assertEqual(normalize_report_chart(base)["diagnostic"]["code"], "dataset_length_mismatch")

		labels = [str(index) for index in range(MAX_NATIVE_CHART_POINTS + 1)]
		oversized = normalize_report_chart(
			{
				"type": "line",
				"data": {"labels": labels, "datasets": [{"values": list(range(len(labels)))}]},
			}
		)
		self.assertEqual(oversized["diagnostic"]["code"], "too_many_points")

	def test_renderer_policy_prefers_lilaq_then_svg_then_omission(self):
		ready = normalize_report_chart(
			{
				"type": "bar",
				"data": {"labels": ["A"], "datasets": [{"values": [1]}]},
			}
		)
		resolved, metadata = resolve_chart_render(ready, "<svg/>", "lilaq")
		self.assertEqual(resolved["engine"], "lilaq")
		self.assertEqual(metadata["status"], "ready")
		resolved, metadata = resolve_chart_render(ready, "<svg/>", "frappe_svg")
		self.assertEqual(resolved["engine"], "frappe_svg")
		self.assertEqual(metadata["reason"], "engine_disabled")
		resolved, metadata = resolve_chart_render(ready, None, "frappe_svg")
		self.assertEqual(resolved["engine"], "none")
		self.assertEqual(metadata["reason"], "engine_disabled_no_svg")

		unsupported = normalize_report_chart(
			{"type": "pie", "data": {"labels": ["A"], "datasets": [{"values": [1]}]}}
		)
		resolved, metadata = resolve_chart_render(unsupported, "<svg/>", "lilaq")
		self.assertEqual(resolved["engine"], "frappe_svg")
		self.assertEqual(metadata["status"], "fallback")
		resolved, metadata = resolve_chart_render(unsupported, None, "lilaq")
		self.assertEqual(resolved["engine"], "none")
		self.assertEqual(metadata["status"], "omitted")

	def test_chart_theme_defaults_and_bounds(self):
		theme = normalize_chart_theme(
			{
				"reportTheme": {
					"negativeColor": "#AA0000",
					"chartPalette": ["#111111"],
					"chart": {"gridStrokePt": 99, "labelSizePt": 2, "legendPosition": "Top"},
				}
			}
		)
		self.assertEqual(theme["grid_stroke_pt"], 5)
		self.assertEqual(theme["label_size_pt"], 6)
		self.assertEqual(theme["legend_position"], "top")
		self.assertEqual(theme["negative_color"], "#AA0000")


class TestReportChartSvgSanitization(FrappeTestCase):
	def test_preserves_legitimate_frappe_svg_features(self):
		svg = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 50">
		<defs><linearGradient id="g"><stop offset="0" stop-color="#fff"/></linearGradient>
		<clipPath id="c"><rect x="0" y="0" width="100" height="50"/></clipPath></defs>
		<g clip-path="url(#c)" transform="translate(1 1)"><path d="M0 0 L10 10" fill="url(#g)"/><text x="2" y="12">A</text></g></svg>"""
		cleaned = sanitize_chart_svg(svg)
		self.assertIsNotNone(cleaned)
		self.assertIn("linearGradient", cleaned)
		self.assertIn("clip-path", cleaned)
		self.assertIn("transform", cleaned)

	def test_removes_active_and_external_content(self):
		svg = """<svg xmlns="http://www.w3.org/2000/svg" onclick="alert(1)">
		<script>alert(1)</script><foreignObject><div>bad</div></foreignObject>
		<image href="https://example.com/a.png"/><path d="M0 0 L1 1"/></svg>"""
		cleaned = sanitize_chart_svg(svg)
		self.assertIsNotNone(cleaned)
		self.assertNotIn("script", cleaned)
		self.assertNotIn("foreignObject", cleaned)
		self.assertNotIn("onclick", cleaned)
		self.assertNotIn("example.com", cleaned)

	def test_rejects_malformed_or_contentless_svg(self):
		self.assertIsNone(sanitize_chart_svg("<svg><path></svg>"))
		self.assertIsNone(sanitize_chart_svg('<svg xmlns="http://www.w3.org/2000/svg"/>'))


class TestBasicReportChartCompatibility(FrappeTestCase):
	def test_native_injection_prevents_legacy_svg_duplication(self):
		legacy = '#if "chart_svg" in data [#image(data.chart_svg)]\n// TABLE SETUP\n'
		source = _prepare_basic_chart_source(
			legacy,
			{"chart_spec": {"engine": "lilaq"}},
			{"report": {"chart_enabled": True}},
		)
		self.assertEqual(source.count("crispy-chart("), 1)
		self.assertEqual(source.count("CRISPY-CHART-SECTION v2"), 1)

	def test_existing_native_and_svg_fallback_sources_are_not_reinjected(self):
		native = "#crispy-chart(data.chart_spec)"
		self.assertEqual(
			_prepare_basic_chart_source(
				native,
				{"chart_spec": {"engine": "lilaq"}},
				{"report": {"chart_enabled": True}},
			),
			native,
		)
		fallback = "#image(data.chart_svg)"
		self.assertEqual(
			_prepare_basic_chart_source(
				fallback,
				{"chart_spec": {"engine": "frappe_svg"}},
				{"report": {"chart_enabled": True}},
			),
			fallback,
		)

	def test_advanced_format_detection(self):
		from types import SimpleNamespace

		self.assertTrue(_is_basic_report_format(SimpleNamespace(raw_typst=0)))
		self.assertFalse(_is_basic_report_format(SimpleNamespace(raw_typst=1)))
