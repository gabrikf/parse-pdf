import { expect, test } from '@playwright/test'

import { card, expectStatus, openApp, shot, uploadAndWait } from './support/app'
import { pagesFile, sample, SAMPLE } from './support/files'

test('the pages sheet shows 50 pages and loads the next 50', async ({ page }, info) => {
  await openApp(page)
  const ready = await uploadAndWait(page, pagesFile('long-120.pdf', 120))

  await ready.getByRole('button', { name: 'View all 120 pages' }).click()
  const sheet = page.getByRole('dialog', { name: 'long-120.pdf' })
  await expect(sheet).toContainText('120 pages · text · PyPDF')
  const pages = sheet.getByRole('article', { name: /^Page \d+$/ })
  await expect(pages).toHaveCount(50)
  await expect(sheet.getByRole('status')).toHaveText('Showing 50 of 120 pages')
  await expect(sheet.getByRole('article', { name: 'Page 50' })).toContainText('Page 50')
  await shot(page, info, 'pages-sheet')

  await sheet.getByRole('button', { name: 'Load the next 50 pages' }).click()
  await expect(pages).toHaveCount(100)
  await expect(sheet.getByRole('status')).toHaveText('Showing 100 of 120 pages')
  await sheet.getByRole('button', { name: 'Load the next 50 pages' }).click()
  await expect(pages).toHaveCount(120)
  await expect(sheet.getByRole('button', { name: 'Load the next 50 pages' })).toHaveCount(0)
})

test('a no_text card shows its hint and reparses with gemini', async ({ page }, info) => {
  await openApp(page)
  const scanned = await uploadAndWait(page, sample(SAMPLE.scanned), 'no_text')

  await expect(scanned).toContainText('No text found on any page.')
  await expect(scanned).toContainText('Try the gemini-3.1-flash-lite parser, which reads scans.')
  await shot(page, info, 'no-text-card')

  await scanned.getByRole('button', { name: 'Reparse with Gemini' }).click()
  const confirm = page.getByRole('alertdialog', { name: `Reparse ${SAMPLE.scanned}?` })
  await expect(confirm.getByRole('radio', { name: /Gemini 3.1 Flash Lite/ })).toBeChecked()
  const sent = page.waitForRequest((request) => request.url().endsWith('/reparse'))
  await confirm.getByRole('button', { name: 'Reparse' }).click()
  expect((await sent).postDataJSON()).toEqual({ parser: 'gemini-3.1-flash-lite' })

  const reparsed = await expectStatus(page, SAMPLE.scanned, 'ready')
  await expect(reparsed).toContainText('Gemini 3.1 Flash Lite · 3 pages')
})

test('copy summary copies the markdown and shows copied', async ({ page }, info) => {
  await openApp(page)
  const ready = await uploadAndWait(page, sample(SAMPLE.dummy))

  await ready.getByRole('button', { name: `Copy summary of ${SAMPLE.dummy}` }).click()
  await expect(ready.getByRole('status')).toHaveText('Copied')
  const copied = await page.evaluate(() => navigator.clipboard.readText())
  expect(copied).toContain('### Key points')
  expect(copied).toContain('- Rendered as markdown')
  await shot(page, info, 'copy-summary')

  await expect(card(page, SAMPLE.dummy).getByRole('status')).toHaveText('', { timeout: 4_000 })
})
