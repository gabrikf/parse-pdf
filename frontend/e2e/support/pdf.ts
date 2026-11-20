/** Small, valid PDFs built in memory, the same way as `backend/tests/pdf_factory.py`. */

function escape(text: string): string {
  return text.replaceAll('\\', '\\\\').replaceAll('(', '\\(').replaceAll(')', '\\)')
}

function serialize(objects: string[]): Buffer {
  let out = '%PDF-1.4\n'
  const offsets: number[] = []
  objects.forEach((body, index) => {
    offsets.push(Buffer.byteLength(out, 'latin1'))
    out += `${index + 1} 0 obj\n${body}\nendobj\n`
  })
  const xref = Buffer.byteLength(out, 'latin1')
  out += `xref\n0 ${objects.length + 1}\n0000000000 65535 f \n`
  out += offsets.map((offset) => `${String(offset).padStart(10, '0')} 00000 n \n`).join('')
  out += `trailer\n<< /Size ${objects.length + 1} /Root 1 0 R >>\nstartxref\n${xref}\n%%EOF\n`
  return Buffer.from(out, 'latin1')
}

/** One page per string; an empty string makes a blank page. */
export function makePdf(pages: string[]): Buffer {
  const pageIds = pages.map((_, index) => 4 + 2 * index)
  const kids = pageIds.map((id) => `${id} 0 R`).join(' ')
  const objects = [
    '<< /Type /Catalog /Pages 2 0 R >>',
    `<< /Type /Pages /Kids [${kids}] /Count ${pages.length} >>`,
    '<< /Type /Font /Subtype /Type1 /BaseFont /Helvetica >>',
  ]
  pages.forEach((text, index) => {
    const content = text ? `BT /F1 12 Tf 72 720 Td (${escape(text)}) Tj ET` : ''
    objects.push(
      `<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] /Resources << /Font << /F1 3 0 R >> >> /Contents ${(pageIds[index] ?? 0) + 1} 0 R >>`,
      `<< /Length ${content.length} >>\nstream\n${content}\nendstream`,
    )
  })
  return serialize(objects)
}

/** `count` pages reading "<prefix> <n>". */
export function textPdf(count: number, prefix = 'Page'): Buffer {
  return makePdf(Array.from({ length: count }, (_, index) => `${prefix} ${index + 1}`))
}
