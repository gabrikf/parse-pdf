import { expect, test } from '@playwright/test'

import { card, chip, expectStatus, openApp, shot, upload, uploadAndWait } from './support/app'
import { failOnceFile, sample, SAMPLE, tooLargeFile, unsafeFile } from './support/files'

test('reparse with another parser asks first and cancel sends nothing', async ({ page }, info) => {
  await openApp(page)
  const ready = await uploadAndWait(page, sample(SAMPLE.dummy))
  const reparses: string[] = []
  page.on('request', (request) => {
    if (request.url().endsWith('/reparse')) reparses.push(request.postData() ?? '')
  })

  await ready.getByRole('button', { name: `Reparse ${SAMPLE.dummy}` }).click()
  const confirm = page.getByRole('alertdialog', { name: `Reparse ${SAMPLE.dummy}?` })
  await expect(confirm).toContainText('Its pages and summary are cleared')
  await expect(confirm.getByRole('radio', { name: /PyPDF/ })).toBeChecked()
  await confirm.getByText('GPT-5 Mini').click()
  await shot(page, info, 'reparse-confirm')
  await confirm.getByRole('button', { name: 'Cancel' }).click()
  await expect(confirm).toBeHidden()
  expect(reparses).toEqual([])
  await expect(ready).toHaveAttribute('data-status', 'ready')

  await ready.getByRole('button', { name: `Reparse ${SAMPLE.dummy}` }).click()
  await confirm.getByText('GPT-5 Mini').click()
  await confirm.getByRole('button', { name: 'Reparse' }).click()
  await expect.poll(() => reparses).toEqual([JSON.stringify({ parser: 'gpt-5-mini' })])
  await expect(await expectStatus(page, SAMPLE.dummy, 'ready')).toContainText('GPT-5 Mini · 1 page')
})

test('delete forever removes the card and it stays gone after reload', async ({ page }, info) => {
  await openApp(page)
  const ready = await uploadAndWait(page, sample(SAMPLE.dummy))

  await ready.getByRole('button', { name: `Delete ${SAMPLE.dummy}` }).click()
  const confirm = page.getByRole('alertdialog', { name: `Delete ${SAMPLE.dummy} forever?` })
  await expect(confirm).toContainText("This can't be undone.")
  const action = confirm.getByRole('button', { name: 'Delete forever' })
  const danger = await page.evaluate(() => getComputedStyle(document.documentElement).getPropertyValue('--danger').trim())
  const background = await action.evaluate((element) => getComputedStyle(element).backgroundColor)
  expect(background).toBe(await page.evaluate((hex) => {
    const probe = document.createElement('i')
    probe.style.color = hex
    document.body.append(probe)
    const rgb = getComputedStyle(probe).color
    probe.remove()
    return rgb
  }, danger))
  await shot(page, info, 'delete-confirm')

  await action.click()
  await expect(card(page, SAMPLE.dummy)).toHaveCount(0)
  await page.reload()
  await expect(page.getByRole('heading', { name: 'No documents yet' })).toBeVisible()
  await expect(card(page, SAMPLE.dummy)).toHaveCount(0)
})

test('a refused action keeps its confirmation open with the reason and refreshes the feed', async ({ page }, info) => {
  await openApp(page)
  const ready = await uploadAndWait(page, sample(SAMPLE.dummy))
  const listed = await (await page.request.get('/api/v1/documents?state=all&limit=50')).json()
  const document = (listed.data as { id: string; filename: string }[]).find((item) => item.filename === SAMPLE.dummy)
  expect(document).toBeDefined()

  await ready.getByRole('button', { name: `Delete ${SAMPLE.dummy}` }).click()
  const confirm = page.getByRole('alertdialog', { name: `Delete ${SAMPLE.dummy} forever?` })
  // Another tab deletes it while this confirmation is open.
  expect((await page.request.delete(`/api/v1/documents/${document?.id}`)).status()).toBe(200)

  const refused = page.waitForResponse((response) => response.request().method() === 'DELETE' && response.status() === 404)
  await confirm.getByRole('button', { name: 'Delete forever' }).click()
  await refused
  await expect(confirm).toBeVisible()
  await expect(confirm.getByRole('alert')).toHaveText('This document is gone. It may have been deleted in another tab.')
  await expect(card(page, SAMPLE.dummy)).toHaveCount(0)
  await shot(page, info, 'action-refused')

  await confirm.getByRole('button', { name: 'Cancel' }).click()
  await expect(confirm).toBeHidden()
})

