from __future__ import annotations

import os
import unittest
from unittest.mock import MagicMock, patch

from scripts.configure_and_push_remote import (
    discover_repo_url_by_name,
    discovery_headers,
    push_with_optional_token,
    resolve_remote_url,
    to_https_github_url,
)


class ConfigureAndPushRemoteTests(unittest.TestCase):
    @patch("scripts.configure_and_push_remote.json.load")
    @patch("scripts.configure_and_push_remote.urllib.request.urlopen")
    def test_discover_repo_url_by_name_exact_match(
        self, mock_urlopen: MagicMock, mock_load: MagicMock
    ) -> None:
        payload = {
            "items": [
                {
                    "name": "It-s-whatever-",
                    "clone_url": "https://github.com/example/It-s-whatever-.git",
                }
            ]
        }
        response = MagicMock()
        response.__enter__.return_value = response
        response.__exit__.return_value = False
        mock_urlopen.return_value = response
        mock_load.return_value = payload

        self.assertEqual(
            discover_repo_url_by_name("It-s-whatever-"),
            "https://github.com/example/It-s-whatever-.git",
        )

    @patch("scripts.configure_and_push_remote.discover_repo_url_by_name")
    @patch("scripts.configure_and_push_remote.repo_name")
    def test_resolve_remote_url_falls_back_to_discovery(
        self, mock_repo_name: MagicMock, mock_discover: MagicMock
    ) -> None:
        mock_repo_name.return_value = "It-s-whatever-"
        mock_discover.return_value = "https://github.com/example/It-s-whatever-.git"

        original_owner = os.environ.pop("GITHUB_OWNER", None)
        original_remote = os.environ.pop("GIT_REMOTE_URL", None)
        try:
            self.assertEqual(
                resolve_remote_url(None),
                "https://github.com/example/It-s-whatever-.git",
            )
        finally:
            if original_owner is not None:
                os.environ["GITHUB_OWNER"] = original_owner
            if original_remote is not None:
                os.environ["GIT_REMOTE_URL"] = original_remote

    def test_discovery_headers_include_token(self) -> None:
        original_token = os.environ.get("GITHUB_TOKEN")
        os.environ["GITHUB_TOKEN"] = "abc123"
        try:
            headers = discovery_headers()
            self.assertEqual(headers.get("Authorization"), "Bearer abc123")
        finally:
            if original_token is None:
                os.environ.pop("GITHUB_TOKEN", None)
            else:
                os.environ["GITHUB_TOKEN"] = original_token


    def test_to_https_github_url_converts_ssh_forms(self) -> None:
        self.assertEqual(
            to_https_github_url("git@github.com:example/It-s-whatever-.git"),
            "https://github.com/example/It-s-whatever-.git",
        )
        self.assertEqual(
            to_https_github_url("ssh://git@github.com/example/It-s-whatever-.git"),
            "https://github.com/example/It-s-whatever-.git",
        )

    @patch("scripts.configure_and_push_remote.run")
    @patch("scripts.configure_and_push_remote.remote_url")
    def test_push_with_optional_token_uses_extraheader_for_github_https(
        self, mock_remote_url: MagicMock, mock_run: MagicMock
    ) -> None:
        mock_remote_url.return_value = "https://github.com/example/It-s-whatever-.git"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        original_token = os.environ.get("GH_TOKEN")
        os.environ["GH_TOKEN"] = "tok123"
        try:
            push_with_optional_token("origin", "work")
            cmd = mock_run.call_args.args[0]
            self.assertIn("http.https://github.com/.extraheader=AUTHORIZATION: bearer tok123", cmd)
        finally:
            if original_token is None:
                os.environ.pop("GH_TOKEN", None)
            else:
                os.environ["GH_TOKEN"] = original_token

    @patch("scripts.configure_and_push_remote.run")
    @patch("scripts.configure_and_push_remote.remote_url")
    def test_push_with_optional_token_normalizes_ssh_remote(
        self, mock_remote_url: MagicMock, mock_run: MagicMock
    ) -> None:
        mock_remote_url.return_value = "git@github.com:example/It-s-whatever-.git"
        mock_run.return_value = MagicMock(returncode=0, stderr="")

        original_token = os.environ.get("GH_TOKEN")
        os.environ["GH_TOKEN"] = "tok123"
        try:
            push_with_optional_token("origin", "work")
            first_cmd = mock_run.call_args_list[0].args[0]
            second_cmd = mock_run.call_args_list[-1].args[0]
            self.assertEqual(first_cmd, ["git", "remote", "set-url", "origin", "https://github.com/example/It-s-whatever-.git"])
            self.assertIn("http.https://github.com/.extraheader=AUTHORIZATION: bearer tok123", second_cmd)
        finally:
            if original_token is None:
                os.environ.pop("GH_TOKEN", None)
            else:
                os.environ["GH_TOKEN"] = original_token


if __name__ == "__main__":
    unittest.main()
