#import "@preview/zebra:0.1.0": qrcode as zebra-qrcode, datamatrix as zebra-datamatrix

#let _sizing(width, height, module-size) = {
  if width != auto {
    (width: width)
  } else if height != auto {
    (height: height)
  } else {
    (module-size: module-size)
  }
}

#let crispy-qrcode(
  data,
  options: (:),
  quiet-zone: true,
  width: auto,
  height: auto,
  module-size: 3pt,
  fill: black,
  background-fill: none,
) = zebra-qrcode(
  data,
  options: options,
  quiet-zone: quiet-zone,
  fill: fill,
  background-fill: background-fill,
  .._sizing(width, height, module-size),
)

#let crispy-datamatrix(
  data,
  options: (:),
  quiet-zone: true,
  width: auto,
  height: auto,
  module-size: 3pt,
  fill: black,
  background-fill: none,
) = zebra-datamatrix(
  data,
  options: options,
  quiet-zone: quiet-zone,
  fill: fill,
  background-fill: background-fill,
  .._sizing(width, height, module-size),
)
