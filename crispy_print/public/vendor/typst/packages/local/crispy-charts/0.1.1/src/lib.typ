#import "@preview/lilaq:0.6.0" as lq

#let _default-palette = (
  "#1e3a8a",
  "#2563eb",
  "#0f766e",
  "#b45309",
  "#7c3aed",
  "#be123c",
)

#let _get(dict, key, default) = if type(dict) == dictionary {
  dict.at(key, default: default)
} else {
  default
}

#let _paint(value, default) = {
  let candidate = if type(value) == str { value } else { default }
  rgb(candidate)
}

#let _theme(theme) = {
  let palette = _get(theme, "palette", _default-palette)
  if type(palette) != array or palette.len() == 0 {
    palette = _default-palette
  }
  (
    palette: palette,
    horizontal-grid: _get(theme, "horizontal_grid", true),
    vertical-grid: _get(theme, "vertical_grid", true),
    minor-grid: _get(theme, "minor_grid", false),
    grid-color: _paint(_get(theme, "grid_color", "#cbd5e1"), "#cbd5e1"),
    grid-stroke: _get(theme, "grid_stroke_pt", 0.4) * 1pt,
    axis-color: _paint(_get(theme, "axis_color", "#64748b"), "#64748b"),
    axis-stroke: _get(theme, "axis_stroke_pt", 0.6) * 1pt,
    zero-color: _paint(_get(theme, "zero_line_color", "#475569"), "#475569"),
    zero-stroke: _get(theme, "zero_line_stroke_pt", 1.0) * 1pt,
    legend-position: _get(theme, "legend_position", "auto"),
    label-size: _get(theme, "label_size_pt", 8) * 1pt,
    data-labels: _get(theme, "data_labels", "auto"),
    line-stroke: _get(theme, "line_stroke_pt", 1.2) * 1pt,
    marker-size: _get(theme, "marker_size_pt", 4) * 1pt,
    accessibility: _get(theme, "accessibility_mode", true),
    negative-color: _paint(_get(theme, "negative_color", "#b91c1c"), "#b91c1c"),
    muted-color: _paint(_get(theme, "muted_color", "#64748b"), "#64748b"),
  )
}

#let _series-color(theme, index) = {
  let value = theme.palette.at(calc.rem(index, theme.palette.len()))
  _paint(value, _default-palette.at(calc.rem(index, _default-palette.len())))
}

#let _series-name(series, index) = {
  let value = _get(series, "name", "")
  if value == "" { "Series " + str(index + 1) } else { value }
}

#let _kind(series, default) = _get(series, "kind", default)

#let _legend(spec, theme) = {
  let series = _get(spec, "series", ())
  let position = theme.legend-position
  let visible = position != "hidden" and series.len() > 1
  if visible {
    let cells = series.enumerate().map(((index, item)) => {
      let color = _series-color(theme, index)
      let marker = if theme.accessibility {
        ("●", "■", "▲", "◆", "+", "×").at(calc.rem(index, 6))
      } else {
        "■"
      }
      box(inset: (right: 12pt, bottom: 3pt))[
        #text(size: theme.label-size, fill: color)[#marker]
        #h(3pt)
        #text(size: theme.label-size, fill: theme.muted-color)[#_series-name(item, index)]
      ]
    })
    grid(columns: (auto,) * calc.min(4, cells.len()), ..cells)
  }
}

#let _ticks(labels, max-labels: 12) = {
  if labels.len() <= max-labels {
    labels.enumerate()
  } else {
    let step = calc.ceil(labels.len() / max-labels)
    labels.enumerate().filter(((index, _)) => calc.rem(index, step) == 0)
  }
}

#let _values(series) = _get(series, "values", ())

#let _numeric-values(series) = _values(series).filter(value => value != none)

#let _has-negative(series) = series.any(item => _numeric-values(item).any(value => value < 0))

#let _data-labels-enabled(spec, theme) = {
  theme.data-labels == "always" or (
    theme.data-labels == "auto" and _get(spec, "labels", ()).len() <= 8
  )
}

