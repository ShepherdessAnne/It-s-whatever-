from __future__ import annotations

import argparse
import json
import os
import re
import shlex
import shutil
import subprocess
from dataclasses import dataclass
from pathlib import Path


ENV_PATTERN = re.compile(r"\$\{([^}]+)\}")


@dataclass
class Component:
    name: str
    source_type: str
    repo: str
    ref: str
    build_cmd: str
    provider: str
    model_id: str


def _expand(value: str) -> str:
    def replace(match: re.Match[str]) -> str:
        expr = match.group(1)
        if ":-" in expr:
            key, default = expr.split(":-", 1)
            return os.environ.get(key, default)
        return os.environ.get(expr, match.group(0))

    return ENV_PATTERN.sub(replace, value)


def load_components(path: Path) -> list[Component]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    raw_components = payload.get("components", [])

    components: list[Component] = []
    for raw in raw_components:
        source_type = _expand(str(raw.get("source_type", "git")))
        repo = _expand(str(raw.get("repo", raw.get("fallback_repo", ""))))
        component = Component(
            name=str(raw["name"]),
            source_type=source_type,
            repo=repo,
            ref=_expand(str(raw.get("ref", "main"))),
            build_cmd=_expand(str(raw.get("build_cmd", "python -m pip wheel . -w dist"))),
            provider=_expand(str(raw.get("provider", ""))),
            model_id=_expand(str(raw.get("model_id", ""))),
        )
        components.append(component)
    return components


def run(cmd: str, cwd: Path | None = None, dry_run: bool = False) -> None:
    location = f" (cwd={cwd})" if cwd else ""
    print(f"$ {cmd}{location}")
    if dry_run:
        return
    subprocess.run(shlex.split(cmd), cwd=str(cwd) if cwd else None, check=True)


def _origin_url(repo_dir: Path) -> str:
    output = subprocess.check_output(
        ["git", "config", "--get", "remote.origin.url"],
        cwd=str(repo_dir),
        text=True,
    ).strip()
    return output


def _reclone(component: Component, dest: Path, dry_run: bool) -> None:
    if dry_run:
        print(f"$ rm -rf {dest}")
    else:
        shutil.rmtree(dest, ignore_errors=True)
    run(
        f"git clone --depth 1 --single-branch --branch {shlex.quote(component.ref)} "
        f"{shlex.quote(component.repo)} {shlex.quote(str(dest))}",
        dry_run=dry_run,
    )


def ensure_cloned(component: Component, base_dir: Path, dry_run: bool) -> Path:
    dest = base_dir / component.name
    if component.source_type != "git":
        print(
            f"Skipping git pull for {component.name}: source_type={component.source_type}, "
            f"provider={component.provider}, model_id={component.model_id}"
        )
        return dest

    if dest.exists():
        if not dry_run:
            current_origin = _origin_url(dest)
            if current_origin.rstrip("/") != component.repo.rstrip("/"):
                _reclone(component, dest, dry_run=dry_run)
            else:
                run(f"git fetch --depth 1 origin {shlex.quote(component.ref)}", cwd=dest, dry_run=dry_run)
        else:
            run(f"git fetch --depth 1 origin {shlex.quote(component.ref)}", cwd=dest, dry_run=dry_run)
    else:
        run(
            f"git clone --depth 1 --single-branch --branch {shlex.quote(component.ref)} "
            f"{shlex.quote(component.repo)} {shlex.quote(str(dest))}",
            dry_run=dry_run,
        )

    run(f"git checkout {shlex.quote(component.ref)}", cwd=dest, dry_run=dry_run)
    run(f"git pull --ff-only origin {shlex.quote(component.ref)}", cwd=dest, dry_run=dry_run)
    return dest


def pull(components: list[Component], workspace: Path, dry_run: bool) -> None:
    workspace.mkdir(parents=True, exist_ok=True)
    for component in components:
        if component.source_type == "git" and not component.repo:
            raise ValueError(f"Component '{component.name}' is missing repo URL.")
        ensure_cloned(component, workspace, dry_run)


def build(components: list[Component], workspace: Path, dry_run: bool) -> None:
    for component in components:
        if component.source_type != "git":
            print(
                f"Skipping local build for {component.name}: source_type={component.source_type}, "
                f"provider={component.provider}, model_id={component.model_id}"
            )
            continue

        dest = workspace / component.name
        if not dest.exists() and not dry_run:
            raise FileNotFoundError(f"Component directory missing: {dest}. Run pull first.")
        run(component.build_cmd, cwd=dest, dry_run=dry_run)


def main() -> None:
    parser = argparse.ArgumentParser(description="Pull and build external model components")
    parser.add_argument("--config", type=Path, default=Path("components/components.json"))
    parser.add_argument("--workspace", type=Path, default=Path("external_components"))
    parser.add_argument("--pull", action="store_true")
    parser.add_argument("--build", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    if not args.pull and not args.build:
        parser.error("Specify at least one action: --pull and/or --build")

    components = load_components(args.config)
    if args.pull:
        pull(components, args.workspace, args.dry_run)
    if args.build:
        build(components, args.workspace, args.dry_run)


if __name__ == "__main__":
    main()
