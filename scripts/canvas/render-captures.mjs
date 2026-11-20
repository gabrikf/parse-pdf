// Render every frame of a design canvas to `<Frame>.png` at the frame's size (canvas.json w x h).
//   node scripts/canvas/render-captures.mjs .specs/features/document-processing/captures
import { chromium } from '../../frontend/node_modules/playwright/index.mjs';
import { readFileSync, copyFileSync, rmSync } from 'node:fs';
import { join, resolve } from 'node:path';
import { pathToFileURL } from 'node:url';

const captures = resolve(process.argv[2]);
const canvas = join(captures, 'canvas');
const boards = JSON.parse(readFileSync(join(canvas, 'canvas.json'), 'utf8')).boards;
const shim = join(canvas, 'support.js');
copyFileSync(new URL('./support.js', import.meta.url), shim);

const browser = await chromium.launch({ args: ['--allow-file-access-from-files'] });
try {
  for (const [file, board] of Object.entries(boards)) {
    const page = await browser.newPage({ viewport: { width: board.w, height: board.h }, deviceScaleFactor: 1 });
    page.on('console', (message) => { if (message.type() === 'warning') console.warn(file, message.text()); });
    await page.goto(pathToFileURL(join(canvas, file)).href);
    await page.waitForSelector('body[data-rendered="true"]', { timeout: 30000 });
    const out = join(captures, file.replace('.dc.html', '.png'));
    await page.screenshot({ path: out, clip: { x: 0, y: 0, width: board.w, height: board.h } });
    console.log(`${out} ${board.w}x${board.h} - ${board.title}`);
    await page.close();
  }
} finally {
  await browser.close();
  rmSync(shim);
}
