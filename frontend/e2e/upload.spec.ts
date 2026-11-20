import { expect, test, type Page } from '@playwright/test'

import { card, chip, expectStatus, openApp, openUpload, pickFiles, shot, upload, uploadAndWait } from './support/app'
import { lockedSamplePassword, pdfFile, sample, SAMPLE, type FilePayload } from './support/files'

const BYTES = /^\d+ [KM]?B$/

/** Build a `File` inside the page, from bytes sent over as base64. */
async function inPageTransfer(page: Page, file: FilePayload) {
  return page.evaluateHandle(
    ({ name, data }) => {
      const transfer = new DataTransfer()
      const bytes = Uint8Array.from(atob(data), (char) => char.charCodeAt(0))
      transfer.items.add(new File([bytes], name, { type: 'application/pdf' }))
      return transfer
    },
    { name: file.name, data: file.buffer.toString('base64') },
  )
}

test('first visit creates a session and shows the empty feed', async ({ page, context }, info) => {
  await openApp(page)

  const cookie = (await context.cookies()).find((item) => item.name === 'pp_session')
  expect(cookie?.httpOnly).toBe(true)
  await expect(page.getByRole('heading', { name: 'No documents yet' })).toBeVisible()
  await expect(page.getByRole('main').getByRole('button', { name: 'Upload PDFs' })).toBeVisible()

  await page.reload()
  const again = (await context.cookies()).find((item) => item.name === 'pp_session')
  expect(again?.value).toBe(cookie?.value)
  await shot(page, info, 'first-visit')

  // Newest first: the second upload's card comes before the first's.
  const first = pdfFile('older.pdf', sample(SAMPLE.dummy).buffer)
  const second = pdfFile('newer.pdf', sample(SAMPLE.dummy).buffer)
  await uploadAndWait(page, first)
  await uploadAndWait(page, second)
  const names = await page.getByRole('main').getByRole('article').evaluateAll((items) => items.map((item) => item.getAttribute('aria-label')))
  expect(names).toEqual([second.name, first.name])
})

test('the parser select offers exactly three parsers with pypdf selected', async ({ page }, info) => {
  await openApp(page)
  const dialog = await openUpload(page)
  const select = dialog.getByLabel('Parser')

  await expect(select).toHaveValue('pypdf')
  await expect(select.locator('option')).toHaveText(['PyPDF · plain text', 'Gemini 3.1 Flash Lite · markdown', 'GPT-5 Mini · OCR'])
  const values = await select.locator('option').evaluateAll((options) => options.map((option) => (option as HTMLOptionElement).value))
  expect(values).toEqual(['pypdf', 'gemini-3.1-flash-lite', 'gpt-5-mini'])
  await shot(page, info, 'parser-select')
})

test('files added by picker, drop and paste are listed with name and size', async ({ page }, info) => {
  await openApp(page)
  const dialog = await openUpload(page)

  await pickFiles(dialog, [sample(SAMPLE.dummy)])
  const dropped = await inPageTransfer(page, pdfFile('dropped.pdf', sample(SAMPLE.dummy).buffer))
  await dialog.getByTestId('drop-zone').dispatchEvent('drop', { dataTransfer: dropped })
  const pasted = await inPageTransfer(page, pdfFile('pasted.pdf', sample(SAMPLE.dummy).buffer))
  await page.evaluate((transfer) => window.dispatchEvent(new ClipboardEvent('paste', { clipboardData: transfer })), pasted)

  const rows = dialog.locator('li[data-file]')
  await expect(rows).toHaveCount(3)
  for (const name of [SAMPLE.dummy, 'dropped.pdf', 'pasted.pdf']) {
    const row = dialog.locator(`li[data-file="${name}"]`)
    await expect(row).toContainText(name)
    await expect(row.locator('span').filter({ hasText: BYTES })).toHaveText('13 KB')
  }
  await expect(dialog.getByRole('status')).toHaveText('3 selected')
  await shot(page, info, 'picker-drop-paste')
})

