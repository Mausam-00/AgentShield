"""Rendering tests for the PowerShell welcome banner (scripts/agentshield_banner.ps1).

The banner is the primary on-invocation screen. These tests assert the boxed
layout invariants so accidental edits cannot silently break alignment or drop
the intake menu / evidence panel. They shell out to PowerShell (or pwsh) and
skip cleanly on hosts where neither is available.
"""

from __future__ import annotations

import shutil
import subprocess
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "agentshield_banner.ps1"

# Box frame characters (single-cell BMP glyphs, so len() == display width).
_FRAME_PREFIXES = ("\u2551", "\u2554", "\u255a", "\u2560")  # ║ ╔ ╚ ╠
_BOX_WIDTH = 80  # 78 inner + two vertical borders


def _find_pwsh() -> str | None:
    for exe in ("pwsh", "powershell"):
        if shutil.which(exe):
            return exe
    return None


def _run(args: list[str]) -> str:
    exe = _find_pwsh()
    assert exe is not None
    proc = subprocess.run(
        [exe, "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(SCRIPT), *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=60,
    )
    assert proc.returncode == 0, proc.stderr
    return proc.stdout


@unittest.skipIf(_find_pwsh() is None, "no PowerShell interpreter available")
class TestBannerPs1(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SCRIPT.exists(), f"missing {SCRIPT}")
        self.plain = _run(["-Plain"])
        self.lines = self.plain.splitlines()

    def test_every_framed_line_is_exactly_box_width(self) -> None:
        framed = [ln for ln in self.lines if ln.startswith(_FRAME_PREFIXES)]
        self.assertGreater(len(framed), 20)
        for ln in framed:
            self.assertEqual(
                len(ln), _BOX_WIDTH, f"misaligned ({len(ln)} != {_BOX_WIDTH}): {ln!r}"
            )

    def test_has_top_and_bottom_borders(self) -> None:
        self.assertTrue(any(ln.startswith("\u2554") for ln in self.lines))  # ╔
        self.assertTrue(any(ln.startswith("\u255a") for ln in self.lines))  # ╚

    def test_all_eight_menu_modes_present(self) -> None:
        for token in (
            "1  ASSESS",
            "2  OBSERVE",
            "3  GOVERN",
            "4  RED-TEAM",
            "5  RESPONSIBLE",
            "6  VALIDATE",
            "7  REPORT",
            "8  NOT SURE",
        ):
            self.assertIn(token, self.plain, f"menu entry missing: {token}")

    def test_runtime_decision_badges_present(self) -> None:
        for badge in ("[ ALLOW ]", "[ TRANSFORM ]", "[ APPROVE ]", "[ ESCALATE ]", "[ DENY ]"):
            self.assertIn(badge, self.plain)

    def test_assurance_not_authorization_panel(self) -> None:
        # Assurance posture must stay separate from authorization in the banner.
        self.assertIn("ASSURANCE \u2260 AUTHORIZATION", self.plain)
        self.assertIn("PASS is not certification", self.plain)
        self.assertIn("never invented", self.plain)
        self.assertIn("AI advises", self.plain)

    def test_workflow_and_tagline_present(self) -> None:
        self.assertIn("PREDICT", self.plain)
        self.assertIn("EXECUTE SAFELY", self.plain)
        self.assertIn("The Security Control Plane for the Agentic Enterprise", self.plain)

    def test_plain_mode_has_no_ansi_escapes(self) -> None:
        self.assertNotIn("\x1b[", self.plain)

    def test_colour_mode_emits_truecolor_sgr(self) -> None:
        coloured = _run([])
        self.assertIn("\x1b[38;2;", coloured)  # 24-bit foreground SGR


if __name__ == "__main__":
    unittest.main()