#let _compact-number(value) = {
  let absolute = calc.abs(value)
  let compact = if absolute >= 1000000000 {
    str(calc.round(value / 1000000000, digits: 1)) + "B"
  } else if absolute >= 1000000 {
    str(calc.round(value / 1000000, digits: 1)) + "M"
  } else if absolute >= 1000 {
    str(calc.round(value / 1000, digits: 1)) + "K"
  } else {
    str(calc.round(value, digits: 2))
  }
  compact
}

#let _format-value(value, spec) = {
  let format = _get(spec, "value_format", (:))
  let suffix = _get(format, "suffix", "")
  _compact-number(value) + suffix
}

#let _format-ticks(ticks, ..args) = ticks.map(value => _compact-number(value))

#let _numeric-axis(theme) = (
  mirror: false,
  subticks: if theme.minor-grid { 1 } else { none },
  format-ticks: _format-ticks,
)

#let _unit-label(spec, theme) = {
  let format = _get(spec, "value_format", (:))
  let currency = _get(format, "currency", "")
  let suffix = _get(format, "suffix", "")
  let unit = if currency != "" { currency } else { suffix }
  if unit != "" {
    let rtl = _get(_get(spec, "options", (:)), "rtl", false)
    align(if rtl { right } else { left })[
      #text(size: theme.label-size, fill: theme.muted-color)[#unit]
    ]
  }
}

#let _bar-labels(xs, values, theme, spec, offset: 0) = {
  xs.zip(values).filter(((_, value)) => value != none).map(((x, value)) => {
    lq.place(
      x + offset,
      value,
      text(size: theme.label-size * 0.9, fill: theme.axis-color)[#_format-value(value, spec)],
      align: if value < 0 { top } else { bottom },
    )
  })
}

#let _configured(theme, body) = {
  show: lq.cond-set(
    lq.grid.with(kind: "x"),
    stroke: if theme.vertical-grid { theme.grid-stroke + theme.grid-color } else { none },
    stroke-sub: if theme.vertical-grid and theme.minor-grid {
      (theme.grid-stroke / 2) + theme.grid-color.lighten(35%)
    } else { none },
  )
  show: lq.cond-set(
    lq.grid.with(kind: "y"),
    stroke: if theme.horizontal-grid { theme.grid-stroke + theme.grid-color } else { none },
    stroke-sub: if theme.horizontal-grid and theme.minor-grid {
      (theme.grid-stroke / 2) + theme.grid-color.lighten(35%)
    } else { none },
  )
  show: lq.set-spine(stroke: theme.axis-stroke + theme.axis-color)
  show: lq.set-tick(stroke: (theme.axis-stroke * 0.75) + theme.axis-color)
  show lq.selector(lq.tick-label): set text(size: theme.label-size, fill: theme.axis-color)
  show lq.selector(lq.label): set text(size: theme.label-size, fill: theme.axis-color)
  body
}

#let _bar-diagram(spec, theme, width, height) = {
  let labels = _get(spec, "labels", ())
  let series = _get(spec, "series", ())
  let xs = range(labels.len())
  let grouped = series.len() > 1
  let bar-width = if grouped { 0.78 / series.len() } else { 72% }
  let plots = series.enumerate().map(((index, item)) => {
    let offset = if grouped { (index - (series.len() - 1) / 2) * bar-width } else { 0 }
    let values = _values(item).map(value => if value == none { 0 } else { value })
    lq.bar(
      xs,
      values,
      width: bar-width,
      offset: offset,
      fill: values.map(value => if value < 0 { theme.negative-color } else { _series-color(theme, index) }),
    )
  })
  let labels-content = if _data-labels-enabled(spec, theme) {
    series.enumerate().map(((index, item)) => {
      let offset = if grouped { (index - (series.len() - 1) / 2) * bar-width } else { 0 }
      _bar-labels(xs, _values(item), theme, spec, offset: offset)
    }).flatten()
  } else { () }
  let zero = if _has-negative(series) {
    (lq.line((0%, 0), (100%, 0), stroke: theme.zero-stroke + theme.zero-color),)
  } else { () }
  _configured(theme, lq.diagram(
    width: width,
    height: height,
    legend: none,
    xaxis: (
      ticks: _ticks(labels),
      subticks: none,
      mirror: false,
      inverted: _get(_get(spec, "options", (:)), "invert_categories", false),
    ),
    yaxis: _numeric-axis(theme),
    ..plots,
    ..zero,
    ..labels-content,
  ))
}

