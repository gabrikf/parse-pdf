# Document processing screens

**Verifier**: independent sub-agent (author != verifier)
**Round**: 2 (of the AD-052 review; round 1 at da2480d; earlier: AD-050 review round 1 at b041b7b and round 2 at ebd58a3; AD-049 review round 1 at 932cbba and round 2 at 68cfd98; first review round 1 at 19cf1ff and round 2 at 28a6e1c)
**HEAD**: 2243668

Round 1 judged the 11 pictures re-saved at da2480d. It re-judged every row of every picture and
copied no earlier verdict; nine pictures diverged on one row each: the glyph inside the document
circles of the stories row (the capture draws a page with two equal lines, about 18x22 px; the
pictures drew a smaller page with a short line over two lines, the card-header glyph). Round 2
judges the pictures re-saved at 2243668. It reopened the nine `differs` rows: the circles now draw
a page with two equal lines, 18x22 px, the same glyph as the capture pixel for pixel at 4x zoom in
every frame (light, dark, under the scrim and dimmed), so each is now `same`. It looked at every
`same` row of all 11 re-saved pictures for a visible regression and found none. Nothing else was
added or re-judged; the only other changes are notes whose test data (budget numbers, counts, the
circles in the stories row) now read as in the re-saved pictures. The re-saved pictures are in the
working tree, not committed at 2243668.

The pictures use the e2e stack's test data (local OpenRouter stub). File names, sizes, page counts,
times, chip counts, budget numbers, the stub summary text (including its `Key points` heading), the
error reason for each `error_code`, feed order, the parser each document used and the number and
kind of circles in the stories row (two processing instead of one queued and one
processing) all differ from the canvas sample data. They are recorded as notes
on `same` rows. One item from `## Differences from the source` applies: the two loose text labels on
DesktopDark are not UI (AD-025).

All 11 pictures are at their frame's size: phone 375x812, tablet 768x1024, desktop 1280x1240.
Their text reads at the capture's size, so no picture is resized. Other icons were compared glyph by
glyph at 3-6x zoom (rail and tab bar icons, rail logo, cloud upload, close, check, warning triangle,
padlock, action row icons, `…`, sun and moon); they match, apart from the cloud upload glyph being a
little smaller (size).

| Screen | Compared with | Verdict | Finding |
| --- | --- | --- | --- |
| `captures/PhoneEmpty.running.png` | `captures/PhoneEmpty.png` | matches | 0 rows differ; no regression |
| `captures/DesktopUpload.running.png` | `captures/DesktopUpload.png` | matches | round 1's story-circle glyph row is now same; no regression |
| `captures/PhonePages.running.png` | `captures/PhonePages.png` | matches | 0 rows differ; no regression; the markdown subheading cannot be judged (the stub pages have none) |
| `captures/PhoneConfirm.running.png` | `captures/PhoneConfirm.png` | matches | round 1's story-circle glyph row is now same; no regression |
| `captures/Main.running.png` | `captures/Main.png` | matches | round 1's story-circle glyph row is now same; no regression |
| `captures/PhoneLight.running.png` | `captures/PhoneLight.png` | matches | round 1's story-circle glyph row is now same; no regression |
| `captures/Tablet.running.png` | `captures/Tablet.png` | matches | round 1's story-circle glyph row is now same; no regression |
| `captures/DesktopDark.running.png` | `captures/DesktopDark.png` | matches | round 1's story-circle glyph row is now same; no regression |
| `captures/PhoneDark.running.png` | `captures/PhoneDark.png` | matches | round 1's story-circle glyph row is now same; no regression |
| `captures/PhoneFailed.running.png` | `captures/PhoneFailed.png` | matches | round 1's story-circle glyph row is now same; no regression; the size-limit wording of the too-large box cannot be judged (the picture shows the page limit) |
| `captures/PhoneDelete.running.png` | `captures/PhoneDelete.png` | matches | round 1's story-circle glyph row is now same; no regression |

### `captures/PhoneEmpty.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| top bar: wordmark `Parse PDF` left (serif italic, `PDF` purple), hairline under the bar | same | |
| top bar right: budget `<n> of 3,000` (mono) over `model pages today` | same | note: 20 instead of 1,240 (data) |
| no stories row, no filter chips | same | |
| empty state, centered: outline circle holding a purple cloud-upload icon | same | note: the cloud glyph is a little smaller inside the circle (size) |
| heading `No documents yet` (serif) | same | |
| sentence `Upload a PDF to read it page by page, with a short summary at the top.` on two lines | same | |
| filled purple button `Upload PDFs` | same | |
| small grey sentence `Files stay private to this browser and are deleted after 7 days.` on two lines | same | |
| bottom tab bar with a hairline above it: home, plus-square and moon icons | same | |

