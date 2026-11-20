"""Build small, valid PDFs in memory for tests: text pages, blank pages, encryption."""

import io

from pypdf import PdfReader, PdfWriter


def _escape(text: str) -> str:
    return text.replace("\\", "\\\\").replace("(", "\\(").replace(")", "\\)")


def make_pdf(pages: list[str]) -> bytes:
    """A PDF with one page per string; an empty string makes a blank page."""
    objects: list[bytes] = []
    page_ids = [4 + 2 * index for index in range(len(pages))]
    kids = " ".join(f"{pid} 0 R" for pid in page_ids)

    objects.append(b"<< /Type /Catalog /Pages 2 0 R >>")
    objects.append(f"<< /Type /Pages /Kids [{kids}] /Count {len(pages)} >>".encode())
    objects.append(b"<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>")
    for index, text in enumerate(pages):
        content = f"BT /F1 12 Tf 72 720 Td ({_escape(text)}) Tj ET".encode() if text else b""
        contents_ref = f"{page_ids[index] + 1} 0 R"
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /Font << /F1 3 0 R >> >> /Contents {contents_ref} >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(content) + content + b"\nendstream")

    return _serialize(objects)


def _serialize(objects: list[bytes]) -> bytes:
    out = io.BytesIO()
    out.write(b"%PDF-1.4\n")
    offsets = []
    for number, body in enumerate(objects, 1):
        offsets.append(out.tell())
        out.write(f"{number} 0 obj\n".encode() + body + b"\nendobj\n")
    xref = out.tell()
    out.write(f"xref\n0 {len(objects) + 1}\n0000000000 65535 f \n".encode())
    for offset in offsets:
        out.write(f"{offset:010d} 00000 n \n".encode())
    out.write(f"trailer\n<< /Size {len(objects) + 1} /Root 1 0 R >>\n".encode())
    out.write(f"startxref\n{xref}\n%%EOF\n".encode())
    return out.getvalue()


def make_image_pdf(page_count: int = 1) -> bytes:
    """A scanned-style PDF: each page draws one grey image and holds no text at all."""
    objects: list[bytes] = [b"<< /Type /Catalog /Pages 2 0 R >>", b""]
    image = b"\x80" * 64
    objects.append(
        b"<< /Type /XObject /Subtype /Image /Width 8 /Height 8 /ColorSpace /DeviceGray "
        b"/BitsPerComponent 8 /Length %d >>\nstream\n" % len(image) + image + b"\nendstream"
    )
    kids = []
    for _ in range(page_count):
        draw = b"q 540 0 0 720 36 36 cm /Im1 Do Q"
        page_id = len(objects) + 1
        kids.append(f"{page_id} 0 R")
        objects.append(
            f"<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] "
            f"/Resources << /XObject << /Im1 3 0 R >> >> /Contents {page_id + 1} 0 R >>".encode()
        )
        objects.append(b"<< /Length %d >>\nstream\n" % len(draw) + draw + b"\nendstream")
    objects[1] = f"<< /Type /Pages /Kids [{' '.join(kids)}] /Count {page_count} >>".encode()
    return _serialize(objects)


def make_text_pdf(page_count: int, prefix: str = "Page") -> bytes:
    """``page_count`` pages reading ``"<prefix> <n>"``."""
    return make_pdf([f"{prefix} {number}" for number in range(1, page_count + 1)])


def encrypt(pdf: bytes, user_password: str, owner_password: str = "owner-secret") -> bytes:
    """The same PDF, AES-256 encrypted."""
    writer = PdfWriter(clone_from=PdfReader(io.BytesIO(pdf)))
    writer.encrypt(user_password=user_password, owner_password=owner_password, algorithm="AES-256")
    buffer = io.BytesIO()
    writer.write(buffer)
    return buffer.getvalue()


PNG_BYTES = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64
