import { execFileSync } from 'node:child_process'
import path from 'node:path'

/**
 * Bring up (or reuse) the e2e stack before any test. The stub answers each model call after
 * 1.5 s, so a document stays `queued` / `processing` long enough to be seen in the stories row.
 */
export default function globalSetup() {
  if (process.env.E2E_SKIP_STACK === '1') return
  const script = path.resolve(import.meta.dirname, '../../scripts/proofs/e2e-stack.sh')
  execFileSync(script, { stdio: 'inherit', env: { ...process.env, STUB_DELAY_S: process.env.STUB_DELAY_S ?? '1.5' } })
}
