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
  const notice = page.getByRole('status').filter({ hasText: 'Too many uploads in the last minute.' })
  await expect(notice).toHaveText(/You can upload again in \d+ s\.$/)
  const shown = Number((await notice.textContent())?.match(/in (\d+) s/)?.[1])
  expect(shown).toBeLessThanOrEqual(retryAfter)
  expect(shown).toBeGreaterThan(retryAfter - 5)
  await shot(page, info, 'rate-limited')
})
