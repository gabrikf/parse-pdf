import path from 'node:path'

const REPO_EVIDENCE = path.resolve(import.meta.dirname, '../../../evidence')

/**
 * Where a run writes its records: `evidence/` in the repo, or `EVIDENCE_DIR` when set.
 * check_proofs.py runs with `EVIDENCE_DIR` outside the repo so the run leaves the tree clean (AD-038).
 */
export function evidencePath(...parts: string[]): string {
  return path.join(process.env.EVIDENCE_DIR ?? REPO_EVIDENCE, ...parts)
}
