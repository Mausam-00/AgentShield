#!/usr/bin/env python3
"""AgentShield AI - premium terminal banner + intake menu.

Renders a cybersecurity/AI styled invocation screen: a gradient AGENTSHIELD
wordmark (cyan -> electric blue -> violet), a magenta "A I" mark, the tagline,
the PREDICT / GOVERN / APPROVE / EXECUTE SAFELY / AUDIT workflow line, version
metadata, and the numbered intake menu with per-mode guidance.

Design goals:
  * Deep-black terminal aesthetic, brand colours cyan/blue/violet/magenta.
  * Amber = warning/approval, green = success, red = blocked/denied.
  * Fits within 80 visible columns; centre-aligns the banner, left-aligns menu.
  * ANSI colour codes never affect visible-width maths (padding is computed on
    the raw text, colour is applied afterwards).
  * Graceful fallback: no colour when NO_COLOR is set, when output is not a TTY,
    or when --plain is passed. All text, spacing, and labels are preserved.

Usage:
    python agentshield_banner.py [--plain] [--width N] [--wait]

    --wait  first prints "Press any key to continue" and blocks for one
            keypress, then reveals the banner. Safely skips the wait when stdin
            is not an interactive terminal, so it never hangs in a pipe.
"""

from __future__ import annotations

import os
import sys

WIDTH = 88

# Filled block wordmark (figlet "ANSI Shadow"), 6 rows, 87 cols wide.
# Solid block glyphs so the letters render filled with colour, not outlined.
WORDMARK = [
    " █████╗  ██████╗ ███████╗███╗   ██╗████████╗███████╗██╗  ██╗██╗███████╗██╗     ██████╗",
    "██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔════╝██║  ██║██║██╔════╝██║     ██╔══██╗",
    "███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ███████╗███████║██║█████╗  ██║     ██║  ██║",
    "██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ╚════██║██╔══██║██║██╔══╝  ██║     ██║  ██║",
    "██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ███████║██║  ██║██║███████╗███████╗██████╔╝",
    "╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝",
]

# Truecolor brand palette (R, G, B).
CYAN = (56, 225, 255)
BLUE = (79, 124, 255)
VIOLET = (139, 92, 246)
MAGENTA = (236, 72, 153)
WHITE = (240, 244, 255)
GREY = (140, 152, 176)
DGREY = (96, 106, 128)
AMBER = (245, 158, 11)
GREEN = (52, 211, 153)
RED = (239, 68, 68)
# PowerShell security-warning yellow (the "run only scripts you trust" prompt).
PSYELLOW = (240, 210, 60)
PSGOLD = (196, 156, 0)

# VS Code "Dark+" syntax palette - one hue per menu option for a rainbow,
# code-editor look on the 1-8 intake badges.
VSC_BLUE = (86, 156, 214)    # keyword
VSC_TEAL = (78, 201, 176)    # type / class
VSC_PURPLE = (197, 134, 192)  # control flow
VSC_RED = (209, 105, 105)    # regexp
VSC_YELLOW = (220, 220, 170)  # function
VSC_LGREEN = (181, 206, 168)  # numeric constant
VSC_ORANGE = (206, 145, 120)  # string
VSC_LBLUE = (156, 220, 254)  # variable
MENU_COLORS = [
    VSC_BLUE, VSC_TEAL, VSC_PURPLE, VSC_RED,
    VSC_YELLOW, VSC_LGREEN, VSC_ORANGE, VSC_LBLUE,
]

# Filled wordmark gradient: Matrix / emerald green, light -> deep. Tuned to glow
# against the classic PowerShell navy background (#012456).
ROW_COLORS = [
    (124, 255, 178),
    (74, 255, 150),
    (0, 255, 106),
    (0, 230, 118),
    (0, 201, 99),
    (0, 168, 83),
]


def supports_color(force_plain: bool) -> bool:
    if force_plain:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("AGENTSHIELD_NO_COLOR") is not None:
        return False
    return sys.stdout.isatty()


class Painter:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def fg(self, text: str, rgb: tuple[int, int, int], bold: bool = False) -> str:
        if not self.enabled:
            return text
        r, g, b = rgb
        b0 = "1;" if bold else ""
        return f"\x1b[{b0}38;2;{r};{g};{b}m{text}\x1b[0m"


