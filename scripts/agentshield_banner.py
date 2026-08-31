#!/usr/bin/env python3
"""AgentShield AI - premium terminal banner + intake menu.

Renders a cybersecurity/AI styled invocation screen: a layered AGENTSHIELD
wordmark (bright cyan upper body -> bright green lower body -> dim-green shadow),
a magenta "A I" mark, the security-yellow tagline, the
PREDICT / GOVERN / APPROVE / EXECUTE SAFELY / AUDIT workflow line, genuine
version metadata, and the numbered intake menu with per-mode guidance.

Design goals:
  * Navy-terminal cybersecurity aesthetic; wordmark cyan -> green, magenta A I.
  * 16-colour ANSI only (survives hosts that silently drop 24-bit truecolour).
  * Colour ON by default; opt out via --plain / NO_COLOR (clean-redirect path).
  * Fits within the detected width; centre-aligns the banner, left-aligns menu.
  * ANSI colour codes never affect visible-width maths (padding is computed on
    the raw text, colour is applied afterwards).
  * Graceful fallbacks: ASCII wordmark without Unicode, compact heading in a
    narrow terminal, plain text with no ANSI when colour is disabled.

Usage:
    python agentshield_banner.py [--plain] [--width N] [--wait]

    --wait  first prints "Press any key to continue" and blocks for one
            keypress, then reveals the banner. Safely skips the wait when stdin
            is not an interactive terminal, so it never hangs in a pipe.
"""

from __future__ import annotations

import os
import sys

# Ensure the block-drawing glyphs and ANSI colour survive on legacy Windows
# consoles (cp1252) so the banner renders identically wherever it is invoked.
try:
    sys.stdout.reconfigure(encoding="utf-8")  # type: ignore[attr-defined]
except (AttributeError, ValueError):
    pass

# On Windows, turn on ANSI escape interpretation (ENABLE_VIRTUAL_TERMINAL_
# PROCESSING) so the classic console / conhost renders the colour codes instead
# of printing them literally. Modern terminals already do this; the call is a
# harmless no-op there. Failure degrades gracefully to plain text.
if os.name == "nt":
    try:
        import ctypes

        _k32 = ctypes.windll.kernel32
        _k32.SetConsoleMode(_k32.GetStdHandle(-11), 7)
    except Exception:
        pass

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

# 16-colour ANSI SGR foreground codes. These are the most universally
# supported colour codes - rendered by virtually every terminal and CLI host,
# unlike 24-bit truecolour (38;2;r;g;b) which many hosts silently drop. Each
# constant is the SGR parameter string used by Painter.fg().
CYAN = "96"     # bright cyan  - headings / quick-start / reply
BLUE = "94"     # bright blue
VIOLET = "95"   # bright magenta
MAGENTA = "95"  # bright magenta - the "A I" mark
WHITE = "97"    # bright white
GREY = "90"     # bright black (grey) - descriptions
DGREY = "90"    # grey - rules / metadata
AMBER = "93"    # bright yellow - approve / reminder
ORANGE = "33"   # yellow (dimmer) - escalate (amber/orange, distinct from approve)
GREEN = "92"    # bright green - allow
RED = "91"      # bright red - deny
# PowerShell security-warning gold (tagline + workflow verbs / separators).
PSYELLOW = "93"  # bright yellow
PSGOLD = "33"    # yellow (dimmer) - separators

# VS Code "Dark+" style rainbow - one hue per 1-8 menu option, mapped to the
# nearest 16-colour ANSI code.
MENU_COLORS = [
    "94",  # [1] ASSESS       - blue
    "92",  # [2] OBSERVE      - green
    "95",  # [3] GOVERN       - magenta / violet
    "91",  # [4] RED-TEAM     - red
    "93",  # [5] RESPONSIBLE  - yellow
    "96",  # [6] VALIDATE     - cyan
    "33",  # [7] HTML report  - amber / orange
    "96",  # [8] guidance     - light cyan
]

# Layered wordmark: bright cyan upper body -> bright green lower body -> dim
# green shadow row, for a cyan/green depth effect on the navy background.
ROW_COLORS = ["96", "96", "96", "92", "92", "32"]

# ASCII-only wordmark fallback for terminals without Unicode block support.
WORDMARK_ASCII = [
    "  _   ___ ___ _  _ _____ ___ _  _ ___ ___ _    ___  ",
    " /_\\ / __| __| \\| |_   _/ __| || |_ _| __| |  |   \\ ",
    "/ _ \\ (_ | _|| .` | | | \\__ \\ __ || || _|| |__| |) |",
    "/_/ \\_\\___|___|_|\\_| |_| |___/_||_|___|___|____|___/ ",
]


def supports_color(force_plain: bool) -> bool:
    # Colour is ON by default. AgentShield's banner almost always runs with its
    # stdout piped (the Copilot CLI shell escape and agent tool calls both pipe),
    # so gating on sys.stdout.isatty() wrongly stripped every colour and printed
    # plain white text. Emit colour unless the user explicitly opts out via
    # --plain or NO_COLOR / AGENTSHIELD_NO_COLOR (the clean-redirect path).
    if force_plain:
        return False
    if os.environ.get("NO_COLOR") is not None:
        return False
    if os.environ.get("AGENTSHIELD_NO_COLOR") is not None:
        return False
    return True


def supports_unicode() -> bool:
    # Block-drawing glyphs need a Unicode-capable stdout. We reconfigure stdout
    # to UTF-8 at import time, but honour an explicit opt-out and probe the
    # encoding so legacy code pages fall back to the ASCII wordmark.
    if os.environ.get("AGENTSHIELD_ASCII") is not None:
        return False
    enc = (getattr(sys.stdout, "encoding", "") or "").lower()
    if "utf" in enc:
        return True
    try:
        "█".encode(enc or "ascii")
        return True
    except (UnicodeEncodeError, LookupError):
        return False


