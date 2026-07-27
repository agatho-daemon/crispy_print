import {
  BinaryBitmap,
  DecodeHintType,
  HybridBinarizer,
  MultiFormatReader,
  RGBLuminanceSource,
} from "@zxing/library";
import { execFileSync } from "node:child_process";
import { readFileSync, writeFileSync } from "node:fs";
import { PNG } from "pngjs";

export function decodeQrPng(buffer: Buffer): string {
  const png = PNG.sync.read(buffer);
  const luminance = new Uint8ClampedArray(png.width * png.height);
  for (
    let sourceOffset = 0, targetOffset = 0;
    sourceOffset < png.data.length;
    sourceOffset += 4
  ) {
    luminance[targetOffset++] = Math.round(
      (png.data[sourceOffset] +
        2 * png.data[sourceOffset + 1] +
        png.data[sourceOffset + 2]) /
        4,
    );
  }
  const source = new RGBLuminanceSource(luminance, png.width, png.height);
  const bitmap = new BinaryBitmap(new HybridBinarizer(source));
  const reader = new MultiFormatReader();
  reader.setHints(new Map([[DecodeHintType.TRY_HARDER, true]]));
  return reader.decode(bitmap).getText();
}

export function decodeQrPdf(
  pdfBase64: string,
  pdfPath: string,
  pngPrefix: string,
): string {
  writeFileSync(pdfPath, Buffer.from(pdfBase64, "base64"));
  execFileSync("pdftoppm", [
    "-f",
    "1",
    "-singlefile",
    "-png",
    "-r",
    "300",
    pdfPath,
    pngPrefix,
  ]);
  return decodeQrPng(readFileSync(`${pngPrefix}.png`));
}
