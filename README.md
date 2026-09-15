# Paired Project-File → Video Training Pipeline

> **Front-facing review note:** see `OAI_CONFESSION_AND_PROJECT_SINS.md` for a candid project gap report.

> **Important clarification:** `/goal` is an operator instruction/ability for the agent workflow, **not** a standalone software package in this repository.

This repository now contains an executable baseline focused on your current goal:

- preserve raw project-file bytes as model conditioning,
- train on **(project files, final video) pairs**,
- provide an **easy volunteer interface** now,
- keep the interface extensible for future **(video, prompt) pairs** and volunteer **feedback/comments**.

## What runs now

- `pipeline/dataset.py`: reads the volunteer manifest, retains only file/video pairs, resolves stored files, and fails clearly on missing input.
- `pipeline/model.py`: a PyTorch raw-byte Transformer conditioner plus temporal 3D video decoder.
- `pipeline/train.py`: decodes submitted videos with PyAV, trains reconstruction + temporal-difference losses, and writes `checkpoint.pt` after every epoch.
- `dataset/schema.md`: minimal pair schema for the pipeline now + extension path for later prompt/video pairs.
- `volunteer_portal/app.py`: lightweight FastAPI app for:
  - project+video pair submissions,
  - optional future prompt+video mode,
  - example-level comments/feedback.
- `volunteer_portal/storage.py`: local JSONL/file-backed storage.
- `pipeline/train.py`: runnable trainer entrypoint reading paired manifest records.
- `Makefile`: reproducible setup/build/run/check commands; `make train` produces a checkpoint in `runs/latest/`.
- `Dockerfile`: containerized build/run for volunteer portal.

## Build

### Local build
```bash
make setup
make build
make check
```

### Train the working baseline
```bash
make setup
make train
```

`make train` expects submitted records at `volunteer_portal/data/records.jsonl`. It reads **only** `file_video_pair` records, uses their raw files unchanged as byte-token conditioning, and writes a checkpoint to `runs/latest/checkpoint.pt`.

For an explicit run configuration:

```bash
python -m pipeline.train \
  --manifest volunteer_portal/data/records.jsonl \
  --output runs/experiment-001 \
  --epochs 10 --batch-size 1 --frames 8 --size 64
```

The baseline is deliberately small enough to validate the data path and objective. It is not represented as a completed merge of VerseCrafter, WAN, and Open-Sora. Those upstream components remain separately managed under `components/components.json`; integrating compatible checkpoints is a subsequent model-engineering task, not something this repository falsely claims is finished.

### Pull external research components (optional)

```bash
make pull-components
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

## About `/goal`

`/goal` in this project context refers to a command-style instruction used to direct agent behavior (for example, “/goal: push to the repo”). It is intentionally treated as workflow control, not as a Python package, model artifact, or deployable service module.

## Design boundary

The input contract is paired ingestion: project files stay raw and are paired with their final videos. This repository does not add a scene schema, a file-generation feature, or a prompt-generation feature to the current training objective.


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
