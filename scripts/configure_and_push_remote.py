#!/usr/bin/env python
"""Configure git remote and push current branch.

Usage:
  python scripts/configure_and_push_remote.py [--remote-name origin] [--remote-url URL] [--branch BRANCH]

Resolution order for remote URL when origin is missing:
1) --remote-url
2) GIT_REMOTE_URL
3) https://github.com/${GITHUB_OWNER}/${REPO_NAME}.git (when GITHUB_OWNER is set)
4) Exact-name GitHub repository search (best-effort)

Authentication options for push:
- If GITHUB_TOKEN or GH_TOKEN is present and remote is https://github.com/...,
  push is attempted with an Authorization header for this command only.
"""

from __future__ import annotations

import argparse
import json
import os
import subprocess
import urllib.parse
import urllib.request
from pathlib import Path


def run(cmd: list[str], check: bool = True) -> subprocess.CompletedProcess[str]:
    return subprocess.run(cmd, check=check, text=True, capture_output=True)


def current_branch() -> str:
    return run(["git", "rev-parse", "--abbrev-ref", "HEAD"]).stdout.strip()


def repo_name() -> str:
    top = run(["git", "rev-parse", "--show-toplevel"]).stdout.strip()
    return Path(top).name


def remote_exists(remote_name: str) -> bool:
    result = run(["git", "remote"], check=False)
    remotes = {line.strip() for line in result.stdout.splitlines() if line.strip()}
    return remote_name in remotes


def remote_url(remote_name: str) -> str:
    return run(["git", "remote", "get-url", remote_name]).stdout.strip()


def github_token() -> str | None:
    return os.getenv("GITHUB_TOKEN") or os.getenv("GH_TOKEN")


def discovery_headers() -> dict[str, str]:
    headers = {
        "Accept": "application/vnd.github+json",
        "User-Agent": "paired-video-pipeline/0.1",
    }
    token = github_token()
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def discover_repo_url_by_name(name: str) -> str | None:
    """Find an exact GitHub repository-name match and return clone URL."""
    query = f"{name} in:name"
    url = "https://api.github.com/search/repositories?q=" + urllib.parse.quote(query)
    request = urllib.request.Request(url, headers=discovery_headers())
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.load(response)
    except Exception:
        return None

    items = payload.get("items", [])
    exact = [item for item in items if item.get("name") == name]
    if len(exact) == 1:
        return exact[0].get("clone_url")
    return None


def resolve_remote_url(explicit_url: str | None) -> str | None:
    if explicit_url:
        return explicit_url

    env_url = os.getenv("GIT_REMOTE_URL")
    if env_url:
        return env_url

    owner = os.getenv("GITHUB_OWNER")
    if owner:
        return f"https://github.com/{owner}/{repo_name()}.git"

    return discover_repo_url_by_name(repo_name())


def push_with_optional_token(remote_name: str, branch: str) -> subprocess.CompletedProcess[str]:
    cmd = ["git", "push", "-u", remote_name, branch]
    token = github_token()
    url = remote_url(remote_name)
    if token and url.startswith("https://github.com/"):
        cmd = [
            "git",
            "-c",
            f"http.https://github.com/.extraheader=AUTHORIZATION: bearer {token}",
            "push",
            "-u",
            remote_name,
            branch,
        ]
    return run(cmd, check=False)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--remote-name", default="origin")
    parser.add_argument("--remote-url")
    parser.add_argument("--branch")
    args = parser.parse_args()

    branch = args.branch or current_branch()

    if not remote_exists(args.remote_name):
        url = resolve_remote_url(args.remote_url)
        if not url:
            print(
                "ERROR: No git remote configured and no URL discovered. "
                "Set GIT_REMOTE_URL, set GITHUB_OWNER, or pass --remote-url."
            )
            return 2
        run(["git", "remote", "add", args.remote_name, url])
        print(f"Added remote {args.remote_name}: {url}")
    else:
        print(f"Using existing remote {args.remote_name}: {remote_url(args.remote_name)}")

    push = push_with_optional_token(args.remote_name, branch)
    if push.returncode != 0:
        stderr = push.stderr.strip()
        if "could not read Username" in stderr:
            print(
                "ERROR: Push failed because GitHub credentials are unavailable in this environment. "
                "Set GITHUB_TOKEN or GH_TOKEN for non-interactive auth."
            )
        elif "Authentication failed" in stderr or "403" in stderr:
            print(
                "ERROR: Push failed due to invalid/insufficient GitHub token permissions. "
                "Ensure token can push to this repository."
            )
        else:
            print(f"ERROR: git push failed: {stderr}")
        return push.returncode

    print(f"Pushed branch '{branch}' to {args.remote_name}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
