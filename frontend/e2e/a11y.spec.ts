import AxeBuilder from '@axe-core/playwright'
import { expect, test, type Page } from '@playwright/test'

import { card, chip, expectStatus, openApp, openUpload, pickFiles, shot, upload, uploadAndWait } from './support/app'
import { pagesFile, pdfFile, sample, SAMPLE, tooLargeFile } from './support/files'
import { expectFocusRing, expectFocusTrapped, tabTo } from './support/keyboard'

/** Proper nouns and acronyms that keep their capital inside a sentence-case label. */
const PROPER = new Set(['PDF', 'PDFs', 'PyPDF', 'Gemini', 'GPT-5', 'Mini', 'Flash', 'Lite', 'UTC', 'OCR', 'Parse', 'Page'])

async function contrastViolations(page: Page): Promise<string[]> {
  const result = await new AxeBuilder({ page }).withRules(['color-contrast']).analyze()
  return result.violations.flatMap((violation) => violation.nodes.map((node) => node.target.join(' ')))
}

test('keyboard-only upload and confirm with a visible focus ring', async ({ page }, info) => {
  await openApp(page)
  await tabTo(page, /^Upload PDFs$/)
  await expectFocusRing(page)
  await page.keyboard.press('Enter')

  await tabTo(page, /^Choose files$/)
  await expectFocusRing(page)
  const chooser = page.waitForEvent('filechooser')
  await page.keyboard.press('Enter')
  await (await chooser).setFiles([sample(SAMPLE.dummy)])
  await tabTo(page, /^Upload 1 file$/)
  await page.keyboard.press('Enter')
  await expect(page.getByRole('button', { name: 'Done' })).toBeVisible()
  await tabTo(page, /^Done$/)
  await page.keyboard.press('Enter')

  await expectStatus(page, SAMPLE.dummy, 'ready')
  await tabTo(page, new RegExp(`^Delete ${SAMPLE.dummy}$`))
  await expectFocusRing(page)
  await page.keyboard.press('Enter')
  await expect(page.getByRole('alertdialog', { name: `Delete ${SAMPLE.dummy} forever?` })).toBeVisible()
  await tabTo(page, /^Delete forever$/)
  await expectFocusRing(page)
  await shot(page, info, 'keyboard-confirm')
  await page.keyboard.press('Enter')
  await expect(card(page, SAMPLE.dummy)).toHaveCount(0)
})

test('dialogs close on escape and keep focus inside', async ({ page }, info) => {
  await openApp(page)
  const dialog = await openUpload(page)
  await pickFiles(dialog, [sample(SAMPLE.dummy)])
  await expectFocusTrapped(page)
  await page.keyboard.press('Escape')
  await expect(dialog).toBeHidden()

  const ready = await uploadAndWait(page, sample(SAMPLE.dummy))
  await ready.getByRole('button', { name: 'View all 1 page' }).click()
  await expectFocusTrapped(page)
  await page.keyboard.press('Escape')
  await expect(page.getByRole('dialog', { name: SAMPLE.dummy })).toBeHidden()

  await ready.getByRole('button', { name: `Delete ${SAMPLE.dummy}` }).click()
  const confirm = page.getByRole('alertdialog')
  await expectFocusTrapped(page)
  await shot(page, info, 'dialog-focus')
  await page.keyboard.press('Escape')
  await expect(confirm).toBeHidden()
  await expect(ready).toBeVisible()
})

test('the pages sheet scrolls by keyboard and a dialog opened from more actions gives focus back', async ({ page }) => {
  await openApp(page)
  const ready = await uploadAndWait(page, pagesFile('thirty-pages.pdf', 30))

  await ready.getByRole('button', { name: 'View all 30 pages' }).click()
  const sheet = page.getByRole('dialog', { name: 'thirty-pages.pdf' })
  const body = sheet.getByRole('region', { name: 'thirty-pages.pdf' })
  const isFocused = () => body.evaluate((element) => element === document.activeElement)
  for (let press = 0; press < 3 && !(await isFocused()); press += 1) await page.keyboard.press('Tab')
  await expect(body).toBeFocused()
  await page.keyboard.press('PageDown')
  await expect.poll(() => body.evaluate((element) => element.scrollTop)).toBeGreaterThan(0)
  await page.keyboard.press('Escape')
  await expect(sheet).toBeHidden()

  const more = ready.getByRole('button', { name: 'More actions for thirty-pages.pdf' })
  await more.click()
  await page.getByRole('list', { name: 'Actions for thirty-pages.pdf' }).getByRole('button', { name: 'Reparse' }).click()
  const confirm = page.getByRole('alertdialog')
  await expect(confirm).toBeVisible()
  await page.keyboard.press('Escape')
  await expect(confirm).toBeHidden()
  await expect(more).toBeFocused()
})

test('text and controls keep 4.5 to 1 contrast', async ({ page }, info) => {
  await openApp(page)
  expect(await contrastViolations(page)).toEqual([])
  await upload(page, [sample(SAMPLE.dummy), sample(SAMPLE.scanned), tooLargeFile('thousand-pages.pdf')])
  await expectStatus(page, SAMPLE.scanned, 'no_text')
  await expectStatus(page, SAMPLE.dummy, 'ready')
  expect(await contrastViolations(page)).toEqual([])

  await chip(page, 'Failed').click()
  await expect(card(page, 'thousand-pages.pdf')).toBeVisible()
  expect(await contrastViolations(page)).toEqual([])

  const dialog = await openUpload(page)
  await pickFiles(dialog, [pdfFile('empty.pdf', Buffer.alloc(0)), sample(SAMPLE.locked)])
  await dialog.getByRole('button', { name: 'Upload 2 files' }).click()
  await expect(dialog.locator('li[data-file="empty.pdf"]')).toHaveAttribute('data-state', 'rejected')
  expect(await contrastViolations(page)).toEqual([])
  await shot(page, info, 'contrast')
})

test('every visible label and button is in sentence case', async ({ page }, info) => {
  await openApp(page)
  await uploadAndWait(page, sample(SAMPLE.dummy))
  const dialog = await openUpload(page)
  await pickFiles(dialog, [sample(SAMPLE.dummy)])

  const labels = await page.locator('button, label, legend, h1, h2, h3, option, [role="status"], [role="alert"]').evaluateAll((elements) =>
    elements
      .filter((element) => (element as HTMLElement).offsetParent !== null || element.tagName === 'OPTION')
      .map((element) => element.getAttribute('aria-label') ?? element.textContent?.trim() ?? '')
      .filter((text) => /[A-Za-z]/.test(text)),
  )
  const offenders = labels
    .filter((text) => {
      const words = text
        .split(/\s+/)
        .filter((word) => !word.toLowerCase().includes('.pdf'))
        .map((word) => word.replaceAll(/[·,?.!]/g, ''))
        .filter((word) => /^[A-Za-z0-9]/.test(word))
      const first = words[0] ?? ''
      const startsRight = first === '' || /^[A-Z0-9]/.test(first) || PROPER.has(first)
      return !startsRight || words.slice(1).some((word) => /^[A-Z]/.test(word) && !PROPER.has(word))
    })
  expect(labels.length).toBeGreaterThan(10)
  expect(offenders).toEqual([])
  await shot(page, info, 'sentence-case')
})
