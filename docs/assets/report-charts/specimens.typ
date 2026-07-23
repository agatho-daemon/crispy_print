#import "@local/crispy-charts:0.1.1": crispy-chart

#set page(width: 132mm, height: 130mm, margin: 8mm, fill: rgb("#f8fafc"))
#set text(font: ("Inter", "Arial"), size: 8pt, fill: rgb("#0f172a"))

#let theme = (
  palette: ("#2563eb", "#0f766e", "#7c3aed", "#b45309"),
  negative_color: "#b91c1c",
  muted_color: "#475569",
  grid_color: "#cbd5e1",
  legend_position: "bottom",
  data_labels: "auto",
)

#let specimen(title, spec) = {
  text(size: 12pt, weight: "bold", fill: rgb("#0f172a"))[#title]
  v(3pt)
  crispy-chart(spec, theme: theme, width: 100%, height: 58mm)
}

#specimen(
  "Bar",
  (
    kind: "bar",
    labels: ("Jan", "Feb", "Mar", "Apr"),
    series: ((name: "Revenue", kind: "bar", values: (42, 58, 51, 69)),),
    options: (:),
    value_format: (suffix: "K"),
    accessibility: (summary: "Monthly revenue bar chart."),
  ),
)

#pagebreak()
#specimen(
  "Grouped bar",
  (
    kind: "grouped_bar",
    labels: ("Q1", "Q2", "Q3", "Q4"),
    series: (
      (name: "Actual", kind: "bar", values: (82, 94, 88, 106)),
      (name: "Budget", kind: "bar", values: (78, 90, 96, 101)),
    ),
    options: (:),
    value_format: (suffix: "K"),
    accessibility: (summary: "Actual and budget grouped bars."),
  ),
)

#pagebreak()
#specimen(
  "Line",
  (
    kind: "line",
    labels: ("Jan", "Feb", "Mar", "Apr", "May", "Jun"),
    series: (
      (name: "Cash balance", kind: "line", values: (74, 81, none, 92, 88, 103)),
      (name: "Forecast", kind: "line", values: (70, 78, 84, 89, 95, 101)),
    ),
    options: (:),
    value_format: (suffix: "K"),
    accessibility: (summary: "Cash balance and forecast line chart with a missing point."),
  ),
)

#pagebreak()
#specimen(
  "Mixed",
  (
    kind: "mixed",
    labels: ("Q1", "Q2", "Q3", "Q4"),
    series: (
      (name: "Sales", kind: "bar", values: (120, 145, 138, 167)),
      (name: "Margin", kind: "line", values: (22, 26, 24, 29)),
    ),
    options: (:),
    value_format: (suffix: "K"),
    accessibility: (summary: "Sales bars with a margin line."),
  ),
)

#pagebreak()
#specimen(
  "Horizontal bar",
  (
    kind: "horizontal_bar",
    labels: ("Services", "Materials", "Labor", "Overhead"),
    series: ((name: "Cost", kind: "bar", values: (63, 91, 76, 38)),),
    options: (:),
    value_format: (suffix: "K"),
    accessibility: (summary: "Cost by category horizontal bars."),
  ),
)

#pagebreak()
#specimen(
  "Percentage aging",
  (
    kind: "percentage_stacked",
    labels: ("Current", "30 days", "60 days", "90+ days"),
    series: (
      (name: "Current", kind: "bar", values: (56,)),
      (name: "30 days", kind: "bar", values: (24,)),
      (name: "60 days", kind: "bar", values: (13,)),
      (name: "90+ days", kind: "bar", values: (7,)),
    ),
    options: (stacked: true, orientation: "horizontal"),
    value_format: (suffix: "%"),
    accessibility: (summary: "Receivables aging distribution."),
  ),
)

#pagebreak()
#specimen(
  "Waterfall",
  (
    kind: "waterfall",
    labels: ("Opening", "Income", "Expense", "Tax", "Adjustment"),
    series: ((name: "Movement", kind: "bar", values: (100, 42, -29, -11, 8)),),
    options: (:),
    value_format: (suffix: "K"),
    accessibility: (summary: "Cumulative accounting movement waterfall."),
  ),
)