def detect_width(requested: int | None) -> int:
    # Explicit --width wins; otherwise detect the real terminal width and clamp
    # to a readable 60-100 columns. Falls back to WIDTH when detection fails.
    if requested is not None:
        return max(40, min(requested, 100))
    try:
        import shutil

        cols = shutil.get_terminal_size(fallback=(WIDTH, 24)).columns
    except Exception:
        cols = WIDTH
    return max(40, min(cols, 100))


def detect_version() -> str:
    # Use the genuine project version; never invent one. Read __version__ from
    # the agentshield package, falling back to a sane default.
    here = os.path.dirname(os.path.abspath(__file__))
    init = os.path.join(here, "..", "agentshield", "__init__.py")
    try:
        with open(init, encoding="utf-8") as fh:
            for line in fh:
                if line.strip().startswith("__version__"):
                    return line.split("=", 1)[1].strip().strip('"').strip("'")
    except OSError:
        pass
    return "1.0.0"


class Painter:
    def __init__(self, enabled: bool) -> None:
        self.enabled = enabled

    def fg(self, text: str, code: str, bold: bool = False) -> str:
        if not self.enabled:
            return text
        b0 = "1;" if bold else ""
        return f"\x1b[{b0}{code}m{text}\x1b[0m"


def centre(text: str, width: int = WIDTH) -> str:
    pad = max(0, (width - len(text)) // 2)
    return " " * pad + text


def rule(paint: Painter, width: int = WIDTH) -> str:
    return paint.fg("-" * width, DGREY)


def render(width: int, plain: bool) -> str:
    paint = Painter(supports_color(plain))
    unicode_ok = supports_unicode()
    version = detect_version()
    out: list[str] = []
    out.append("")

    # Wordmark: full Unicode block art when it fits and Unicode is available;
    # ASCII wordmark when Unicode is unavailable; compact heading when the
    # terminal is too narrow for the block art.
    block = WORDMARK if unicode_ok else WORDMARK_ASCII
    block_w = max(len(r) for r in block)
    dot = "·" if unicode_ok else "-"
    if width < block_w + 2:
        # Compact banner for narrow terminals.
        out.append(centre(paint.fg("A G E N T S H I E L D", "96", bold=True), width))
    else:
        left = max(0, (width - block_w) // 2)
        colors = ROW_COLORS if unicode_ok else ["96", "96", "92", "92"]
        for row, color in zip(block, colors):
            out.append(" " * left + paint.fg(row, color, bold=True))

    # "A I" mark in magenta.
    out.append("")
    out.append(centre(paint.fg("A  I", MAGENTA, bold=True), width))

    # Tagline in PowerShell security-warning yellow.
    out.append("")
    out.append(centre(paint.fg("The Security Control Plane for the Agentic Enterprise", PSYELLOW, bold=True), width))

    # Workflow line: security-yellow words, muted separator dots.
    words = ["PREDICT", "GOVERN", "APPROVE", "EXECUTE SAFELY", "AUDIT"]
    sep_raw = f"  {dot}  "
    raw = sep_raw.join(words)
    pad = max(0, (width - len(raw)) // 2)
    colored = paint.fg(sep_raw, PSGOLD).join(paint.fg(w, PSYELLOW, bold=True) for w in words)
    out.append("")
    out.append(" " * pad + colored)

    # Metadata + version (genuine project version).
    out.append("")
    out.append(centre(paint.fg(f"Deterministic governance for AI agents  {dot}  Simulation-first", DGREY), width))
    out.append(centre(paint.fg(f"BlastRadius: capability & impact  {dot}  ChangeShield: safe change", PSGOLD), width))
    out.append(centre(paint.fg(f"v{version}", GREY), width))

    out.append("")
    out.append(rule(paint, width))

    # Intake menu.
    def item(num: str, badge_rgb, title: str, desc: str) -> None:
        out.append(
            "  " + paint.fg("[" + num + "]", badge_rgb, bold=True) + " "
            + paint.fg(title, badge_rgb, bold=True)
        )
        # Wrap long descriptions cleanly to the content width, keeping the
        # hanging indent aligned under the first word.
        indent = "       "
        prefix = "> "
        avail = max(20, width - len(indent) - len(prefix))
        words_d = desc.split()
        line = ""
        wrapped: list[str] = []
        for w in words_d:
            if line and len(line) + 1 + len(w) > avail:
                wrapped.append(line)
                line = w
            else:
                line = f"{line} {w}".strip()
        if line:
            wrapped.append(line)
        for i, seg in enumerate(wrapped):
            lead = prefix if i == 0 else "  "
            out.append(indent + paint.fg(lead + seg, GREY))

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
         "AgentShield will select the appropriate mode and identify the required evidence.")

    out.append("")
    out.append(rule(paint, width))
    out.append("")

    # Decision badge legend.
    badges = (
        paint.fg("[ ALLOW ]", GREEN) + " "
        + paint.fg("[ TRANSFORM ]", CYAN) + " "
        + paint.fg("[ APPROVE ]", AMBER) + " "
        + paint.fg("[ ESCALATE ]", ORANGE) + " "
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
    requested: int | None = None
    if "--width" in argv:
        try:
            requested = int(argv[argv.index("--width") + 1])
        except (ValueError, IndexError):
            requested = None
    # Auto-detect terminal width when not explicitly requested.
    width = detect_width(requested)
    if wait:
        _wait_gate(plain)
    sys.stdout.write(render(width, plain) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
