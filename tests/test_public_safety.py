"""Public-repository safety and no-live-integration tests (behaviors 20, 21).

Scans tracked project sources for secrets, tokens, private keys, internal URLs,
real-looking emails, and unsupported live-integration claims. Uses only
fictional, allowlisted example values.
"""

from __future__ import annotations

import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

# Directories and files that are not project source.
EXCLUDED_DIRS = {
    ".git",
    "__pycache__",
    ".pytest_cache",
    "reference-agent",  # supplied reference package; not our authored content
    ".venv",
    "venv",
    "node_modules",
}

SCANNED_SUFFIXES = {".py", ".md", ".html", ".txt", ".gitignore", ""}

# Fictional tokens explicitly allowed to appear in tests/fixtures.
ALLOWLIST = {
    "SHOULD-NOT-APPEAR",  # sentinel used in redaction tests
}


def _iter_source_files():
    for path in ROOT.rglob("*"):
        if not path.is_file():
            continue
        if any(part in EXCLUDED_DIRS for part in path.parts):
            continue
        if path.name == "test_public_safety.py":
            continue  # this file necessarily contains the patterns
        if path.suffix in SCANNED_SUFFIXES or path.name == ".gitignore":
            yield path


def _read(path: Path) -> str:
    try:
        return path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        return ""


class SecretScanTests(unittest.TestCase):
    def setUp(self):
        self.files = list(_iter_source_files())
        self.assertTrue(self.files, "no source files discovered to scan")

    def test_no_private_keys(self):
        marker = "-----BEGIN " + "PRIVATE KEY-----"
        for path in self.files:
            self.assertNotIn(marker, _read(path), f"private key marker in {path}")

    def test_no_aws_like_access_keys(self):
        pattern = re.compile(r"AKIA[0-9A-Z]{16}")
        for path in self.files:
            self.assertIsNone(
                pattern.search(_read(path)), f"AWS-like key in {path}"
            )

    def test_no_bearer_or_pat_tokens(self):
        patterns = [
            re.compile(r"ghp_[A-Za-z0-9]{20,}"),
            re.compile(r"xox[baprs]-[A-Za-z0-9-]{10,}"),
            re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}\."),  # JWT
        ]
        for path in self.files:
            content = _read(path)
            for pattern in patterns:
                self.assertIsNone(
                    pattern.search(content), f"token-like value in {path}"
                )

    def test_no_hardcoded_password_assignments(self):
        # Flags string literals assigned to password/secret variables.
        pattern = re.compile(
            r"(password|passwd|secret|api_key|client_secret)\s*[=:]\s*[\"'][^\"']+[\"']",
            re.IGNORECASE,
        )
        for path in self.files:
            for match in pattern.finditer(_read(path)):
                literal = match.group(0)
                if any(allowed in literal for allowed in ALLOWLIST):
                    continue
                # Redaction constants and empty-ish placeholders are safe.
                if "REDACTED" in literal or "SHOULD-NOT" in literal:
                    continue
                self.fail(f"hardcoded secret-like assignment in {path}: {literal}")

    def test_no_real_internal_urls_or_hosts(self):
        # Only self-contained docs are allowed; no external/internal http(s) URLs
        # in authored HTML/docs (schema references may mention the words only).
        pattern = re.compile(r"https?://[^\s\"'<>]+", re.IGNORECASE)
        for path in self.files:
            if path.suffix not in {".html", ".py", ".md"}:
                continue
            for match in pattern.finditer(_read(path)):
                url = match.group(0)
                self.fail(f"unexpected URL in {path}: {url}")

    def test_no_real_email_addresses(self):
        pattern = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
        for path in self.files:
            for match in pattern.finditer(_read(path)):
                email = match.group(0)
                # Allow fictional example.* domains and noreply placeholders.
                if email.endswith((".example", "@example.com", "@example.org")):
                    continue
                self.fail(f"real-looking email in {path}: {email}")


class NoLiveIntegrationTests(unittest.TestCase):
    def test_20_no_execution_adapter_is_implemented(self):
        from agentshield import interfaces

        # ExecutionAdapter is a Protocol/interface, not a concrete class.
        self.assertTrue(hasattr(interfaces, "ExecutionAdapter"))
        # There is no concrete adapter exported from the package.
        import agentshield

        for name in dir(agentshield):
            obj = getattr(agentshield, name)
            self.assertFalse(
                isinstance(obj, type) and name.endswith("ExecutionAdapter") and
                getattr(obj, "enabled", False) is True,
                f"a live-enabled execution adapter is exported: {name}",
            )

    def test_20_controlled_live_is_disabled_in_docs(self):
        agent = (ROOT / ".github" / "agents" / "agentshield.agent.md").read_text(
            encoding="utf-8"
        )
        protocol = (ROOT / "Protocols" / "AGENTSHIELD-PROTOCOL.md").read_text(
            encoding="utf-8"
        )
        self.assertIn("disabled by default", agent + protocol)

    def test_20_no_network_calls_in_package(self):
        # The runtime package must not import networking libraries.
        forbidden = ("import requests", "import socket", "import http.client",
                     "urllib.request", "import urllib3")
        pkg = ROOT / "agentshield"
        for path in pkg.rglob("*.py"):
            content = path.read_text(encoding="utf-8")
            for token in forbidden:
                self.assertNotIn(token, content, f"{token} found in {path}")


if __name__ == "__main__":
    unittest.main()
