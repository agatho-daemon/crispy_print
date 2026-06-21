# Typst Cookbook for Crispy Report Templates

Use these snippets inside `typst_code` for report-mode formats.

## 1) Safe text helper

```typst
#let asText(v) = if v == none { "" } else { str(v) }
```

## 2) Filters block (toggle-safe)

```typst
#if "filters" in data and data.filters.len() > 0 [
  #block(fill: rgb("f8fafc"), inset: 8pt, radius: 4pt)[
    #text(weight: "semibold", size: 8pt)[Filters]
    #v(0.3em)
    #grid(
      columns: (auto, 1fr) * 2,
      column-gutter: 8pt,
      row-gutter: 4pt,
      ..data.filters.map(f => (
        text(size: 8pt, weight: "medium")[#asText(f.label):],
        text(size: 8pt)[#asText(f.value)],
      )).flatten()
    )
  ]
]
```

## 3) Summary block (label/value list)

```typst
#if "report_summary" in data and data.report_summary.len() > 0 [
  #block(stroke: 0.5pt + rgb("#e5e7eb"), inset: 8pt, radius: 4pt)[
    #grid(
      columns: (1fr, auto),
      column-gutter: 12pt,
      row-gutter: 4pt,
      ..data.report_summary.map(item => (
        text(size: 8pt, fill: rgb("#475569"))[#asText(item.label)],
        text(size: 9pt, weight: "semibold")[#asText(item.value)],
      )).flatten()
    )
  ]
]
```

## 4) Chart block (if present)

```typst
#if "chart_svg" in data and data.chart_svg != "" [
  #block(stroke: 0.5pt + rgb("#e5e7eb"), inset: 8pt, radius: 4pt)[
    #align(center)[#image(data.chart_svg, width: 100%, height: 210pt, fit: "contain")]
  ]
]
```

## 5) Main table with numeric alignment

```typst
#let isNumeric(col) = "is_numeric" in col and col.is_numeric
#let colWidth(col) = if "width" in col and col.width != "auto" { eval(col.width) } else { auto }

#table(
  columns: data.columns.map(colWidth),
  align: (x, y) => if y == 0 { center + horizon } else if isNumeric(data.columns.at(x)) { right + horizon } else { left + horizon },
  fill: (x, y) => if y == 0 { rgb("f1f5f9") },
  inset: (top: 2pt, right: 2pt, bottom: 2pt, left: 2pt),
  table.header(..data.columns.map(c => text(weight: "semibold")[#asText(c.label)])),
  ..data.rows.map(row => row.cells.map(cell => [#asText(cell.value)])).flatten(),
)
```

## 6) Totals footer controlled by `show_totals`

```typst
#let showTotals = ("show_totals" in data and data.show_totals) or !("show_totals" in data)

#if showTotals [
  #v(0.6em)
  #align(right)[
    #text(size: 8pt, fill: rgb("#64748b"))[Total Records: #data.total_rows]
  ]
]
```

## Notes

- Always guard optional keys with `"key" in data` before access.
- In some preview payloads, rows can be absent or shape-shifted; prefer defensive checks.
- Keep helper names consistent (`asText`, `isNumeric`, etc.) to reduce template errors.