### `captures/DesktopUpload.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| left rail: wordmark; `Feed` selected (tinted block), `Upload`, `Dark mode`, each with an outline icon; hairline right edge | same | |
| right rail: `Parsers` guide (PyPDF, Gemini 3.1 Flash Lite and GPT-5 Mini, each with its lines; `Every summary is written by Gemini 3.1 Flash Lite.`), hairline, `Model pages today` (big serif number, `of 3,000`, purple meter, `Resets at 00:00 UTC. PyPDF parsing doesn't count.`), hairline, privacy line | same | note: 41 instead of 1,240, so the meter has a sliver of fill (data) |
| backdrop: grey scrim over the whole page | same | |
| backdrop: stories row (dashed `Upload` circle with plus, two document circles) and the `Parsed` chip under the scrim | same | note: both document rings are solid purple (two processing) where the capture has one dashed queued ring (data state) |
| backdrop: glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| backdrop: feed under the scrim: ready card (summary box, action icons, `Page 1` preview, `View all <n> pages`), no-text card (`Reparse with Gemini`, `Delete`), next ready card | same | note: stub summary with a `Key points` heading; no-text card `constitution-scanned-p1-3.pdf`, next card `w3c-dummy.pdf` (data) |
| dialog: white, rounded, centered over the feed; header `Upload PDFs`, close `×` on the right, hairline under the header | same | note: the dialog ends about 20 px higher because its rows are tighter (spacing) |
| drop zone: dashed border, tinted fill, purple cloud-upload icon, `Drop PDFs here, or paste them`, `Up to 20 files, 50 MB each`, outlined `Choose files` | same | note: the cloud icon is a little smaller and the zone a little shorter (spacing) |
| `Parser` label with a native select under it | same | note: the select shows `PyPDF · plain text` instead of `Gemini 3.1 Flash Lite · markdown` (the user's pick) |
| list heading `<n> of <m> files uploaded` | same | note: `2 of 4` |
| accepted rows: green check, file name, mono size on the right, hairline between rows | same | note: `constitution.pdf` 3.8 MB and `federalist.pdf` 13 KB (data); rows a little tighter (spacing) |
| rejected row: red warning triangle, name, size, red reason `This file isn't a PDF. Export it as a PDF and add it again.` | same | note: 19 B (data) |
| password row icon: orange outline padlock left of the name | same | |
| password row text: name, size, orange `This PDF needs a password. It is used once to unlock the file and never stored.` on two lines | same | note: `w3c-dummy-locked.pdf`, 14 KB (data) |
| password row field: `Password` input with a filled purple `Unlock` button on its right | same | note: `Unlock` is a little wider and the input a little shorter (spacing) |
| footer with a hairline above it: outlined `Add more files` and filled purple `Done`, right-aligned | same | |

### `captures/PhonePages.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| page behind: top bar with wordmark and budget, dimmed under a dark scrim | same | note: 39 (data) |
| sheet: dark, rounded top corners, from just under the top bar to the bottom of the window | same | starts at about y 52, as the capture does |
| sheet header: bold file name (cut with an ellipsis when long), close `×` on the right | same | note: `constitution-gemini.pdf` fits, so there is no ellipsis (shorter name); the `×` is a brighter white and a little heavier (shade, weight) |
| sheet header subline `<n> pages · <format> · <parser>` | same | note: `3 pages · markdown · Gemini 3.1 Flash Lite` |
| hairline under the header | same | |
| `Page 1`: small grey label above the page body | same | |
| page body drawn as markdown: serif heading, bold italic subheading, serif paragraphs | same | serif heading `Page 1` and serif paragraph `Stub markdown for page 1.`. Note: the stub's markdown has no subheading, so the bold italic subheading cannot be judged from this picture |
| hairline between pages, then the `Page 2` label and its body | same | note: pages 2 and 3 are both in view, each with a hairline above it |
| end of the list | same | note: a centered grey `Showing 3 of 3 pages` under the last hairline. The capture's 18-page list runs past the window, so the capture does not draw its end (another state) |

### `captures/PhoneConfirm.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| page behind, dimmed: top bar with wordmark and budget | same | note: 26 (data) |
| page behind: stories row (dashed `Upload` circle, document circles with name and status), hairline | same | note: two processing circles instead of queued + processing (data state) |
| page behind: glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| page behind: chips `Parsed` (selected, purple tint), `Failed`, `All` with counts | same | note: 3 / 0 / 5 (data) |
| page behind: card header (doc icon, name cut with an ellipsis, meta, green `Ready` badge, `…`) and the top of the summary box | same | |
| bottom sheet: white, rounded top corners, full width | same | note: starts higher because the title takes two lines |
| title `Reparse <file>?` in bold | same | note: wraps to two lines (longer name) |
| sentence `Its pages and summary are cleared, then it runs again with the parser you pick.` | same | |
| `Parser` label, then three bordered radio rows: `PyPDF · plain text`, `Gemini 3.1 Flash Lite · markdown`, `GPT-5 Mini · OCR`; the selected row has a purple border and tint | same | note: PyPDF is selected instead of GPT-5 Mini (the document's current parser). The parser names are a heavier weight and the `Parser` label a lighter one (type weight); rows a little shorter (spacing) |
| outlined `Cancel` and filled purple `Reparse`, right-aligned | same | |

### `captures/Main.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| left rail: wordmark; `Feed` selected, `Upload`, `Dark mode`; hairline right edge | same | |
| center column: stories row (dashed `Upload` circle with plus, document circles with name and status under each) | same | note: two processing circles (solid purple, orange `Processing`) instead of one queued (dashed grey, `Queued`) and one processing (data state) |
| glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| hairline under the stories row | same | |
| chips `Parsed 3` (selected, purple border and tint), `Failed`, `All` with counts | same | note: 3 / 0 / 5 (data) |
| ready card header: round doc icon, bold name, meta `<parser> · <n> pages · <time>`, green `Ready` badge, `…` | same | note: `PyPDF · 85 pages · just now` (data) |
| summary box: tinted, hairline border, `Summary · Gemini 3.1 Flash Lite` label, serif overview, serif bullets | same | note: the stub summary has a small grey `Key points` heading between the overview and the bullets (data) |
| action row: book, refresh and copy icons on the left, trash on the right | same | |
| page preview: bold `Page 1` followed by serif text cut with an ellipsis on the second line, then the `View all <n> pages` link | same | note: the PyPDF text of the sample (data) |
| hairline between cards | same | |
| no-text card header: doc icon, name, meta, grey `No text` badge, `…` | same | |
| no-text box: bold `No text found on any page.` then `This usually means a scanned PDF or a photo of a page. Gemini 3.1 Flash Lite reads scanned pages.` | same | |
| no-text box buttons: filled purple `Reparse with Gemini`, outlined `Delete` | same | note: both buttons a little wider (spacing) |
| next ready card header and summary box at the bottom, cut by the window | same | |
| right rail: parser guide, hairline, model pages meter, hairline, privacy line | same | note: 2 instead of 1,240, so the meter shows no visible fill (data) |

### `captures/PhoneLight.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| top bar: wordmark left, budget right, hairline | same | note: 6 (data) |
| stories row: `Upload` dashed circle, document circles with name and status | same | note: two processing instead of queued + processing (data state) |
| glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| hairline under the stories row | same | |
| chips `Parsed` (selected, purple tint), `Failed`, `All` with counts | same | note: 3 / 0 / 5 (data) |
| card header: doc icon, name cut with an ellipsis, meta line, green `Ready` badge, `…` | same | note: the meta `PyPDF · 85 pages · just now` fits, so it is not cut (data) |
| summary box: tinted, hairline, label, serif overview, serif bullets | same | note: the stub summary is shorter and has a `Key points` heading, so the box ends above the tab bar and the action row and the start of the `Page 1` preview show (data) |
| bottom tab bar with a hairline above it: home, plus-square, moon | same | |

### `captures/Tablet.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| narrow left icon rail: purple doc logo, home (selected tint), plus-square, moon; hairline right edge | same | |
| rate-limit banner at the top of the column: warning triangle, `Too many uploads in the last minute. You can upload again in <n> s.` in orange on an orange tint, rounded | same | note: `23 s` instead of `42 s` (the wait from `Retry-After`) |
| stories row: `Upload` dashed circle, document circles with name and status | same | note: two processing instead of queued + processing (data state) |
| glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| hairline, then chips `Parsed` (selected), `Failed`, `All` with counts | same | note: 3 / 0 / 5 (data) |
| ready card: header, summary box, action row (book, refresh and copy; trash on the right), `Page 1` preview cut with an ellipsis, `View all <n> pages` | same | note: stub summary with a `Key points` heading (data) |
| hairline between cards | same | |
| no-text card: grey `No text` badge; bold `No text found on any page.` then `This usually means a scanned PDF or a photo of a page. Gemini 3.1 Flash Lite reads scanned pages.` | same | |
| no-text buttons: filled purple `Reparse with Gemini`, outlined `Delete` | same | note: the shorter card above lets the whole box show (data) |
| no right rail and no bottom tab bar at 768 px | same | |

### `captures/DesktopDark.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| dark theme throughout: near-black background, hairline borders, lavender primary | same | |
| left rail: wordmark (`PDF` lavender); `Feed` selected, `Upload`, `Light mode` with a sun icon | same | |
| loose labels `scripts/phase.sh implement` and `annual-report` over the summary | same | left out per `## Differences from the source` (AD-025) |
| stories row (dashed `Upload`, document circles with lavender rings, yellow `Processing`) and hairline | same | note: two processing instead of queued + processing (data state) |
| glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| chips `Parsed` (selected, lavender border and purple tint), `Failed`, `All` | same | note: 3 / 0 / 5 (data) |
| ready card: header with green `Ready` badge, dark summary box, action icons, `Page 1` preview, `View all <n> pages` link | same | note: stub summary with a `Key points` heading (data) |
| no-text card: `No text` badge; bold `No text found on any page.` then `This usually means a scanned PDF or a photo of a page. Gemini 3.1 Flash Lite reads scanned pages.` | same | |
| no-text buttons: lavender filled `Reparse with Gemini` with dark text, outlined `Delete` | same | |
| next ready card, cut by the window | same | |
| right rail: parser guide, model pages meter with lavender fill, privacy line | same | note: 16, so the fill is a sliver (data) |

### `captures/PhoneDark.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| dark top bar: wordmark (`PDF` lavender), budget, hairline | same | note: 20 (data) |
| stories row: dashed `Upload`, document circles with lavender rings, yellow `Processing` | same | note: two processing instead of queued + processing (data state) |
| glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| chips `Parsed` (selected, purple tint), `Failed`, `All` | same | note: 3 / 0 / 5 (data) |
| card header: doc icon, name cut with an ellipsis, meta, green `Ready` badge, `…` | same | |
| summary box: dark tint, hairline, label, serif text and bullets | same | note: the stub summary is shorter, so the action row and the start of the `Page 1` preview show (data) |
| bottom tab bar: home, plus-square, sun | same | |

### `captures/PhoneFailed.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| top bar: wordmark, budget, hairline | same | note: 31 (data) |
| stories row under the top bar: dashed `Upload` circle with plus, document circles with name and status, hairline under it | same | note: `annual-rep…` and `lecture-no…`, both solid purple with orange `Processing`, instead of one queued and one processing (data state) |
| glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| chips: `Parsed`, `Failed` (selected, purple tint), `All` with counts | same | note: 1 / 2 / 5 (data) |
| failed card header: doc icon, name, meta, red `Failed` badge, `…` | same | note: the failed card is second; the too-large card is first (newest first, data order) |
| failed box: pink tint; red reason sentence; then, stacked, filled purple `Retry`, outlined `Reparse with another parser`, outlined `Delete forever` in red text | same | note: reason `The model provider refused this file.` instead of the max-deliveries sentence (another `error_code`); the box runs under the tab bar, as the capture's too-large box does |
| hairline between cards | same | |
| too-large card header: doc icon, name, meta cut with an ellipsis, grey `Too large` badge, `…` | same | |
| too-large box: grey tint; sentence `<limit reason>, so it can't be retried. ... then upload it again.`; outlined `Delete forever` in red text only | same | note: page-limit wording `1,001 pages is over the 1,000-page limit, so it can't be retried. Split the PDF, then upload it again.` The capture draws the size limit (`... Split or compress the PDF, then upload it again.`), which this picture does not show, so that wording cannot be judged here |
| bottom tab bar | same | |

### `captures/PhoneDelete.running.png`

| Element | Result | Picture draws |
| --- | --- | --- |
| page behind, dimmed: top bar | same | note: 31 (data) |
| page behind, dimmed: stories row (dashed `Upload` circle, document circles) and hairline | same | note: two processing circles instead of one queued and one processing (data state) |
| page behind, dimmed: glyph inside each document circle | same | round 2: a page with two equal lines, 18x22 px, as the capture draws it. Round 1: differs, a smaller page (16x20 px) with a short line over two lines, the card-header glyph |
| page behind, dimmed: chips with `Failed` selected, failed card with `Retry`, `Reparse with another parser` and `Delete forever` | same | note: the too-large card sits above the failed card (data order), so the failed card's buttons are under the sheet; only the reason and the top edge of `Retry` show |
| bottom sheet: white, rounded top corners, full width | same | |
| title `Delete <file> forever?` in bold | same | note: fits on one line (shorter name) |
| sentence `The PDF, its pages and its summary are removed for good. This can't be undone.` | same | |
| outlined `Cancel` and red filled `Delete forever`, right-aligned | same | |