#let _line-plot(item, index, theme) = {
  let values = _values(item).map(value => if value == none { float.nan } else { value })
  // Lilaq mark names are case-sensitive. `d` is the supported diamond mark.
  let marks = ("o", "s", "^", "d", "+", "x")
  let dashes = ("solid", "dashed", "dotted", "dash-dotted")
  lq.plot(
    range(values.len()),
    values,
    color: _series-color(theme, index),
    stroke: (
      thickness: theme.line-stroke,
      dash: if theme.accessibility { dashes.at(calc.rem(index, dashes.len())) } else { "solid" },
    ),
    mark: if theme.accessibility { marks.at(calc.rem(index, marks.len())) } else { "o" },
    mark-size: theme.marker-size,
  )
}

#let _line-diagram(spec, theme, width, height) = {
  let labels = _get(spec, "labels", ())
  let series = _get(spec, "series", ())
  let zero = if _has-negative(series) {
    (lq.line((0%, 0), (100%, 0), stroke: theme.zero-stroke + theme.zero-color),)
  } else { () }
  _configured(theme, lq.diagram(
    width: width,
    height: height,
    legend: none,
    xaxis: (
      ticks: _ticks(labels),
      subticks: none,
      mirror: false,
      inverted: _get(_get(spec, "options", (:)), "invert_categories", false),
    ),
    yaxis: _numeric-axis(theme),
    ..series.enumerate().map(((index, item)) => _line-plot(item, index, theme)),
    ..zero,
  ))
}

#let _mixed-diagram(spec, theme, width, height) = {
  let labels = _get(spec, "labels", ())
  let series = _get(spec, "series", ())
  let bar-series = series.enumerate().filter(((_, item)) => _kind(item, "line") == "bar")
  let bar-count = calc.max(1, bar-series.len())
  let bar-width = 0.72 / bar-count
  let plots = series.enumerate().map(((index, item)) => {
    if _kind(item, "line") == "bar" {
      let bar-index = bar-series.position(pair => pair.first() == index)
      let offset = (bar-index - (bar-count - 1) / 2) * bar-width
      let values = _values(item).map(value => if value == none { 0 } else { value })
      lq.bar(
        range(labels.len()),
        values,
        width: bar-width,
        offset: offset,
        fill: values.map(value => if value < 0 { theme.negative-color } else { _series-color(theme, index).lighten(25%) }),
      )
    } else {
      _line-plot(item, index, theme)
    }
  })
  let zero = if _has-negative(series) {
    (lq.line((0%, 0), (100%, 0), stroke: theme.zero-stroke + theme.zero-color),)
  } else { () }
  _configured(theme, lq.diagram(
    width: width,
    height: height,
    legend: none,
    xaxis: (ticks: _ticks(labels), subticks: none, mirror: false),
    yaxis: _numeric-axis(theme),
    ..plots,
    ..zero,
  ))
}

