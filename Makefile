PYTHON ?= python
VENV ?= .venv

.PHONY: setup install build run-portal train check clean pull-components build-components pull-build-components check-wan-latest push-repo

setup:
	$(PYTHON) -m venv $(VENV)
	. $(VENV)/bin/activate && pip install --upgrade pip && pip install -e .

install:
	pip install -e .

build:
	$(PYTHON) -m pip wheel . -w dist

run-portal:
	uvicorn volunteer_portal.app:app --host 0.0.0.0 --port 8000 --reload

train:
	$(PYTHON) -m pipeline.train --manifest volunteer_portal/data/records.jsonl

pull-components:
	$(PYTHON) scripts/pull_and_build_components.py --pull

build-components:
	$(PYTHON) scripts/pull_and_build_components.py --build

pull-build-components:
	$(PYTHON) scripts/pull_and_build_components.py --pull --build

check-wan-latest:
	$(PYTHON) scripts/check_wan_latest.py

check:
	$(PYTHON) -m py_compile volunteer_portal/app.py volunteer_portal/storage.py pipeline/train.py scripts/pull_and_build_components.py scripts/check_wan_latest.py scripts/configure_and_push_remote.py
	$(PYTHON) -m unittest discover -s tests -p 'test_*.py'

push-repo:
	$(PYTHON) scripts/configure_and_push_remote.py

clean:
	$(PYTHON) -c "import pathlib, shutil; [shutil.rmtree(p, ignore_errors=True) if p.is_dir() else p.unlink(missing_ok=True) for pattern in ['build','dist','*.egg-info','external_components'] for p in pathlib.Path('.').glob(pattern)]"