test('a document the safety check flags says which category, not only that it failed', async ({ page }, info) => {
  await openApp(page)
  const dead = await uploadAndWait(page, unsafeFile('flagged.pdf'), 'dead')

  await expect(dead).toContainText(
    "The safety check flagged the document's text for violent crimes (S1), so no summary was written.",
  )
  await shot(page, info, 'dead-card-guardrail-hint')
})

test('retry a dead document moves it to the stories row as queued', async ({ page }, info) => {
  await openApp(page)
  const file = failOnceFile('refused-once.pdf')
  const dead = await uploadAndWait(page, file, 'dead')
  await expect(dead).toContainText('The model provider refused this file.')
  await expect(dead.getByRole('button').filter({ hasNotText: /^$/ })).toHaveText(['Retry', 'Reparse with another parser', 'Delete forever'])
  await shot(page, info, 'dead-card')

  for (const [button, title] of [
    ['Reparse with another parser', `Reparse ${file.name}?`],
    ['Delete forever', `Delete ${file.name} forever?`],
  ] as const) {
    await dead.getByRole('button', { name: button }).click()
    const asked = page.getByRole('alertdialog', { name: title })
    await expect(asked).toBeVisible()
    await asked.getByRole('button', { name: 'Cancel' }).click()
    await expect(asked).toHaveCount(0)
  }

  await dead.getByRole('button', { name: 'Retry' }).click()
  const confirm = page.getByRole('alertdialog', { name: `Retry ${file.name}?` })
  await expect(confirm).toContainText('It goes back in the queue with the same parser, PyPDF.')
  const answer = page.waitForResponse((response) => response.url().endsWith('/requeue'))
  await confirm.getByRole('button', { name: 'Retry' }).click()
  expect((await (await answer).json()).data.status).toBe('queued')

  await expect(card(page, file.name)).toHaveCount(0)
  await expect(page.getByRole('region', { name: 'In progress' }).getByRole('button', { name: new RegExp(`^${file.name}, `) })).toBeVisible()
  await shot(page, info, 'retry-in-stories')
  await chip(page, 'Parsed').click()
  await expectStatus(page, file.name, 'ready')
})

test('a too_large card offers only delete forever', async ({ page }, info) => {
  await openApp(page)
  const large = await uploadAndWait(page, tooLargeFile('thousand-pages.pdf'), 'too_large')

  await expect(large).toContainText('1,001 pages')
  const buttons = large.getByRole('button').filter({ hasNotText: /^$/ })
  await expect(buttons).toHaveText(['Delete forever'])
  await large.getByRole('button', { name: /More actions/ }).click()
  const menu = page.getByRole('list', { name: 'Actions for thousand-pages.pdf' })
  await expect(menu.getByRole('button')).toHaveText(['Delete forever'])
  await page.keyboard.press('Escape')
  await expect(menu).toHaveCount(0)
  await expect(large.getByRole('button', { name: /More actions/ })).toBeFocused()
  await large.getByRole('button', { name: /More actions/ }).click()
  await shot(page, info, 'too-large-card')
})

test('parsed, failed and all chips filter the feed with counts', async ({ page }, info) => {
  await openApp(page)
  await upload(page, [sample(SAMPLE.dummy), tooLargeFile('thousand-pages.pdf')])
  await expectStatus(page, SAMPLE.dummy, 'ready')

  await expect(chip(page, 'Parsed')).toHaveAttribute('aria-pressed', 'true')
  await expect(chip(page, 'Parsed')).toHaveText('Parsed 1')
  await expect(chip(page, 'Failed')).toHaveText('Failed 1')
  await expect(chip(page, 'All')).toHaveText('All 2')
  await expect(page.getByRole('article')).toHaveCount(1)
  await shot(page, info, 'chips-parsed')

  await chip(page, 'Failed').click()
  await expect(page.getByRole('article')).toHaveCount(1)
  await expect(card(page, 'thousand-pages.pdf')).toBeVisible()
  await chip(page, 'All').click()
  await expect(page.getByRole('article')).toHaveCount(2)

  await page.reload()
  await expect(chip(page, 'Parsed')).toHaveAttribute('aria-pressed', 'true')
})