#let _horizontal-diagram(spec, theme, width, height) = {
  let labels = _get(spec, "labels", ())
  let series = _get(spec, "series", ())
  let item = series.first(default: (:))
  let values = _values(item)
	let fills = values.map(value => if value != none and value < 0 { theme.negative-color } else { _series-color(theme, 0) })
  let ys = range(labels.len())
  let labels-content = if _data-labels-enabled(spec, theme) {
    ys.zip(values).filter(((_, value)) => value != none).map(((y, value)) => {
      lq.place(value, y, text(size: theme.label-size * 0.9)[#_format-value(value, spec)], align: left + horizon)
    })
  } else { () }
  let zero = if _has-negative(series) {
    (lq.line((0, 0%), (0, 100%), stroke: theme.zero-stroke + theme.zero-color),)
  } else { () }
  _configured(theme, lq.diagram(
    width: width,
    height: height,
    legend: none,
    xaxis: _numeric-axis(theme),
    yaxis: (ticks: _ticks(labels, max-labels: 20), subticks: none, mirror: false),
    lq.hbar(
      values.map(value => if value == none { 0 } else { value }),
      ys,
      width: 68%,
      fill: fills,
    ),
    ..zero,
    ..labels-content,
  ))
}

#let _percentage-diagram(spec, theme, width, height) = {
  let series = _get(spec, "series", ())
  let values = series.map(item => _values(item).first(default: 0))
  let total = values.sum(default: 0)
  let percentages = if total > 0 { values.map(value => value / total * 100) } else { values }
  let starts = range(values.len()).map(index => percentages.slice(0, index).sum(default: 0))
  let ends = range(values.len()).map(index => starts.at(index) + percentages.at(index))
  let plots = range(values.len()).map(index => lq.hbar(
    (ends.at(index),),
    (0,),
    base: starts.at(index),
    width: 55%,
    fill: _series-color(theme, index),
  ))
  let labels-content = range(values.len()).filter(index => percentages.at(index) >= 6).map(index => {
    lq.place(
      (starts.at(index) + ends.at(index)) / 2,
      0,
      text(size: theme.label-size, weight: "bold", fill: white)[#calc.round(percentages.at(index))%],
      align: center + horizon,
    )
  })
  _configured(theme, lq.diagram(
    width: width,
    height: height,
    legend: none,
    xlim: (0, 100),
    xaxis: (tick-distance: 10, subticks: none, mirror: false),
    yaxis: none,
    ..plots,
    ..labels-content,
  ))
}

#let _waterfall-diagram(spec, theme, width, height) = {
  let labels = _get(spec, "labels", ())
  let values = _values(_get(spec, "series", ()).first(default: (:)))
  let starts = range(values.len()).map(index => values.slice(0, index).sum(default: 0))
  let ends = range(values.len()).map(index => starts.at(index) + values.at(index))
  let fills = values.map(value => if value < 0 { theme.negative-color } else { _series-color(theme, 0) })
  let labels-content = if _data-labels-enabled(spec, theme) {
    range(values.len()).map(index => lq.place(
      index,
      ends.at(index),
      text(size: theme.label-size * 0.9)[#_format-value(ends.at(index), spec)],
      align: if values.at(index) < 0 { top } else { bottom },
    ))
  } else { () }
  _configured(theme, lq.diagram(
    width: width,
    height: height,
    legend: none,
    xaxis: (ticks: _ticks(labels), subticks: none, mirror: false),
    yaxis: _numeric-axis(theme),
    lq.bar(range(values.len()), ends, base: starts, width: 68%, fill: fills),
    lq.line((0%, 0), (100%, 0), stroke: theme.zero-stroke + theme.zero-color),
    ..labels-content,
  ))
}

#let crispy-chart(
  spec,
  theme: (:),
  width: 100%,
  height: 220pt,
) = {
  let normalized-theme = _theme(theme)
  let kind = _get(spec, "kind", "")
  let legend-position = normalized-theme.legend-position
  let legend-top = legend-position == "top" or legend-position == "auto"
  let legend = _legend(spec, normalized-theme)
  let body = if kind == "bar" or kind == "grouped_bar" {
    _bar-diagram(spec, normalized-theme, width, height)
  } else if kind == "line" {
    _line-diagram(spec, normalized-theme, width, height)
  } else if kind == "mixed" {
    _mixed-diagram(spec, normalized-theme, width, height)
  } else if kind == "horizontal_bar" {
    _horizontal-diagram(spec, normalized-theme, width, height)
  } else if kind == "percentage_stacked" {
    _percentage-diagram(spec, normalized-theme, width, height)
  } else if kind == "waterfall" {
    _waterfall-diagram(spec, normalized-theme, width, height)
  } else {
    none
  }
  if body != none {
    let chart-content = block(width: 100%)[
      #if legend-top and legend != none [#legend #v(5pt)]
      #_unit-label(spec, normalized-theme)
      #body
      #if not legend-top and legend != none [#v(5pt) #legend]
    ]
    figure(
      chart-content,
      alt: _get(_get(spec, "accessibility", (:)), "summary", "Report chart"),
      kind: "chart",
      supplement: none,
    )
  }
}
