import { readFileSync, writeFileSync } from "node:fs";
import { resolve } from "node:path";

import {
  buildReportTypstFromConfig,
  normalizeReportBuilderConfig,
} from "../crispy_print/public/js/utils/reportBuilder";

const sampleIds = [
  "statement-of-account",
  "accounts-receivable-aging",
  "accounts-payable-aging",
];
const sampleDirectory = resolve(
  process.cwd(),
  "crispy_print/examples/formats",
);

for (const sampleId of sampleIds) {
  const path = resolve(sampleDirectory, `${sampleId}.json`);
  const payload = JSON.parse(readFileSync(path, "utf8"));
  const settings = JSON.parse(payload.format.presentation_settings);
  const config = normalizeReportBuilderConfig(
    settings.report,
    payload.format.report_renderer,
  );
  config.mode = "basic";
  config.renderer = payload.format.report_renderer;
  payload.format.presentation_settings = JSON.stringify({
    ...settings,
    report: config,
  });
  payload.format.typst_code = buildReportTypstFromConfig(config, {
    language: payload.format.default_print_language || "en",
  });
  writeFileSync(path, `${JSON.stringify(payload, null, 2)}\n`, "utf8");
}
