import { mkdirSync } from 'node:fs'
import path from 'node:path'

import { expect, type Locator, type Page, type TestInfo } from '@playwright/test'

import type { FilePayload } from './files'

const SCREENS = path.resolve(import.meta.dirname, '../../../evidence/e2e/screens')
export const PROCESSING_TIMEOUT = 60_000

/** Open the page and wait for the session and the first read. */
export async function openApp(page: Page): Promise<void> {
  const session = page.waitForResponse((response) => response.url().endsWith('/api/v1/sessions') && response.ok())
  await page.goto('/')
  await session
}

/** The visible "Upload PDFs" control: the tab bar on phones, the rail from 768 px. */
export function uploadControl(page: Page): Locator {
  return page.getByRole('navigation', { name: 'Main' }).filter({ visible: true }).getByRole('button', { name: 'Upload PDFs' })
}

export function uploadDialog(page: Page): Locator {
  return page.getByRole('dialog', { name: 'Upload PDFs' })
}

export async function openUpload(page: Page): Promise<Locator> {
  await uploadControl(page).click()
  const dialog = uploadDialog(page)
  await expect(dialog).toBeVisible()
  return dialog
}

/** Add files through the hidden picker input, as the file chooser does. */
export async function pickFiles(dialog: Locator, files: FilePayload[]): Promise<void> {
  await dialog.getByLabel('Choose PDF files').setInputFiles(files)
}

/** Pick, choose the parser, send, and close the dialog once every file has an outcome. */
export async function upload(page: Page, files: FilePayload[], parser?: string): Promise<void> {
  const dialog = await openUpload(page)
  await pickFiles(dialog, files)
  if (parser) await dialog.getByLabel('Parser').selectOption(parser)
  await dialog.getByRole('button', { name: /^Upload \d+ files?$/ }).click()
  await expect(dialog.getByRole('button', { name: 'Done' })).toBeVisible()
  await dialog.getByRole('button', { name: 'Done' }).click()
  await expect(dialog).toBeHidden()
}

export function card(page: Page, filename: string): Locator {
  return page.getByRole('article', { name: filename, exact: true })
}

export function chip(page: Page, label: 'Parsed' | 'Failed' | 'All'): Locator {
  return page.getByRole('group', { name: 'Show in feed' }).getByRole('button', { name: new RegExp(`^${label}\\b`) })
}

/** Wait until the card shows in the current feed with the given status. */
export async function expectStatus(page: Page, filename: string, status: string): Promise<Locator> {
  const target = card(page, filename)
  await expect(target).toHaveAttribute('data-status', status, { timeout: PROCESSING_TIMEOUT })
  return target
}

/** Upload one file and wait for it to reach the status, on the chip that shows it. */
export async function uploadAndWait(page: Page, file: FilePayload, status = 'ready', parser?: string): Promise<Locator> {
  await upload(page, [file], parser)
  if (status === 'dead' || status === 'too_large') await chip(page, 'Failed').click()
  return expectStatus(page, file.name, status)
}

/** One screenshot per scenario and size, kept in `evidence/e2e/screens/<project>/`. */
export async function shot(page: Page, info: TestInfo, slug: string): Promise<void> {
  const folder = path.join(SCREENS, info.project.name)
  mkdirSync(folder, { recursive: true })
  await page.screenshot({ path: path.join(folder, `${slug}.jpg`), type: 'jpeg', quality: 70 })
}
