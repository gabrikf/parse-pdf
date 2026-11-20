import { expect, type Page } from '@playwright/test'

/** The accessible name of the focused element: its aria-label, or its text. */
export function focusedName(page: Page): Promise<string> {
  return page.evaluate(() => {
    const element = document.activeElement
    return element?.getAttribute('aria-label') ?? element?.textContent?.trim() ?? ''
  })
}

/** Press Tab until the focused element's name matches, as a keyboard user would. */
export async function tabTo(page: Page, name: RegExp, limit = 60): Promise<void> {
  if (name.test(await focusedName(page))) return
  for (let step = 0; step < limit; step += 1) {
    await page.keyboard.press('Tab')
    if (name.test(await focusedName(page))) return
  }
  throw new Error(`Tab never reached ${String(name)}`)
}

/** The focused element draws a visible outline (the focus ring). */
export async function expectFocusRing(page: Page): Promise<void> {
  const ring = await page.evaluate(() => {
    const element = document.activeElement
    if (!element) return null
    const style = getComputedStyle(element)
    return { style: style.outlineStyle, width: Number.parseFloat(style.outlineWidth) }
  })
  expect(ring?.style).not.toBe('none')
  expect(ring?.width).toBeGreaterThanOrEqual(2)
}

/** Tab through `presses` stops and check that focus never leaves the open dialog. */
export async function expectFocusTrapped(page: Page, presses = 15): Promise<void> {
  for (let step = 0; step < presses; step += 1) {
    await page.keyboard.press(step % 3 === 2 ? 'Shift+Tab' : 'Tab')
    const inside = await page.evaluate(() => {
      const dialog = document.querySelector('dialog[open]')
      return dialog !== null && dialog.contains(document.activeElement)
    })
    expect(inside).toBe(true)
  }
}
