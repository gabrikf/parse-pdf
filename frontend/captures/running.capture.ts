import path from 'node:path'

import { expect, test, type Page } from '@playwright/test'

import { card, chip, expectStatus, openApp, openUpload, pickFiles, upload } from '../e2e/support/app'
import { failOnceFile, pdfFile, sample, SAMPLE, tooLargeFile } from '../e2e/support/files'

const CAPTURES = path.resolve(import.meta.dirname, '../../.specs/features/document-processing/captures')
const PHONE = { width: 375, height: 812 }
const TABLET = { width: 768, height: 1024 }
const DESKTOP = { width: 1280, height: 1240 }

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

/** Two more files, so the stories row shows them queued and processing. */
async function withStories(page: Page) {
  await upload(page, [pdfFile('lecture-notes.pdf', sample(SAMPLE.dummy).buffer), pdfFile('annual-report.pdf', sample(SAMPLE.dummy).buffer)])
  await expect(page.getByRole('region', { name: 'In progress' })).toBeVisible()
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
      await withStories(page)
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
    await card(page, SAMPLE.constitution).getByRole('button', { name: 'View all 85 pages' }).click()
    await expect(page.getByRole('dialog', { name: SAMPLE.constitution }).getByRole('article').first()).toBeVisible()
    await save(page, 'PhonePages')
  })
})

test.describe('DesktopUpload', () => {
  test.use({ viewport: DESKTOP, colorScheme: 'light' })
  test('submit 3 files with 1 refused', async ({ page }) => {
    await openApp(page)
    const dialog = await openUpload(page)
    const notes = { name: 'meeting-notes.pdf', mimeType: 'application/pdf', buffer: Buffer.from('Plain notes, not a PDF.') }
    await pickFiles(dialog, [sample(SAMPLE.constitution), sample(SAMPLE.dummy), notes])
    await dialog.getByRole('button', { name: 'Upload 3 files' }).click()
    await expect(dialog.getByRole('button', { name: 'Done' })).toBeVisible()
    await save(page, 'DesktopUpload')
  })
})
