# Report preview operational benchmark

Date: 2026-07-23  
Site: `fdev.local`  
Case: General Ledger, Wasaq Group General Trading, 2025-01-01 through
2026-07-22, eight readable default columns.

The benchmark is reproducible with
`crispy_print.dev_utils.perf_benchmarks.run_report_pipeline`. It is
non-mutating: it creates no format, File, report job, or business record.

## Cold pipeline result

| Stage | Time | Python peak | Process/child RSS signal |
| --- | ---: | ---: | ---: |
| ERPNext report execution | 3.537 s | 25.5 MiB | +51.6 MiB process |
| Report normalization | 7.024 s | 40.3 MiB | +18.5 MiB process |
| Temporary JSON serialization | 1.269 s | 38.0 MiB | +40.3 MiB process |
| Typst source/data-file construction | 3.817 s | 90.4 MiB | +94.5 MiB process |
| Typst PDF compilation, forced cache miss | 5.363 s | 107.2 MiB | +1,549.2 MiB child max RSS |
| Base64 decode | 0.041 s | 50.0 MiB | — |
| RPC JSON serialization | 0.066 s | 57.2 MiB | — |
| PDF page metadata scan | 3.043 s | 29.2 MiB | +22.3 MiB process |

The measured cold server stages before browser parsing total approximately
21.1 seconds. Typst itself reported 5.313 seconds against the configured
60-second render timeout, leaving about 54.6 seconds of render-time headroom.
A repeated identical compile was a cache hit and returned in 43 ms, although
snapshot presentation/source construction still took approximately 3.75
seconds.

## Payload size

| Quantity | Result |
| --- | ---: |
| Rows / columns | 11,126 / 8 |
| Temporary normalized JSON | 19,906,559 bytes |
| Typst source (data externalized) | 4,994 bytes |
| PDF | 22,481,405 bytes |
| PDF pages | 587 |
| Base64 PDF | 29,975,208 bytes |
| Complete RPC JSON | 29,975,270 bytes |
| Base64 expansion | 33.33% |

## Browser/PDF.js memory

PDF.js rendering is bounded to five active pages. Each retained page has one
high-resolution canvas and one matching selectable-text layer. Earlier browser
acceptance on the same report family verified five active pages at the
beginning, middle, and end while all other pages remained placeholders.

The benchmark found that those placeholder canvas elements still carried the
HTML default 300×150 backing size. At four bytes per pixel, 587 placeholders
represent a theoretical 100.8 MiB, and the earlier 1,408-page result represents
241.7 MiB, before counting the five useful rendered canvases. The renderer now
sets every placeholder backing store to 0×0 on registration and allocates
pixels only when a page enters the five-page window. Text-layer DOM follows the
same window and is cancelled and cleared with its canvas. The focused PDF
renderer test verifies the five-page bound, zero-width offscreen backing store,
selectable text creation, and text cleanup during page eviction.

A fresh live browser heap sample was not available because the built-in browser
connection was unavailable during this benchmark. The deterministic backing
store calculation, existing live five-canvas evidence, and renderer regression
test cover the allocation decision without substituting another browser.

## Decision

Large report PDFs need binary transfer. The measured 22.5 MiB PDF becomes a
30.0 MiB JSON response and requires additional base64/string/decoded copies.
The recommended follow-up is an authenticated, short-lived binary response or
download endpoint for compiled report PDFs. Keep the current JSON response for
small previews during migration; switch at approximately 8 MiB of PDF output.

Large reports also need background compilation above an operational threshold.
The measured case completes inside the timeout, so background execution is not
required for ordinary reports. However, a cold 587-page compile used a
1.55 GiB child-process RSS signal and the full two-request pipeline occupied a
web worker for roughly 21 seconds. Concurrent examples of this size are not a
safe synchronous workload. Route reports to a bounded background queue when
any early signal crosses roughly 5,000 rows or 10 MiB of normalized JSON, with
per-site concurrency and memory limits. The background result should use the
same user/report/company/tab-bound expiring snapshot contract and the binary
PDF endpoint.

These thresholds are conservative starting points from one real site, not
universal constants. Record production telemetry for execution time, JSON/PDF
bytes, page count, compile time, cache hits, failures, and queue wait before
tuning them.
