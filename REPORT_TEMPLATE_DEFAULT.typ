// Crispy Print native report renderer.
// Available data: data.title, filters_map, report_summary, columns, rows, renderer.

#set text(font: "Inter", size: 9pt)

#let value-or-empty(dict, key) = if key in dict { dict.at(key) } else { "" }
#let report-filter(key) = if "filters_map" in data { value-or-empty(data.filters_map, key) } else { "" }
#let column-width(col) = {
  if "width_kind" not in col or col.width_kind == "auto" { auto }
  else if col.width_kind == "fr" { col.width_value * 1fr }
  else if col.width_kind == "pt" { col.width_value * 1pt }
  else if col.width_kind == "em" or col.width_kind == "rem" { col.width_value * 1em }
  else if col.width_kind == "%" { col.width_value * 1% }
  else if col.width_kind == "cm" { col.width_value * 1cm }
  else if col.width_kind == "mm" { col.width_value * 1mm }
  else if col.width_kind == "in" { col.width_value * 1in }
  else { auto }
}

#align(center)[
  #text(size: 16pt, weight: "bold")[#data.title]
  #if data.renderer == "receivable_payable" [
    #v(3pt)
    #text(size: 10pt, weight: "semibold")[#report-filter("party")]
    #if report-filter("tax_id") != "" [#linebreak()#text(size: 8pt)[Tax ID: #report-filter("tax_id")]]
    #linebreak()
    #text(size: 8pt)[#report-filter("ageing_based_on") #h(0.5em) #report-filter("report_date")]
  ] else if data.renderer == "financial_statement" [
    #v(3pt)
    #text(size: 11pt, weight: "semibold")[#report-filter("company")]
    #linebreak()
    #text(size: 8pt)[#report-filter("fiscal_year") #h(1em) #report-filter("presentation_currency")]
  ] else if data.renderer == "general_ledger" [
    #v(3pt)
    #text(size: 11pt, weight: "semibold")[#if report-filter("party") != "" { report-filter("party") } else { report-filter("account") }]
    #linebreak()
    #text(size: 8pt)[#report-filter("from_date") – #report-filter("to_date")]
  ] else if data.renderer == "bank_reconciliation" [
    #v(3pt)
    #text(size: 10pt, weight: "semibold")[#report-filter("account")]
    #linebreak()
    #text(size: 8pt)[#report-filter("company") #h(1em) #report-filter("report_date")]
  ]
]

#v(10pt)

#if "filters" in data and data.filters.len() > 0 [
  #block(fill: rgb("f5f5f5"), inset: 8pt, radius: 3pt, width: 100%)[
    #grid(
      columns: (auto, 1fr) * 2,
      column-gutter: 10pt,
      row-gutter: 4pt,
      ..data.filters.map(f => (
        text(size: 8pt, weight: "semibold")[#f.label:],
        text(size: 8pt)[#f.value],
      )).flatten(),
    )
  ]
  #v(8pt)
]

#if "chart_svg" in data and data.chart_svg != "" [
  #align(center)[#image(data.chart_svg, width: 100%, height: 220pt, fit: "contain")]
  #v(10pt)
]

#if "report_summary" in data and data.report_summary.len() > 0 [
  #grid(
    columns: (1fr, auto),
    column-gutter: 10pt,
    row-gutter: 3pt,
    ..data.report_summary.map(item => (
      text(size: 8pt, weight: "semibold")[#item.label],
      text(size: 8pt)[#if "formatted_value" in item and item.formatted_value != "" { item.formatted_value } else { item.value }],
    )).flatten(),
  )
  #v(8pt)
]

#table(
  columns: data.columns.map(column-width),
  stroke: (x, y) => (top: if y == 0 { 1pt } else { 0.4pt }, bottom: 0.4pt, left: 0pt, right: 0pt),
  inset: (x: 5pt, y: 4pt),
  align: (x, y) => if y == 0 { center + horizon } else if data.columns.at(x).is_numeric { right + horizon } else { left + horizon },
  table.header(..data.columns.map(col => text(weight: "bold")[#col.label])),
  ..data.rows.map(row => {
    row.cells.enumerate().map(entry => {
      let idx = entry.at(0)
      let cell = entry.at(1)
      let content = if row.role == "grand_total" or row.role == "section" or row.is_bold {
        text(weight: "bold")[#cell.value]
      } else {
        [#cell.value]
      }
      if idx == 0 and "indent" in row and row.indent != none and row.indent > 0 {
        box(inset: (left: row.indent * 2em))[#content]
      } else {
        content
      }
    })
  }).flatten(),
)

#v(8pt)
#align(right)[#text(size: 8pt, fill: rgb("#666"))[Total Records: #data.total_rows]]
