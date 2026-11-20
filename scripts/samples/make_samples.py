"""Build the two local samples: a scanned (image-only) PDF and a password-protected PDF.

    .venv/bin/python scripts/samples/make_samples.py <demo-password>

The scanned sample is pages 1-3 of the Constitution sample rendered to greyscale JPEG by
``pdftoppm`` (poppler-utils) and wrapped one image per page, so it holds no text layer. The
locked sample is ``w3c-dummy.pdf`` encrypted with AES-256 and the demo password given on the
command line; the README prints that password, so it protects nothing.
"""

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from pypdf import PdfReader, PdfWriter
from pypdf.generic import (
    ArrayObject,
    DecodedStreamObject,
    DictionaryObject,
    NameObject,
    NumberObject,
    StreamObject,
)

SAMPLES = Path(__file__).resolve().parents[2] / "samples"
SOURCE = SAMPLES / "constitution-of-the-united-states.pdf"
SCANNED = SAMPLES / "constitution-scanned-p1-3.pdf"
LOCKED = SAMPLES / "w3c-dummy-locked.pdf"
DPI = 110
POINTS_PER_INCH = 72
COLOR_SPACES = {1: "/DeviceGray", 3: "/DeviceRGB"}


def report(message: str) -> None:
    """One line on stdout."""
    sys.stdout.write(f"{message}\n")


def render_pages(folder: Path) -> list[Path]:
    """Pages 1-3 of the source as greyscale JPEGs."""
    pdftoppm = shutil.which("pdftoppm")
    if pdftoppm is None:
        message = "pdftoppm (poppler-utils) is needed to render the scanned sample"
        raise SystemExit(message)
    subprocess.run(  # noqa: S603 - fixed arguments, no user input
        [
            pdftoppm,
            "-f",
            "1",
            "-l",
            "3",
            "-r",
            str(DPI),
            "-gray",
            "-jpeg",
            "-jpegopt",
            "quality=70",
            str(SOURCE),
            str(folder / "page"),
        ],
        check=True,
    )
    return sorted(folder.glob("page-*.jpg"))


def jpeg_size(data: bytes) -> tuple[int, int, int]:
    """Width, height and colour components from the JPEG's SOF marker."""
    index = 2
    while index < len(data):
        marker, length = data[index + 1], int.from_bytes(data[index + 2 : index + 4])
        if marker in {0xC0, 0xC1, 0xC2}:
            height = int.from_bytes(data[index + 5 : index + 7])
            width = int.from_bytes(data[index + 7 : index + 9])
            return width, height, data[index + 9]
        index += 2 + length
    message = "no SOF marker in JPEG"
    raise ValueError(message)


def add_image_page(writer: PdfWriter, jpeg: bytes) -> None:
    """One page the size of the image, drawing only that image."""
    width, height, components = jpeg_size(jpeg)
    page_w, page_h = width * POINTS_PER_INCH / DPI, height * POINTS_PER_INCH / DPI
    page = writer.add_blank_page(page_w, page_h)

    image = StreamObject()
    image._data = jpeg
    image.update(
        {
            NameObject("/Type"): NameObject("/XObject"),
            NameObject("/Subtype"): NameObject("/Image"),
            NameObject("/Width"): NumberObject(width),
            NameObject("/Height"): NumberObject(height),
            NameObject("/ColorSpace"): NameObject(COLOR_SPACES[components]),
            NameObject("/BitsPerComponent"): NumberObject(8),
            NameObject("/Filter"): NameObject("/DCTDecode"),
        }
    )
    resources = DictionaryObject(
        {NameObject("/XObject"): DictionaryObject({NameObject("/Im0"): writer._add_object(image)})}
    )
    page[NameObject("/Resources")] = resources

    content = DecodedStreamObject()
    content.set_data(f"q {page_w:.2f} 0 0 {page_h:.2f} 0 0 cm /Im0 Do Q".encode())
    page[NameObject("/Contents")] = ArrayObject([writer._add_object(content)])


def make_scanned() -> None:
    """Image-only pages: PyPDF finds no text, Gemini and GPT-5 Mini read them."""
    writer = PdfWriter()
    with tempfile.TemporaryDirectory() as folder:
        for path in render_pages(Path(folder)):
            add_image_page(writer, path.read_bytes())
    with SCANNED.open("wb") as handle:
        writer.write(handle)
    report(f"wrote {SCANNED.name}: {len(PdfReader(SCANNED).pages)} pages")


def make_locked(password: str) -> None:
    """The W3C dummy, AES-256 encrypted with the demo password."""
    writer = PdfWriter(clone_from=SAMPLES / "w3c-dummy.pdf")
    writer.encrypt(user_password=password, owner_password=None, algorithm="AES-256")
    with LOCKED.open("wb") as handle:
        writer.write(handle)
    report(f"wrote {LOCKED.name}: encrypted={PdfReader(LOCKED).is_encrypted}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit(__doc__)
    make_scanned()
    make_locked(sys.argv[1])
