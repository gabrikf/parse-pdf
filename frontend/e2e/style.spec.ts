import { mkdirSync, writeFileSync } from 'node:fs'
import path from 'node:path'

import { expect, test } from '@playwright/test'

import { card, openApp, openUpload, pickFiles, shot, uploadAndWait } from './support/app'
import { sample, SAMPLE } from './support/files'

const NETWORK_LOGS = path.resolve(import.meta.dirname, '../../evidence/upload-page')
const PRIMARY = { light: 'rgb(109, 40, 217)', dark: 'rgb(167, 139, 250)' } as const

test('the page calls only its own origin under /api/v1/', async ({ page, baseURL }, info) => {
  const seen: { method: string; url: URL; type: string }[] = []
  page.on('request', (request) => seen.push({ method: request.method(), url: new URL(request.url()), type: request.resourceType() }))

  await openApp(page)
  const ready = await uploadAndWait(page, sample(SAMPLE.dummy))
  await ready.getByRole('button', { name: 'View all 1 page' }).click()
  await page.keyboard.press('Escape')
  await ready.getByRole('button', { name: `Reparse ${SAMPLE.dummy}` }).click()
  await page.getByRole('button', { name: 'Cancel' }).click()

  const origin = new URL(baseURL ?? '').origin
  const calls = seen.filter((entry) => entry.type === 'fetch' || entry.type === 'xhr')
  expect(seen.filter((entry) => entry.url.origin !== origin && entry.url.protocol !== 'data:')).toEqual([])
  expect(calls.length).toBeGreaterThan(3)
  expect(calls.filter((entry) => !entry.url.pathname.startsWith('/api/v1/'))).toEqual([])

  mkdirSync(NETWORK_LOGS, { recursive: true })
  const lines = seen.map((entry) => `${entry.method} ${entry.type} ${entry.url.origin}${entry.url.pathname}`)
  writeFileSync(path.join(NETWORK_LOGS, `network-${info.project.name}.txt`), `${lines.join('\n')}\n`)
  await shot(page, info, 'own-origin')
})

test('the primary color, fonts and no shadows or gradients', async ({ page }, info) => {
  await openApp(page)
  const ready = await uploadAndWait(page, sample(SAMPLE.dummy))
  const scheme = info.project.use.colorScheme === 'dark' ? 'dark' : 'light'

  const summaryFont = await ready.locator('[class*="markdown"]').first().evaluate((element) => getComputedStyle(element).fontFamily)
  expect(summaryFont).toContain('Newsreader Variable')
  expect(await page.evaluate(() => getComputedStyle(document.body).fontFamily)).toContain('Schibsted Grotesk Variable')
  await expect.poll(() => page.evaluate(() => document.fonts.check('16px "Schibsted Grotesk Variable"'))).toBe(true)

  const icons = await page.locator('svg.lucide').evaluateAll((svgs) => svgs.map((svg) => [svg.getAttribute('fill'), svg.getAttribute('stroke')]))
  expect(icons.length).toBeGreaterThan(3)
  expect(icons.every(([fill, stroke]) => fill === 'none' && stroke === 'currentColor')).toBe(true)

  const dialog = await openUpload(page)
  await pickFiles(dialog, [sample(SAMPLE.dummy)])
  const primary = dialog.getByRole('button', { name: 'Upload 1 file' })
  expect(await primary.evaluate((element) => getComputedStyle(element).backgroundColor)).toBe(PRIMARY[scheme])

  const decorated = await page.locator('body *').evaluateAll((elements) =>
    elements
      .map((element) => ({ element, style: getComputedStyle(element) }))
      .filter(({ style }) => style.boxShadow !== 'none' || style.backgroundImage !== 'none')
      .map(({ element }) => `${element.tagName}.${element.className}`),
  )
  expect(decorated).toEqual([])
  await shot(page, info, 'primary-and-fonts')
  await expect(card(page, SAMPLE.dummy)).toBeVisible()
})
