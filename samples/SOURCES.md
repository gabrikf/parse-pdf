# Sample PDFs

| File | Pages | Size | Source | License |
| --- | --- | --- | --- | --- |
| `constitution-of-the-united-states.pdf` | 85 | 4.0 MB | https://www.govinfo.gov/content/pkg/CDOC-110hdoc50/pdf/CDOC-110hdoc50.pdf (House Document 110-50, U.S. Government Publishing Office) | U.S. government work, public domain (17 U.S.C. 105) |
| `w3c-dummy.pdf` | 1 | 13 KB | https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf | W3C test file, W3C Document License |

Downloaded 2026-11-19. sha256:

- `constitution-of-the-united-states.pdf`: `7f29c4a79e310cc7bcee5f3fd07fb1367e463bd4530fa5d854ebdd4fd4402e57`
- `w3c-dummy.pdf`: `3df79d34abbca99308e79cb94461c1893582604d68329a41fd4bec1885e6adb4`

Generated locally by `scripts/samples/make_samples.py` (no download, same licenses as their sources):

| File | Pages | Built from | What it shows |
| --- | --- | --- | --- |
| `constitution-scanned-p1-3.pdf` | 3 | pages 1-3 of the Constitution sample, rendered to JPEG by `pdftoppm` at 110 dpi, one image per page | no text layer: PyPDF ends `no_text`, Gemini 3.1 Flash Lite and GPT-5 Mini read it |
| `w3c-dummy-locked.pdf` | 1 | `w3c-dummy.pdf`, AES-256 encrypted | the page asks for the password and re-sends only that file |

Demo password: `parse-pdf-demo` (public on purpose: it protects nothing).

Rebuild both with `.venv/bin/python scripts/samples/make_samples.py parse-pdf-demo`.
