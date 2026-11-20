import path from 'node:path'

import { expect, test, type Page } from '@playwright/test'

import { card, chip, expectStatus, openApp, openUpload, pickFiles, upload } from '../e2e/support/app'
import { failOnceFile, pdfFile, sample, SAMPLE, tooLargeFile } from '../e2e/support/files'

const CAPTURES = path.resolve(import.meta.dirname, '../../.specs/features/document-processing/captures')
const PHONE = { width: 375, height: 812 }
const TABLET = { width: 768, height: 1024 }
const DESKTOP = { width: 1280, height: 1240 }
const GEMINI = 'gemini-3.1-flash-lite'

async function save(page: Page, frame: string) {
  await page.evaluate(() => document.fonts.ready)
  await page.screenshot({ path: path.join(CAPTURES, `${frame}.running.png`) })
}

/** The canvas feed: a long ready document, a scanned one with no text, a short ready one. */
async function seedFeed(page: Page) {
  await openApp(page)
  await upload(page, [sample(SAMPLE.dummy), sample(SAMPLE.scanned), sample(SAMPLE.constitution)])
  await expectStatus(page, SAMPLE.constitution, 'ready')
  await expectStatus(page, SAMPLE.scanned, 'no_text')
  await expectStatus(page, SAMPLE.dummy, 'ready')
}

/** Two more files, so the stories row shows them queued and processing (Gemini stays longer). */
async function withStories(page: Page, parser?: string) {
  const files = [pdfFile('lecture-notes.pdf', sample(SAMPLE.dummy).buffer), pdfFile('annual-report.pdf', sample(SAMPLE.dummy).buffer)]
  await upload(page, files, parser)
  await expect(page.getByRole('region', { name: 'In progress' })).toBeVisible()
  await page.evaluate(() => window.scrollTo({ top: 0 }))
}

/** Use up the session's uploads for this minute, then try one more from the page: the banner. */
async function rateLimited(page: Page) {
  for (let tries = 0; tries < 12; tries += 1) {
    const answer = await page.request.post('/api/v1/documents', {
      multipart: { parser: 'pypdf', files: { name: 'empty.pdf', mimeType: 'application/pdf', buffer: Buffer.alloc(0) } },
    })
    if (answer.status() === 429) break
  }
  const dialog = await openUpload(page)
  await pickFiles(dialog, [pdfFile('one-too-many.pdf', sample(SAMPLE.dummy).buffer)])
  await dialog.getByRole('button', { name: 'Upload 1 file' }).click()
  await dialog.getByRole('button', { name: 'Close' }).click()
  await expect(page.getByRole('status').filter({ hasText: 'Too many uploads in the last minute.' })).toBeVisible()
  await page.evaluate(() => window.scrollTo({ top: 0 }))
}

const FEED_FRAMES = [
  { frame: 'Main', viewport: DESKTOP, colorScheme: 'light' },
  { frame: 'PhoneLight', viewport: PHONE, colorScheme: 'light' },
  { frame: 'Tablet', viewport: TABLET, colorScheme: 'light' },
  { frame: 'DesktopDark', viewport: DESKTOP, colorScheme: 'dark' },
  { frame: 'PhoneDark', viewport: PHONE, colorScheme: 'dark' },
] as const

for (const { frame, viewport, colorScheme } of FEED_FRAMES) {
  test.describe(frame, () => {
    test.use({ viewport, colorScheme })
    test(`reach the parsed feed for ${frame}`, async ({ page }) => {
      await seedFeed(page)
      if (frame === 'Tablet') {
        await withStories(page, GEMINI)
        await rateLimited(page)
      } else {
        await withStories(page)
      }
      await save(page, frame)
    })
  })
}

test.describe('phone light frames', () => {
  test.use({ viewport: PHONE, colorScheme: 'light' })

  test('PhoneEmpty: reach the empty feed', async ({ page }) => {
    await openApp(page)
    await expect(page.getByRole('heading', { name: 'No documents yet' })).toBeVisible()
    await save(page, 'PhoneEmpty')
  })

  test('PhoneConfirm: open the reparse confirmation', async ({ page }) => {
    await seedFeed(page)
    await withStories(page, GEMINI)
    await card(page, SAMPLE.constitution).getByRole('button', { name: `Reparse ${SAMPLE.constitution}` }).click()
    await expect(page.getByRole('alertdialog')).toBeVisible()
    await save(page, 'PhoneConfirm')
  })

  test('PhoneFailed and PhoneDelete: the Failed chip, then delete forever', async ({ page }) => {
    await openApp(page)
    await upload(page, [failOnceFile('scan-0412.pdf'), tooLargeFile('archive-2019.pdf'), sample(SAMPLE.dummy)])
    await chip(page, 'Failed').click()
    await expectStatus(page, 'scan-0412.pdf', 'dead')
    await expectStatus(page, 'archive-2019.pdf', 'too_large')
    // The frames draw the stories row: two files in flight, not a race with the dummy's parse.
    await withStories(page, GEMINI)
    await save(page, 'PhoneFailed')

    await card(page, 'scan-0412.pdf').getByRole('button', { name: 'Delete forever' }).click()
    await expect(page.getByRole('alertdialog')).toBeVisible()
    await save(page, 'PhoneDelete')
  })
})

test.describe('PhonePages', () => {
  test.use({ viewport: PHONE, colorScheme: 'dark' })
  test('open the pages sheet of a ready document', async ({ page }) => {
    await seedFeed(page)
    const markdown = pdfFile('constitution-gemini.pdf', sample(SAMPLE.scanned).buffer)
    await upload(page, [markdown], GEMINI)
    await expectStatus(page, markdown.name, 'ready')
    await card(page, markdown.name).getByRole('button', { name: /^View all \d+ pages$/ }).click()
    await expect(page.getByRole('dialog', { name: markdown.name }).getByRole('heading').first()).toBeVisible()
    await save(page, 'PhonePages')
  })
})

test.describe('DesktopUpload', () => {
  test.use({ viewport: DESKTOP, colorScheme: 'light' })
  test('submit 4 files: 2 accepted, 1 refused, 1 locked', async ({ page }) => {
    await seedFeed(page)
    await page.evaluate(() => window.scrollTo({ top: 0 }))
    const dialog = await openUpload(page)
    const notes = { name: 'whiteboard-photo.pdf', mimeType: 'application/pdf', buffer: Buffer.from('A photo, not a PDF.') }
    const files = [pdfFile('constitution.pdf', sample(SAMPLE.constitution).buffer), pdfFile('federalist.pdf', sample(SAMPLE.dummy).buffer), notes, sample(SAMPLE.locked)]
    await pickFiles(dialog, files)
    await dialog.getByRole('button', { name: 'Upload 4 files' }).click()
    await expect(dialog.getByRole('button', { name: 'Unlock' })).toBeVisible()
    await expect(dialog.getByRole('button', { name: 'Done' })).toBeVisible()
    await save(page, 'DesktopUpload')
  })
})
