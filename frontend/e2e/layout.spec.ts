import { expect, test } from '@playwright/test'

import { card, expectStatus, openApp, openUpload, shot, upload, uploadAndWait } from './support/app'
import { sample, SAMPLE, tooLargeFile } from './support/files'

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
  await openApp(page)
  const width = page.viewportSize()?.width ?? 0
  const navigation = page.getByRole('navigation', { name: 'Main' }).filter({ visible: true })
  const rightRail = page.getByRole('complementary', { name: 'About parsing' })
  await expect(navigation).toHaveCount(1)

  if (width >= 1024) {
    await expect(rightRail).toBeVisible()
    await expect(rightRail.getByRole('region', { name: 'Model pages today' })).toContainText(/of 3,000/)
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
    await expect(page.getByRole('banner')).toContainText(/of 3,000/)
  }
  await shot(page, info, 'rails-and-tab-bar')
})

test('the stories row shows active documents and hides when empty', async ({ page }, info) => {
  await openApp(page)
  const stories = page.getByRole('region', { name: 'In progress' })
  await expect(stories).toHaveCount(0)

  await upload(page, [sample(SAMPLE.dummy)])
  await expect(stories.getByRole('button', { name: new RegExp(`^${SAMPLE.dummy}, (queued|processing)$`) })).toBeVisible()
  await shot(page, info, 'stories-row')

  await expectStatus(page, SAMPLE.dummy, 'ready')
  await expect(stories).toHaveCount(0)
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
