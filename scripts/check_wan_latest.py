from __future__ import annotations

import json
import re
import urllib.request
from pathlib import Path

WAN_REPO_PATTERN = re.compile(r"^Wan2\.(\d+)$")
WAN_MODEL_PATTERN = re.compile(r"^wan@2\.(\d+)$")


def fetch_wan_repos() -> list[str]:
    url = "https://api.github.com/orgs/Wan-Video/repos?per_page=100"
    with urllib.request.urlopen(url, timeout=20) as response:
        payload = json.loads(response.read().decode("utf-8"))
    return [item.get("name", "") for item in payload]


def latest_wan_repo_name(repo_names: list[str]) -> str:
    versions: list[tuple[int, str]] = []
    for name in repo_names:
        match = WAN_REPO_PATTERN.match(name)
        if match:
            versions.append((int(match.group(1)), name))

    if not versions:
        raise RuntimeError("No Wan2.x repositories found in Wan-Video org")

    versions.sort(key=lambda item: item[0], reverse=True)
    return versions[0][1]


def configured_wan_component(config_path: Path) -> dict:
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    for component in payload.get("components", []):
        if component.get("name") == "wan_latest":
            return component
    raise RuntimeError("wan_latest component not found in components config")


def _wan_model_minor(model_id: str) -> int | None:
    match = WAN_MODEL_PATTERN.match(model_id.strip())
    if not match:
        return None
    return int(match.group(1))


def main() -> None:
    repo_names = fetch_wan_repos()
    latest_repo_name = latest_wan_repo_name(repo_names)
    latest_repo_minor = int(latest_repo_name.split(".")[1])

    config_path = Path("components/components.json")
    wan_component = configured_wan_component(config_path)

    source_type = str(wan_component.get("source_type", "git"))
    configured_repo = str(wan_component.get("repo", wan_component.get("fallback_repo", "")))
    configured_model_id = str(wan_component.get("model_id", ""))

    print(f"Latest WAN repo in Wan-Video org: {latest_repo_name}")
    print(f"Configured WAN source_type: {source_type}")

    if source_type == "api":
        minor = _wan_model_minor(configured_model_id)
        if minor is None:
            raise SystemExit(f"WAN API model_id is invalid: {configured_model_id}")
        print(f"Configured WAN API model_id: {configured_model_id}")
        if minor < latest_repo_minor:
            raise SystemExit(
                f"WAN API model_id is older than latest Wan-Video open repo minor version. "
                f"model_id={configured_model_id}, latest_repo={latest_repo_name}"
            )
        print("Configured WAN API model_id is >= latest Wan-Video open repo minor version.")
        return

    expected_suffix = f"/Wan-Video/{latest_repo_name}.git"
    print(f"Configured WAN repo: {configured_repo}")

    if not configured_repo.endswith(expected_suffix):
        raise SystemExit(
            f"Configured WAN repo is outdated. Expected suffix '{expected_suffix}', got '{configured_repo}'."
        )

    print("Configured WAN repo matches latest Wan-Video Wan2.x repository.")


if __name__ == "__main__":
    main()
