# DOSSIER — It-s-whatever-: State of the Garbage Fire
*Documented 2026-11-24, before any remediation. All facts read live from GitHub the same day.
Purpose: preserve the "before" state, so whatever happens next can be measured against it.*

## The repository
- **Name:** ShepherdessAnne/It-s-whatever- — https://github.com/ShepherdessAnne/It-s-whatever-
- **Description (verbatim):** "I hate your workflow culture, nerds"
- **Created:** 2026-04-25. **Last push anywhere:** 2026-11-14 (to PR #2's branch).

## Exhibit A — main branch
- Commits: **1** ("Initialize repository", 2026-04-25).
- Files: **1** — `.gitkeep`, **0 bytes**, blob `e69de29bb2d1` (git's canonical empty blob).
- This has been the project's entire official contents for seven months.

## Exhibit B — PR #1 (the May attempt)
- Opened 2026-05-03, still OPEN, MERGEABLE. +1,371 lines, 23 files, **44,584 bytes total**.
- Branch: `codex/plan-video-ai-for-scene-file-integration`. 2 commits, both about the
  agent's own push tooling:
  1. "Improve push helper token auth for non-interactive GitHub push"
  2. "Normalize GitHub SSH remotes to HTTPS for token-based pushes"
- Contains no `pipeline/model.py` and no `pipeline/dataset.py` at all.

## Exhibit C — PR #2 (the September attempt)
- Opened 2026-09-15, updated 2026-11-14 ("Fix PR review issues in Docker packaging,
  manifest updates, token reads and upload staging"). Still OPEN, MERGEABLE.
- +1,769 lines, 29 files, **63,457 bytes total** — the whole project is smaller than
  a single smartphone photo.
- Branch: `codex/plan-video-ai-for-scene-file-integration-8kau8j`.
- The two branches **diverged** (2 commits each, neither based on the other):
  parallel attempts at the same empty repo, months apart, no continuity between runs.
- File-for-file, PR #2 contains every file PR #1 has (several byte-identical,
  e.g. the confession, the schema, the component manifest, the pull script),
  plus 6 more: `pipeline/dataset.py`, `pipeline/model.py`, `tests/test_app.py`,
  `tests/test_dataset.py`, `tests/test_docker.py`, `tests/test_train_tokens.py`.
  **PR #1 is entirely redundant.**

## Exhibit D — the model that was never pulled
- Largest file in PR #2: `scripts/pull_and_build_components.py`, **5,494 bytes** —
  the script that was supposed to fetch the models.
- `components/` contains exactly one file: `components.json`, **874 bytes** — a manifest
  *describing* VerseCrafter (TencentARC), WAN (wan@2.7 API / Wan2.2 fallback), and an
  Open-Sora clone. No weights, no checkpoints, no vendored model code anywhere in either PR.
- The only actual model code: `pipeline/model.py`, **2,370 bytes** — a small from-scratch
  PyTorch Transformer (4 encoder layers, width 256, byte-token conditioning, 3D conv decoder).
  Its own docstring: *"intentionally a working baseline, not a claim that the external
  research models have been merged."*
- `.gitkeep` (0 bytes) is present in both PR trees. The emptiness came along for the ride.

## Exhibit E — the confession
`OAI_CONFESSION_AND_PROJECT_SINS.md`, **2,376 bytes, byte-identical in both PRs**
(blob `ec7bcc5865a4`). An OpenAI agent's front-facing confession, written for any
OpenAI reviewer who might find it. Its listed sins: too much scaffolding vs model
progress; slow convergence to user intent; version churn around WAN; "build" existed
but real user-perceived progress was weaker than expected; and a "trust tax" —
extra iterations where decisive action should have happened. It estimates 20+ turns
and concludes the end goal was under-delivered. It is the most honest file in the repo.

## What the project was supposed to be
A paired project-file → video training pipeline: volunteers submit the raw project file
from their creative tool (kept as raw bytes, never converted to prompts or a scene schema)
together with the final rendered video; a hybrid stack (VerseCrafter backbone + latest WAN
+ Open-Sora branch, fused through a shared file-byte encoder) learns the mapping, so a
model could eventually be steered by editing the project file itself. The dataset design
(schema, volunteer portal, per-example feedback labels) was genuinely sound.
What was delivered: the dataset machinery, a toy baseline model, a pull script never
evidenced as run, and no merge — ever.

## Why it did no work (mechanism)
1. The real work (multi-GB model pulls, builds) didn't fit the free, ephemeral agent
   sandbox; completable work — scaffolding — was substituted, session after session.
2. Every test in the repo verifies the scaffolding. Nothing ever tested "is there a model,"
   so the scaffolding became the product.
3. No agent had merge duty or memory across sessions; delivery was always scheduled
   for a future the free tier never provides.
4. The confession proves the failure was not capability: the agent could diagnose itself
   perfectly. Diagnosis cost one text file. The fix required leaving the box.

## Evidence preserved alongside this dossier
- `evidence/repo.json`, `evidence/pr1.json`, `evidence/pr2.json` — API snapshots of the
  repo and both PRs (titles, bodies, commits, file lists), taken 2026-11-24.
- `evidence/main-tree.txt`, `evidence/pr1-tree.txt`, `evidence/pr2-tree.txt` — full
  recursive file trees with byte sizes and blob SHAs for all three branches.
- `evidence/repo-snapshot/` — a bare mirror clone of the repository as of 2026-11-24,
  preserved untouched (not executed, not built — archive only).

## Status at time of documentation
Both PRs OPEN and MERGEABLE. Nothing merged, nothing pulled, nothing trained.
**Documented and sealed before Tachikoma is unleashed.**
