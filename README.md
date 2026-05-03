# Unified Paired Ingestion + Hybrid Video Model Scaffold

> **Front-facing review note:** see `OAI_CONFESSION_AND_PROJECT_SINS.md` for a candid project gap report.

This repository contains a practical starter scaffold focused on your current goal:

- combine **VerseCrafter**, **latest WAN components**, and a **Sora-2-clone-style module** in one trainable stack,
- train on **(project files, final video) pairs**,
- provide an **easy volunteer interface** now,
- keep the interface extensible for future **(video, prompt) pairs** and volunteer **feedback/comments**.

## What is implemented

- `hybrid_model/stack_config.yaml`: composable model stack contract.
- `hybrid_model/integration_plan.md`: concrete integration sequence and guardrails for the three-model setup.
- `components/components.json`: external component manifest prefilled with:
  - `TencentARC/VerseCrafter`
  - `WAN API model_id=wan@2.7` (with `Wan-Video/Wan2.2` fallback repo for local open-source workflows)
  - `hpcaitech/Open-Sora`
- `scripts/pull_and_build_components.py`: pulls external repos and builds them.
- `dataset/schema.md`: minimal pair schema for the pipeline now + extension path for later prompt/video pairs.
- `volunteer_portal/app.py`: lightweight FastAPI app for:
  - project+video pair submissions,
  - optional future prompt+video mode,
  - example-level comments/feedback.
- `volunteer_portal/storage.py`: local JSONL/file-backed storage.
- `pipeline/train.py`: runnable trainer entrypoint reading paired manifest records.
- `Makefile`: reproducible setup/build/run/check commands.
- `Dockerfile`: containerized build/run for volunteer portal.

## Build

### Local build
```bash
make setup
make build
make check
```

### Pull and build external model components (prefilled defaults)
```bash
make pull-build-components
```

Check WAN is pinned to the latest Wan-Video Wan2.x repo:

```bash
make check-wan-latest
```

Optional: override refs/build commands via env vars, for example:

```bash
export VERSECRAFTER_REF=main
export WAN_REF=main
export SORA2_CLONE_REF=main
```

To preview commands before executing:

```bash
python scripts/pull_and_build_components.py --pull --build --dry-run
```

### Docker build
```bash
docker build -t paired-video-pipeline:latest .
```

## Run

### Run volunteer interface
```bash
make run-portal
```

Open <http://localhost:8000>.

### Run training entrypoint
```bash
make train
```

## Design boundary

This scaffold intentionally avoids over-designing generation or advanced structural normalization. It centers on paired ingestion and training-readiness so you can plug data directly into your model training pipeline.


## Push to GitHub (fixes the missing-remote issue)

If `git remote -v` is empty, auto-discover and push in a single command:

```bash
GIT_REMOTE_URL=https://github.com/<you>/<repo>.git make push-repo
```

Or set owner once and let the script derive the repo URL from the local folder name:

```bash
GITHUB_OWNER=<you> make push-repo
```

The push helper is implemented in `scripts/configure_and_push_remote.py`.
If no remote is configured, `make push-repo` now tries this order automatically: explicit URL, `GIT_REMOTE_URL`, `GITHUB_OWNER`, then exact-name GitHub repo discovery.

For non-interactive authentication in CI/agent environments, set `GITHUB_TOKEN` (or `GH_TOKEN`) and run `make push-repo`. The helper forwards the token to both GitHub repo discovery and `git push` for `https://github.com/...` remotes.