test('a 21st file shows up to 20 files per upload', async ({ page }, info) => {
  await openApp(page)
  const dialog = await openUpload(page)
  const files = Array.from({ length: 21 }, (_, index) => pdfFile(`copy-${index + 1}.pdf`, sample(SAMPLE.dummy).buffer))

  await pickFiles(dialog, files)

  await expect(dialog.getByRole('alert')).toHaveText('Up to 20 files per upload')
  await expect(dialog.locator('li[data-file]')).toHaveCount(20)
  await expect(dialog.locator('li[data-file="copy-21.pdf"]')).toHaveCount(0)
  await shot(page, info, 'twenty-one-files')
})

test('upload 3 samples by picker reaches the parsed feed', async ({ page }, info) => {
  await openApp(page)
  const files = [sample(SAMPLE.dummy), sample(SAMPLE.constitution), sample(SAMPLE.scanned)]

  await upload(page, files)
  await expect(page.getByRole('region', { name: 'In progress' })).toBeVisible()
  await shot(page, info, 'three-samples-in-progress')

  await expectStatus(page, SAMPLE.dummy, 'ready')
  await expectStatus(page, SAMPLE.constitution, 'ready')
  await expectStatus(page, SAMPLE.scanned, 'no_text')
  const stories = page.getByRole('region', { name: 'In progress' })
  await expect(stories.getByRole('button', { name: 'Upload' })).toBeVisible()
  await expect(stories.getByRole('button', { name: /, (queued|processing)$/ })).toHaveCount(0)
  await expect(chip(page, 'Parsed')).toHaveAttribute('aria-pressed', 'true')
  await expect(card(page, SAMPLE.constitution)).toContainText('85 pages')
  await shot(page, info, 'three-samples-parsed')
})

test('refused files show their reason inline', async ({ page }, info) => {
  await openApp(page)
  const dialog = await openUpload(page)
  const files = [
    pdfFile('empty.pdf', Buffer.alloc(0)),
    { name: 'notes.pdf', mimeType: 'application/pdf', buffer: Buffer.from('These are notes, not a PDF.') },
    sample(SAMPLE.dummy),
  ]

  await pickFiles(dialog, files)
  await dialog.getByRole('button', { name: 'Upload 3 files' }).click()

  await expect(dialog.locator('li[data-file="empty.pdf"]')).toContainText('This file is empty. Pick the PDF again.')
  await expect(dialog.locator('li[data-file="notes.pdf"]')).toContainText("This file isn't a PDF. Export it as a PDF and add it again.")
  await expect(dialog.locator(`li[data-file="${SAMPLE.dummy}"]`)).toHaveAttribute('data-state', 'accepted')
  await expect(dialog.getByRole('status').first()).toHaveText('1 of 3 files uploaded')
  await shot(page, info, 'refused-files')
})

test('a locked file asks for its password and re-sends only that file', async ({ page }, info) => {
  await openApp(page)
  let uploads = 0
  page.on('request', (request) => {
    if (request.method() === 'POST' && request.url().endsWith('/api/v1/documents')) uploads += 1
  })
  const dialog = await openUpload(page)
  await pickFiles(dialog, [sample(SAMPLE.locked), sample(SAMPLE.dummy)])
  await dialog.getByRole('button', { name: 'Upload 2 files' }).click()

  const row = dialog.locator(`li[data-file="${SAMPLE.locked}"]`)
  const field = row.getByLabel(/needs a password/)
  await expect(field).toBeVisible()
  await field.fill('not-the-password')
  await row.getByRole('button', { name: 'Unlock' }).click()
  await expect(row.getByLabel(/didn't unlock/)).toBeVisible()
  await shot(page, info, 'locked-file-wrong-password')

  await row.getByLabel(/didn't unlock/).fill(lockedSamplePassword())
  await row.getByRole('button', { name: 'Unlock' }).click()
  await expect(row).toHaveAttribute('data-state', 'accepted')

  expect(uploads).toBe(3)
  await dialog.getByRole('button', { name: 'Done' }).click()
  await expectStatus(page, SAMPLE.locked, 'ready')
  await expectStatus(page, SAMPLE.dummy, 'ready')
  // Only the locked file was sent again: the session holds one document per file, not three.
  await chip(page, 'All').click()
  await expect(chip(page, 'All')).toHaveText('All 2')
  await expect(page.getByRole('article')).toHaveCount(2)
})