def centre(text: str, width: int = WIDTH) -> str:
    pad = max(0, (width - len(text)) // 2)
    return " " * pad + text


def rule(paint: Painter, width: int = WIDTH) -> str:
    return paint.fg("-" * width, DGREY)


def render(width: int, plain: bool) -> str:
    paint = Painter(supports_color(plain))
    out: list[str] = []
    out.append("")

    # Wordmark, centred as a block using the widest row.
    block_w = max(len(r) for r in WORDMARK)
    left = max(0, (width - block_w) // 2)
    for row, color in zip(WORDMARK, ROW_COLORS):
        out.append(" " * left + paint.fg(row, color, bold=True))

    # "A I" mark in magenta.
    out.append("")
    out.append(centre(paint.fg("A  I", MAGENTA, bold=True), width))

    # Tagline in PowerShell security-warning yellow.
    out.append("")
    out.append(centre(paint.fg("The Security Control Plane for the Agentic Enterprise", PSYELLOW, bold=True), width))

    # Workflow line: security-yellow words, muted-gold separator dots.
    words = ["PREDICT", "GOVERN", "APPROVE", "EXECUTE SAFELY", "AUDIT"]
    sep_raw = "  .  "
    raw = sep_raw.join(words)
    pad = max(0, (width - len(raw)) // 2)
    colored = paint.fg(sep_raw, PSGOLD).join(paint.fg(w, PSYELLOW, bold=True) for w in words)
    out.append("")
    out.append(" " * pad + colored)

    # Metadata + version.
    out.append("")
    out.append(centre(paint.fg("Deterministic governance for AI agents  .  simulation-first", DGREY), width))
    out.append(centre(paint.fg("v1.0", GREY), width))

    out.append("")
    out.append(rule(paint, width))

    # Intake menu.
    def item(num: str, badge_rgb, title: str, desc: str) -> None:
        out.append(
            "  " + paint.fg("[" + num + "]", badge_rgb, bold=True) + " "
            + paint.fg(title, badge_rgb, bold=True)
        )
        out.append("       " + paint.fg("> " + desc, GREY))

    out.append("")
    out.append("  " + paint.fg("What would you like to do?", CYAN, bold=True))
    out.append("")
    item("1", MENU_COLORS[0], "ASSESS an agent / system",
         "Share an agent file, MCP/tool manifest, or prompt -> findings.")
    item("2", MENU_COLORS[1], "OBSERVE a proposed action",
         "Describe an action -> predicted impact + the decision it WOULD get.")
    item("3", MENU_COLORS[2], "GOVERN - deterministic policy + approval",
         "Run the 7 gates -> ALLOW/TRANSFORM/APPROVE/ESCALATE/DENY + binding.")
    item("4", MENU_COLORS[3], "RED-TEAM (Gate R, simulation-only)",
         "Static probe: ASR, refusal, leakage, injection-resistance x 9 families.")
    item("5", MENU_COLORS[4], "RESPONSIBLE AI assessment",
         "Score 6 RAI pillars -> RAI-PASS / RAI-WARN / RAI-BLOCK (advisory).")
    item("6", MENU_COLORS[5], "VALIDATE an outcome",
         "Compare an approved action + plan vs what happened; flag deviation.")
    item("7", MENU_COLORS[6], "Generate an HTML evidence report",
         "From an existing assessment (explicit request only).")
    item("8", MENU_COLORS[7], "Not sure? Describe your situation",
         "I'll pick the right mode and say exactly what to provide.")

    out.append("")
    out.append(rule(paint, width))
    out.append("")

    # Decision badge legend.
    badges = (
        paint.fg("[ ALLOW ]", GREEN) + " "
        + paint.fg("[ TRANSFORM ]", CYAN) + " "
        + paint.fg("[ APPROVE ]", AMBER) + " "
        + paint.fg("[ ESCALATE ]", AMBER) + " "
        + paint.fg("[ DENY ]", RED)
    )
    out.append("  " + paint.fg("Runtime decisions:", DGREY) + " " + badges)
    out.append("")

    # Quick-start + evidence reminder.
    out.append(
        "  " + paint.fg("Quick start:", CYAN, bold=True) + " "
        + paint.fg("Assess ~/.copilot/Agents/dr-dnd.agent.md", WHITE)
    )
    out.append(
        "  " + paint.fg("Reminder:", AMBER, bold=True) + " "
        + paint.fg("missing evidence lowers confidence - it is never invented.", GREY)
    )
    out.append("")
    out.append("  " + paint.fg("Reply 1-8, or just describe your goal.", CYAN))
    out.append("")
    return "\n".join(out)


def _read_single_key() -> None:
    """Block until the user presses one key. No-op if stdin is not a TTY.

    Uses msvcrt on Windows and termios/tty on POSIX. Any failure (no TTY,
    unsupported platform, redirected stdin) degrades to an immediate return so
    the banner is never blocked from rendering.
    """
    if not sys.stdin.isatty():
        return
    try:
        import msvcrt  # type: ignore
        msvcrt.getch()
        return
    except Exception:
        pass
    try:
        import termios
        import tty
        fd = sys.stdin.fileno()
        old = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            sys.stdin.read(1)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old)
    except Exception:
        return


def _wait_gate(plain: bool) -> None:
    """Render the 'Press any key to continue' gate, then wait for a keypress."""
    paint = Painter(supports_color(plain))
    prompt = paint.fg("  > Press any key to continue ...", CYAN, bold=True)
    sys.stdout.write("\n" + prompt + "\n")
    sys.stdout.flush()
    _read_single_key()
    # Clear the screen for a clean reveal when we control a real terminal.
    if not plain and sys.stdout.isatty():
        sys.stdout.write("\x1b[2J\x1b[H")
        sys.stdout.flush()


def main(argv: list[str]) -> int:
    plain = "--plain" in argv
    wait = "--wait" in argv
    width = WIDTH
    if "--width" in argv:
        try:
            width = int(argv[argv.index("--width") + 1])
        except (ValueError, IndexError):
            width = WIDTH
    # Narrow-terminal courtesy: keep content readable.
    width = max(60, min(width, 100))
    if wait:
        _wait_gate(plain)
    sys.stdout.write(render(width, plain) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
