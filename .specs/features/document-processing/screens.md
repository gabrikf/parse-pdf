# Document processing screens

**Verifier**: independent sub-agent (author != verifier)
**Round**: 2 (round 1 judged HEAD 19cf1ff)
**HEAD**: 28a6e1c

Pictures are the e2e stack's test data (local OpenRouter stub), so file names, sizes, page counts,
times, chip counts, budget numbers, summary text, error reason per `error_code`, feed order and
which parser each document used differ from the canvas sample data; those are notes on `same`
rows. Applied from `## Differences from the source`: the two loose text labels on DesktopDark are
not UI. All 11 pictures are at their frame's size (phone 375x812, tablet 768x1024, desktop
1280x1240) and their text reads at the capture's size: no picture is resized.

Round 2 reopened the rows marked `differs` in round 1 on the pictures re-saved at 28a6e1c, and
looked at every `same` row for a visible regression; nothing else was added or re-judged.

| Screen | Compared with | Verdict | Finding |
| --- | --- | --- | --- |
| `captures/PhoneEmpty.running.png` | `captures/PhoneEmpty.png` | matches | 0 rows differ |
| `captures/DesktopUpload.running.png` | `captures/DesktopUpload.png` | matches | round 1's 2 rows now same |
| `captures/PhonePages.running.png` | `captures/PhonePages.png` | diverges | round 1's row now same; 1 row `differs - regression` |
| `captures/PhoneConfirm.running.png` | `captures/PhoneConfirm.png` | matches | round 1's row now same |
| `captures/Main.running.png` | `captures/Main.png` | matches | round 1's row now same |
| `captures/PhoneLight.running.png` | `captures/PhoneLight.png` | matches | 0 rows differ |
| `captures/Tablet.running.png` | `captures/Tablet.png` | matches | round 1's 2 rows now same |
| `captures/DesktopDark.running.png` | `captures/DesktopDark.png` | matches | round 1's row now same |
| `captures/PhoneDark.running.png` | `captures/PhoneDark.png` | matches | 0 rows differ |
| `captures/PhoneFailed.running.png` | `captures/PhoneFailed.png` | matches | 0 rows differ |
| `captures/PhoneDelete.running.png` | `captures/PhoneDelete.png` | matches | 0 rows differ |

### `captures/PhoneEmpty.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| top bar: wordmark `Parse PDF` (serif italic, `PDF` purple) left, hairline under the bar | same | |
| top bar right: budget `<n> of 3,000` (mono) over `model pages today` | same | note: 1,568 instead of 1,240 (data) |
| no stories row, no filter chips | same | |
| empty state centered: outline circle with purple cloud-upload icon | same | |
| heading `No documents yet` (serif) | same | |
| sentence `Upload a PDF to read it page by page, with a short summary at the top.` | same | |
| filled purple button `Upload PDFs` | same | |
| small grey sentence `Files stay private to this browser and are deleted after 7 days.` | same | |
| bottom tab bar, hairline top: home, plus-square, moon icons | same | |

