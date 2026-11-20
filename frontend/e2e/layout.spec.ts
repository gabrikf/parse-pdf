import { expect, test } from '@playwright/test'

import { card, expectStatus, openApp, openUpload, shot, upload, uploadAndWait } from './support/app'
import { pdfFile, sample, SAMPLE, tooLargeFile } from './support/files'

const MIN_TARGET = 44
const TARGETS = 'button, a[href], select, input:not([type="radio"]):not([type="file"]), label:has(input[type="radio"])'

/** Every visible control smaller than 44 x 44 px, by its name. */
async function smallTargets(page: import('@playwright/test').Page): Promise<string[]> {
  return page.locator(TARGETS).evaluateAll((elements, min) => {
    return elements
      .filter((element) => (element as HTMLElement).offsetParent !== null && !element.closest('.visually-hidden'))
      .filter((element) => {
        const box = element.getBoundingClientRect()
        return box.width < min || box.height < min
      })
      .map((element) => `${element.tagName} ${element.getAttribute('aria-label') ?? element.textContent?.trim() ?? ''}`)
  }, MIN_TARGET)
}

async function noHorizontalScroll(page: import('@playwright/test').Page) {
  expect(await page.evaluate(() => document.documentElement.scrollWidth <= window.innerWidth)).toBe(true)
}

test('no horizontal scroll and touch targets are at least 44 px', async ({ page }, info) => {
  await openApp(page)
  await noHorizontalScroll(page)
  await upload(page, [sample(SAMPLE.dummy), tooLargeFile('thousand-pages.pdf')])
  await expectStatus(page, SAMPLE.dummy, 'ready')

  await noHorizontalScroll(page)
  expect(await smallTargets(page)).toEqual([])
  await shot(page, info, 'targets-feed')

  await openUpload(page)
  expect(await smallTargets(page)).toEqual([])
  await page.keyboard.press('Escape')
  await card(page, SAMPLE.dummy).getByRole('button', { name: `Reparse ${SAMPLE.dummy}` }).click()
  expect(await smallTargets(page)).toEqual([])
  await noHorizontalScroll(page)
})

test('wide screens show both rails with the budget and phones a tab bar', async ({ page }, info) => {
  const budgetAnswer = page.waitForResponse((response) => response.url().endsWith('/api/v1/budget') && response.ok())
  await openApp(page)
  const budget = (await (await budgetAnswer).json()).data as { used: number; limit: number }
  const budgetText = `${budget.used.toLocaleString('en-US')} of ${budget.limit.toLocaleString('en-US')}`
  const width = page.viewportSize()?.width ?? 0
  const navigation = page.getByRole('navigation', { name: 'Main' }).filter({ visible: true })
  const rightRail = page.getByRole('complementary', { name: 'About parsing' })
  await expect(navigation).toHaveCount(1)

  if (width >= 1024) {
    await expect(rightRail).toBeVisible()
    await expect(rightRail.getByRole('region', { name: 'Model pages today' })).toContainText(budgetText)
    await expect(rightRail).toContainText('PyPDF')
    const box = await navigation.boundingBox()
    expect(box?.x).toBe(0)
  } else if (width >= 768) {
    await expect(rightRail).toBeHidden()
    const box = await navigation.boundingBox()
    expect(box?.width).toBe(72)
  } else {
    await expect(rightRail).toBeHidden()
    const box = await navigation.boundingBox()
    expect((box?.y ?? 0) + (box?.height ?? 0)).toBe(page.viewportSize()?.height)
    await expect(page.getByRole('banner')).toContainText(budgetText)
  }
  await shot(page, info, 'rails-and-tab-bar')
})

test('the stories row shows active documents and keeps Upload once any document exists', async ({ page }, info) => {
  await openApp(page)
  const stories = page.getByRole('region', { name: 'In progress' })
  await expect(stories).toHaveCount(0)

  await upload(page, [sample(SAMPLE.dummy)])
  await expect(stories.getByRole('button', { name: new RegExp(`^${SAMPLE.dummy}, (queued|processing)$`) })).toBeVisible()
  await shot(page, info, 'stories-row')

  await expectStatus(page, SAMPLE.dummy, 'ready')
  await expect(stories.getByRole('button', { name: /, (queued|processing)$/ })).toHaveCount(0)
  await expect(stories.getByRole('button', { name: 'Upload' })).toBeVisible()

  // Tapping a story scrolls to its card: reparse the oldest card, so it sits below 4 newer ones.
  await upload(page, ['a.pdf', 'b.pdf', 'c.pdf', 'd.pdf'].map((name) => pdfFile(name, sample(SAMPLE.dummy).buffer)))
  for (const name of ['a.pdf', 'b.pdf', 'c.pdf', 'd.pdf']) await expectStatus(page, name, 'ready')
  await card(page, SAMPLE.dummy).getByRole('button', { name: `Reparse ${SAMPLE.dummy}` }).click()
  const confirm = page.getByRole('alertdialog', { name: `Reparse ${SAMPLE.dummy}?` })
  await confirm.getByRole('radio', { name: /Gemini 3.1 Flash Lite/ }).check()
  await confirm.getByRole('button', { name: 'Reparse' }).click()
  const story = stories.getByRole('button', { name: new RegExp(`^${SAMPLE.dummy}, (queued|processing)$`) })
  await expect(story).toBeVisible()
  await page.evaluate(() => window.scrollTo({ top: document.body.scrollHeight }))
  await story.click()
  await expect(card(page, SAMPLE.dummy)).toBeInViewport()
})

test('the theme follows the system and the toggle is remembered', async ({ page }, info) => {
  await openApp(page)
  const scheme = info.project.use.colorScheme
  const other = scheme === 'dark' ? 'light' : 'dark'
  await expect(page.locator('html')).toHaveAttribute('data-theme', scheme ?? 'light')

  const toggle = page.getByRole('navigation', { name: 'Main' }).filter({ visible: true }).getByRole('button', { name: scheme === 'dark' ? 'Light mode' : 'Dark mode' })
  await toggle.click()
  await expect(page.locator('html')).toHaveAttribute('data-theme', other)

  await page.reload()
  await expect(page.locator('html')).toHaveAttribute('data-theme', other)
  expect(await page.evaluate(() => localStorage.getItem('parse-pdf-theme'))).toBe(other)
  await uploadAndWait(page, sample(SAMPLE.dummy))
  await shot(page, info, 'theme-toggled')
})
