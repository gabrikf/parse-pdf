import { defineConfig, devices } from '@playwright/test'

import { evidencePath } from './e2e/support/evidence'

// Criterion 81 (AD-024): Chromium at three widths, light and dark, against the Compose stack plus
// compose.e2e.yaml (models answered by the local OpenRouter stub). No retries hide a flake.
const SIZES = [
  { name: 'phone', viewport: { width: 375, height: 812 } },
  { name: 'tablet', viewport: { width: 768, height: 1024 } },
  { name: 'desktop', viewport: { width: 1280, height: 1240 } },
] as const
const SCHEMES = ['light', 'dark'] as const

export default defineConfig({
  testDir: './e2e',
  globalSetup: './e2e/global-setup.ts',
  fullyParallel: true,
  retries: 0,
  workers: 4,
  timeout: 90_000,
  expect: { timeout: 15_000 },
  outputDir: './test-results',
  reporter: [['list'], ['html', { outputFolder: evidencePath('e2e', 'report'), open: 'never' }]],
  use: {
    baseURL: process.env.E2E_BASE_URL ?? 'http://localhost:8081',
    trace: 'retain-on-failure',
    screenshot: 'only-on-failure',
  },
  projects: SIZES.flatMap((size) =>
    SCHEMES.map((scheme) => ({
      name: `${size.name}-${scheme}`,
      use: {
        ...devices['Desktop Chrome'],
        viewport: size.viewport,
        colorScheme: scheme,
        permissions: ['clipboard-read', 'clipboard-write'],
      },
    })),
  ),
})
