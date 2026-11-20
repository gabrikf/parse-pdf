import { defineConfig, devices } from '@playwright/test'

// S6 browser proofs (law 3): the real page on the Vite dev server (`.claude/launch.json`, port
// 5180, proxying /api to the e2e stack) at each canvas frame's size, saved next to the frames as
// `captures/<Frame>.running.png`. Run: npx playwright test -c playwright.captures.config.ts
export default defineConfig({
  testDir: './captures',
  // The same stack as the e2e run: the 1.5 s stub delay and an unused model budget.
  globalSetup: './e2e/global-setup.ts',
  testMatch: '*.capture.ts',
  retries: 0,
  workers: 3,
  timeout: 120_000,
  expect: { timeout: 60_000 },
  reporter: [['list']],
  use: { ...devices['Desktop Chrome'], baseURL: process.env.CAPTURE_BASE_URL ?? 'http://localhost:5180' },
})
