import { expect, test } from '@playwright/test'

import { openApp, openUpload, pickFiles, shot } from './support/app'
import { pdfFile } from './support/files'

const UPLOADS_PER_MINUTE = 10

test('a rate-limited upload shows the wait in seconds', async ({ page }, info) => {
  await openApp(page)
  for (let index = 0; index < UPLOADS_PER_MINUTE; index += 1) {
    const answer = await page.request.post('/api/v1/documents', {
      multipart: { parser: 'pypdf', files: { name: `empty-${index}.pdf`, mimeType: 'application/pdf', buffer: Buffer.alloc(0) } },
    })
    expect(answer.status()).not.toBe(429)
  }

  const dialog = await openUpload(page)
  await pickFiles(dialog, [pdfFile('one-too-many.pdf', Buffer.alloc(0))])
  const refused = page.waitForResponse((response) => response.url().endsWith('/api/v1/documents') && response.status() === 429)
  await dialog.getByRole('button', { name: 'Upload 1 file' }).click()
  const retryAfter = Number((await refused).headers()['retry-after'])
  expect(retryAfter).toBeGreaterThan(0)

  await dialog.getByRole('button', { name: 'Close' }).click()
  const notice = page.getByText(/^Too many uploads in the last minute\. You can upload again in \d+ s\.$/)
  await expect(notice).toBeVisible()
  const secondsOnScreen = async () => Number((await notice.textContent())?.match(/in (\d+) s/)?.[1])
  const shown = await secondsOnScreen()
  expect(shown).toBeLessThanOrEqual(retryAfter)
  expect(shown).toBeGreaterThan(retryAfter - 5)

  // The live region says the wait once; the ticking text on screen is not inside it.
  const announced = page.getByRole('status').filter({ hasText: 'Too many uploads in the last minute.' })
  await expect(announced).toHaveText(/^Too many uploads in the last minute\. You can upload again in \d+ seconds\.$/)
  const firstAnnouncement = await announced.textContent()
  await expect.poll(secondsOnScreen, { timeout: 5000 }).toBeLessThan(shown)
  await expect(announced).toHaveText(firstAnnouncement ?? '')
  await shot(page, info, 'rate-limited')
})