### `captures/DesktopUpload.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| left rail: wordmark, `Feed` (selected, tinted block), `Upload`, `Dark mode` with outline icons; hairline right edge | same | |
| right rail: `Parsers` guide (PyPDF, Gemini 3.1 Flash Lite, GPT-5 Mini with their lines, `Every summary is written by Gemini 3.1 Flash Lite.`), hairline, `Model pages today` big serif number `of 3,000`, purple meter, `Resets at 00:00 UTC. PyPDF parsing doesn't count.`, hairline, privacy line | same | note: 1,589 instead of 1,240 (data) |
| backdrop: grey scrim over the page | same | |
| backdrop: stories row (dashed `Upload` circle, document circles) and `Parsed` chip under the scrim | same | note: both document rings solid purple (two processing) where the capture has one dashed queued ring (data state) |
| backdrop: feed of document cards (summary, actions, no-text card, next card) under the scrim | same | round 2: ready card (summary box, action icons, `Page 1` preview, `View all 85 pages`), no-text card with `Reparse with Gemini` / `Delete`, next ready card, under the scrim. Round 1: differs - empty feed behind the dialog |
| dialog: white, rounded, centered; header `Upload PDFs` with close `×` right, hairline under it | same | |
| drop zone: dashed border, tinted, purple cloud-upload icon, `Drop PDFs here, or paste them`, `Up to 20 files, 50 MB each`, outlined `Choose files` | same | |
| `Parser` label and native select under it | same | note: shows `PyPDF · plain text` instead of `Gemini 3.1 Flash Lite · markdown` (user's pick) |
| list heading `<n> of <m> files uploaded` | same | note: `2 of 4` in round 2 (`2 of 3` in round 1) |
| accepted rows: green check, file name, mono size right, hairline between rows | same | |
| rejected row: red warning triangle, name, size, red reason `This file isn't a PDF. Export it as a PDF and add it again.` | same | |
| password row: orange lock icon, name, size, orange `This PDF needs a password. It is used once to unlock the file and never stored.`, `Password` input with filled purple `Unlock` button on its right | same | round 2: drawn as the capture (`w3c-dummy-locked.pdf`, 14 KB). Round 1: differs - no password row, field or `Unlock` button |
| footer, hairline above: outlined `Add more files`, filled purple `Done`, right-aligned | same | |

### `captures/PhonePages.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| page behind: top bar with wordmark and budget, dimmed | same | |
| sheet: dark, rounded top corners, from just under the top bar to the bottom | differs - regression | the sheet starts at about y 282 of 812, so the dimmed page behind (chips `Parsed 4` / `Failed 0` / `All 4`, the card header and the top of its summary box) shows above it; it ends at the bottom with a `Showing 3 of 3 pages` line. Likely the sheet fits the 3 short stub pages; the capture fixes a sheet that starts under the top bar |
| sheet header: bold file name cut with ellipsis, close `×` right | same | |
| sheet header subline `<n> pages · <format> · <parser>` | same | note: `3 pages · markdown · Gemini 3.1 Flash Lite` in round 2 |
| hairline under the header | same | |
| `Page 1` small label above the page body | same | |
| page body rendered as markdown: serif heading (`The Constitution of the United States`), bold italic subheading (`Preamble`), serif paragraphs | same | round 2: a markdown page - serif heading `Page 1`, serif paragraph `Stub markdown for page 1.`; note: the stub's markdown has no subheading, so the bold italic subheading is not exercised. Round 1: differs - a PyPDF `text` page with no markdown drawn |
| hairline between pages, then `Page 2` label and its body | same | round 2: hairline, `Page 2` label and heading, then page 3, all in view |

### `captures/PhoneConfirm.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| page behind, dimmed: top bar with wordmark and budget | same | |
| page behind: stories row (`Upload` dashed circle, queued circle, processing circle with labels) above the chips | same | round 2: dashed `Upload` circle and two processing circles with labels, above the chips; note: two processing instead of queued + processing (data state). Round 1: differs - no stories row |
| page behind: chips `Parsed 3` (selected, purple tint), `Failed 2`, `All 7` | same | note: counts 3 / 0 / 5 (data) |
| page behind: card header (doc icon, name, meta, `Ready` badge, `…`) and summary box | same | note: summary shows a `Key points` label (stub markdown) |
| bottom sheet: white, rounded top corners, full width | same | |
| title `Reparse <file>?` bold | same | note: file name wraps to two lines (longer name) |
| sentence `Its pages and summary are cleared, then it runs again with the parser you pick.` | same | |
| `Parser` label; three bordered radio rows `PyPDF · plain text`, `Gemini 3.1 Flash Lite · markdown`, `GPT-5 Mini · OCR`; selected row purple border and tint | same | note: PyPDF selected instead of GPT-5 Mini |
| outlined `Cancel` and filled purple `Reparse`, right-aligned | same | |

### `captures/Main.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| left rail: wordmark, `Feed` selected, `Upload`, `Dark mode`, hairline right edge | same | |
| center column: stories row (dashed `Upload` circle with plus, document circles with name and status under each) | same | note: two processing (solid purple, orange `Processing`) instead of one queued (dashed grey, `Queued`) and one processing (data state) |
| hairline under the stories row | same | |
| chips `Parsed 3` (selected, purple border and tint), `Failed 2`, `All 7` | same | note: 3 / 0 / 5 (data) |
| ready card header: round doc icon, bold name, meta `<parser> · <n> pages · <time>`, green `Ready` badge, `…` | same | |
| summary box: tinted, hairline border, `Summary · Gemini 3.1 Flash Lite` label, serif overview, serif bullets | same | note: stub summary adds a `Key points` label before the bullets (summary markdown) |
| action row: book, refresh, copy icons left; trash right | same | |
| page preview `Page 1` bold + serif text cut with ellipsis, `View all <n> pages` link | same | |
| hairline between cards | same | |
| no-text card header: `No text` grey badge | same | |
| no-text box: bold `No text found on any page.` then `This usually means a scanned PDF or a photo of a page. Gemini 3.1 Flash Lite reads scanned pages.` | same | round 2: the capture's sentence. Round 1: differs - `... Try the gemini-3.1-flash-lite parser, which reads scans.` |
| no-text box buttons: filled purple `Reparse with Gemini`, outlined `Delete` | same | |
| next ready card header and summary box at the bottom | same | |
| right rail: parser guide, model pages meter, privacy line, hairlines | same | note: 1,550 instead of 1,240 (data) |

### `captures/PhoneLight.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| top bar: wordmark left, budget right, hairline | same | |
| stories row: `Upload` dashed circle, document circles with name and status | same | note: two processing instead of queued + processing (data state) |
| hairline under stories | same | |
| chips `Parsed` (selected), `Failed`, `All` with counts | same | |
| card header: doc icon, name cut with ellipsis, meta line cut, `Ready` badge, `…` | same | |
| summary box: label, serif overview, serif bullets | same | note: shorter stub summary with a `Key points` label, so the action row and `Page 1` preview show above the tab bar |
| bottom tab bar: home, plus-square, moon | same | |

### `captures/Tablet.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| narrow left icon rail: purple doc logo, home (selected tint), plus-square, moon; hairline right edge | same | |
| rate-limit banner on top of the column: warning icon, `Too many uploads in the last minute. You can upload again in 42 s.` on an orange tint | same | round 2: drawn as the capture; note: `23 s` instead of `42 s` (the wait from `Retry-After`). Round 1: differs - no banner |
| stories row: `Upload` dashed circle, document circles with name and status | same | note: two processing instead of queued + processing (data state) |
| hairline, chips `Parsed`, `Failed`, `All` with counts | same | |
| ready card: header, summary box, action row (book, refresh, copy; trash right), `Page 1` preview, `View all <n> pages` | same | |
| no-text card: `No text` badge; bold `No text found on any page.` then `This usually means a scanned PDF or a photo of a page. Gemini 3.1 Flash Lite reads scanned pages.` | same | round 2: the capture's sentence. Round 1: differs - `... Try the gemini-3.1-flash-lite parser, which reads scans.` |
| no-text buttons: `Reparse with Gemini` filled purple, `Delete` outlined | same | |
| no right rail, no bottom tab bar at 768 px | same | |

### `captures/DesktopDark.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| dark theme throughout: near-black background, hairline borders, lavender primary | same | |
| left rail: wordmark (`PDF` lavender), `Feed` selected, `Upload`, sun icon `Light mode` | same | |
| loose labels `scripts/phase.sh implement` and `annual-report` over the summary | same | left out per `## Differences from the source` (AD-025) |
| stories row and hairline | same | note: two processing instead of queued + processing (data state) |
| chips `Parsed` (selected, purple tint), `Failed`, `All` | same | |
| ready card: header with green `Ready` badge, summary box, action icons, `Page 1` preview, `View all` link | same | |
| no-text card: `No text` badge; bold `No text found on any page.` then `... Gemini 3.1 Flash Lite reads scanned pages.` | same | round 2: the capture's sentence. Round 1: differs - `... Try the gemini-3.1-flash-lite parser, which reads scans.` |
| no-text buttons: lavender filled `Reparse with Gemini` with dark text, outlined `Delete` | same | |
| next ready card | same | |
| right rail: parser guide, meter (lavender fill), privacy line | same | |

### `captures/PhoneDark.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| dark top bar: wordmark, budget, hairline | same | |
| stories row: dashed `Upload`, document circles with lavender rings, yellow-orange `Processing` | same | note: two processing instead of queued + processing (data state) |
| chips `Parsed` (selected, purple tint), `Failed`, `All` | same | |
| card header with green `Ready` badge and `…` | same | |
| summary box: dark tint, hairline, label, serif text and bullets | same | note: shorter stub summary, action row and `Page 1` preview show |
| bottom tab bar: home, plus-square, sun | same | |

### `captures/PhoneFailed.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| top bar: wordmark, budget, hairline | same | |
| stories row: dashed `Upload`, document circles with status | same | note: one processing document instead of queued + processing (data state) |
| chips: `Parsed`, `Failed` (selected, purple tint), `All` with counts | same | |
| failed card header: doc icon, name, meta, red `Failed` badge, `…` | same | |
| failed box: pink tint, red reason sentence, filled purple `Retry`, outlined `Reparse with another parser`, outlined `Delete forever` in red text, stacked | same | note: reason `The model provider refused this file.` instead of the max-deliveries sentence (another `error_code`) |
| hairline between cards | same | |
| too-large card header: grey `Too large` badge | same | |
| too-large box: grey tint, sentence `<limit reason>, so it can't be retried. Split ... then upload it again.`, outlined red-text `Delete forever` only | same | note: page-limit wording `1,001 pages is over the 1,000-page limit` instead of the size wording (data); too-large card is first (newest first) |
| bottom tab bar | same | |

### `captures/PhoneDelete.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| page behind, dimmed: top bar, stories row, chips with `Failed` selected, failed card with Retry / Reparse / Delete forever | same | note: too-large card above the failed card (data order) |
| bottom sheet: white, rounded top corners | same | |
| title `Delete <file> forever?` bold | same | note: fits one line (shorter name) |
| sentence `The PDF, its pages and its summary are removed for good. This can't be undone.` | same | |
| outlined `Cancel`, red filled `Delete forever`, right-aligned | same | |
