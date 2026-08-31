#!/usr/bin/env python3
"""Render the AgentShield invocation banner to a coloured PNG.

The Copilot CLI tool-output panel strips ANSI colour, so an agent-run banner
shows plain text there. This renderer produces a faithful *image* of the same
banner - dark navy background, cyan-to-green wordmark, magenta "A I", security-
yellow tagline/workflow, rainbow 1-8 menu, and colour-coded runtime badges - so
the branded screen can be displayed inline where ANSI cannot.

Purely presentational: it imports nothing from the governance engine and changes
no policy, assessment, or report behaviour. It mirrors the exact text and colour
intent of scripts/agentshield_banner.py.

Usage:
    python scripts/agentshield_banner_image.py [OUTPUT.png] [--scale N]
"""

from __future__ import annotations

import os
import sys

try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:  # pragma: no cover - dependency guard
    sys.stderr.write("Pillow is required: pip install Pillow\n")
    raise SystemExit(2)

# ---- Palette (RGB) --------------------------------------------------------
BG = (11, 15, 34)          # deep navy background
CYAN = (56, 225, 255)      # wordmark upper / headings / reply
GREEN = (52, 211, 153)     # wordmark lower / ALLOW / OBSERVE
DGREEN = (22, 138, 105)    # wordmark shadow row
LCYAN = (128, 232, 255)    # option 8 guidance
BLUE = (99, 140, 255)      # option 1 ASSESS
MAGENTA = (236, 72, 153)   # "A I" / option 3 GOVERN
RED = (244, 84, 84)        # option 4 RED-TEAM / DENY
YELLOW = (245, 206, 74)    # tagline / workflow / option 5 / APPROVE
AMBER = (245, 168, 52)     # option 7 / ESCALATE / reminder
WHITE = (238, 242, 255)    # quick-start command
GREY = (150, 162, 188)     # descriptions / metadata
DGREY = (96, 108, 138)     # rules / separators / version

# Per-row wordmark colours: cyan upper body -> green lower -> dim-green shadow.
ROW_COLORS = [CYAN, CYAN, CYAN, GREEN, GREEN, DGREEN]

WORDMARK = [
    " █████╗  ██████╗ ███████╗███╗   ██╗████████╗███████╗██╗  ██╗██╗███████╗██╗     ██████╗",
    "██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝██╔════╝██║  ██║██║██╔════╝██║     ██╔══██╗",
    "███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║   ███████╗███████║██║█████╗  ██║     ██║  ██║",
    "██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║   ╚════██║██╔══██║██║██╔══╝  ██║     ██║  ██║",
    "██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║   ███████║██║  ██║██║███████╗███████╗██████╔╝",
    "╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝╚══════╝╚══════╝╚═════╝",
]

MENU = [
    (BLUE, "[1] ASSESS an agent / system",
     "> Share an agent file, MCP/tool manifest, or prompt -> findings."),
    (GREEN, "[2] OBSERVE a proposed action",
     "> Describe an action -> predicted impact + the decision it WOULD get."),
    (MAGENTA, "[3] GOVERN - deterministic policy + approval",
     "> Run the 7 gates -> ALLOW/TRANSFORM/APPROVE/ESCALATE/DENY + binding."),
    (RED, "[4] RED-TEAM (Gate R, simulation-only)",
     "> Static probe: ASR, refusal, leakage, injection-resistance x 9 families."),
    (YELLOW, "[5] RESPONSIBLE AI assessment",
     "> Score 6 RAI pillars -> RAI-PASS / RAI-WARN / RAI-BLOCK (advisory)."),
    (CYAN, "[6] VALIDATE an outcome",
     "> Compare an approved action + plan vs what happened; flag deviation."),
    (AMBER, "[7] Generate an HTML evidence report",
     "> From an existing assessment (explicit request only)."),
    (LCYAN, "[8] Not sure? Describe your situation",
     "> AgentShield will select the appropriate mode and identify the evidence."),
]

BADGES = [
    ("[ ALLOW ]", GREEN), ("[ TRANSFORM ]", CYAN), ("[ APPROVE ]", YELLOW),
    ("[ ESCALATE ]", AMBER), ("[ DENY ]", RED),
]


def detect_version() -> str:
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


def _font(names: list[str], size: int) -> ImageFont.FreeTypeFont:
    for n in names:
        for path in (n, os.path.join(r"C:\Windows\Fonts", n)):
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
    return ImageFont.load_default()


def render(out_path: str, scale: int = 2) -> str:
    version = detect_version()
    # Base cell metrics (monospace); scaled up for a crisp image.
    fs = 15 * scale
    reg = _font(["consola.ttf", "CascadiaMono.ttf", "cour.ttf"], fs)
    bold = _font(["consolab.ttf", "CascadiaMono.ttf", "courbd.ttf"], fs)
    wf = _font(["consolab.ttf", "consola.ttf"], int(15.2 * scale))

    # Cell size from the font metrics of a wide block glyph.
    tmp = Image.new("RGB", (10, 10))
    d0 = ImageDraw.Draw(tmp)
    bbox = d0.textbbox((0, 0), "█", font=wf)
    cw = bbox[2] - bbox[0]
    ch = int((bbox[3] - bbox[1]) * 1.0)
    line_h = int(fs * 1.55)

    cols = max(len(r) for r in WORDMARK)
    margin = 5 * scale * 6
    width = margin * 2 + cols * cw
    # Count the rendered lines to size the canvas height.
    n_lines = (
        len(WORDMARK) + 1              # wordmark + AI
        + 2 + 2 + 3                    # tagline, workflow, metadata+caps+version (blocks)
        + 2                            # rule + heading
        + len(MENU) * 2                # menu options
        + 2 + 1 + 2 + 1                # rule, badges, quick/reminder, reply
        + 8                           # blank-line spacing
    )
    height = int(margin * 1.4) + int(n_lines * line_h) + margin
    img = Image.new("RGB", (width, height), BG)
    draw = ImageDraw.Draw(img)

    y = int(margin * 0.7)

    def centre_x(text: str, font) -> int:
        w = draw.textbbox((0, 0), text, font=font)[2]
        return max(margin, (width - w) // 2)

    # Wordmark (each row centred as a block, coloured per row). Draw the rows
    # with a pitch equal to the font's true line height so the solid block
    # glyphs in adjacent rows abut instead of leaving horizontal seams. A tiny
    # (2%) overlap guarantees no hairline gaps between rows.
    asc, desc = wf.getmetrics()
    wm_pitch = max(1, int((asc + desc) * 0.98))
    block_px = cols * cw
    left = (width - block_px) // 2
    for row, color in zip(WORDMARK, ROW_COLORS):
        draw.text((left, y), row, font=wf, fill=color)
        y += wm_pitch
    y += int(line_h * 0.9)

    # A I
    draw.text((centre_x("A  I", bold), y), "A  I", font=bold, fill=MAGENTA)
    y += int(line_h * 1.3)

    # Tagline
    tag = "The Security Control Plane for the Agentic Enterprise"
    draw.text((centre_x(tag, bold), y), tag, font=bold, fill=YELLOW)
    y += int(line_h * 1.2)

    # Workflow line (yellow words, grey dots).
    words = ["PREDICT", "GOVERN", "APPROVE", "EXECUTE SAFELY", "AUDIT"]
    sep = "  ·  "
    full = sep.join(words)
    x = centre_x(full, bold)
    for i, w in enumerate(words):
        draw.text((x, y), w, font=bold, fill=YELLOW)
        x += draw.textbbox((0, 0), w, font=bold)[2]
        if i < len(words) - 1:
            draw.text((x, y), sep, font=bold, fill=DGREY)
            x += draw.textbbox((0, 0), sep, font=bold)[2]
    y += int(line_h * 1.25)

    # Metadata + version.
    meta = "Deterministic governance for AI agents  ·  Simulation-first"
    draw.text((centre_x(meta, reg), y), meta, font=reg, fill=GREY)
    y += line_h
    caps = "BlastRadius: capability & impact  ·  ChangeShield: safe change"
    draw.text((centre_x(caps, reg), y), caps, font=reg, fill=YELLOW)
    y += line_h
    ver = f"v{version}"
    draw.text((centre_x(ver, reg), y), ver, font=reg, fill=DGREY)
    y += int(line_h * 1.2)

    # Rule.
    rule_chars = width - margin * 2
    draw.line([(margin, y + ch // 2), (width - margin, y + ch // 2)], fill=DGREY, width=max(1, scale))
    y += int(line_h * 1.1)

    # Menu heading.
    draw.text((margin, y), "What would you like to do?", font=bold, fill=CYAN)
    y += int(line_h * 1.3)

    # Menu items.
    for color, title, desc in MENU:
        draw.text((margin, y), title, font=bold, fill=color)
        y += line_h
        draw.text((margin + cw * 5, y), desc, font=reg, fill=GREY)
        y += int(line_h * 1.05)
    y += int(line_h * 0.3)

    # Rule.
    draw.line([(margin, y + ch // 2), (width - margin, y + ch // 2)], fill=DGREY, width=max(1, scale))
    y += int(line_h * 1.1)

    # Runtime decision badges.
    x = margin
    label = "Runtime decisions:  "
    draw.text((x, y), label, font=reg, fill=DGREY)
    x += draw.textbbox((0, 0), label, font=reg)[2]
    for text, color in BADGES:
        draw.text((x, y), text, font=bold, fill=color)
        x += draw.textbbox((0, 0), text + " ", font=bold)[2]
    y += int(line_h * 1.4)

    # Quick start.
    x = margin
    qs = "Quick start: "
    draw.text((x, y), qs, font=bold, fill=CYAN)
    x += draw.textbbox((0, 0), qs, font=bold)[2]
    draw.text((x, y), "Assess ~/.copilot/Agents/dr-dnd.agent.md", font=reg, fill=WHITE)
    y += line_h
    x = margin
    rm = "Reminder: "
    draw.text((x, y), rm, font=bold, fill=AMBER)
    x += draw.textbbox((0, 0), rm, font=bold)[2]
    draw.text((x, y), "missing evidence lowers confidence - it is never invented.", font=reg, fill=GREY)
    y += int(line_h * 1.3)

    # Reply.
    draw.text((margin, y), "Reply 1-8, or just describe your goal.", font=bold, fill=CYAN)
    y += line_h

    # Trim any surplus vertical space to the actual content (tight bottom pad).
    final_h = min(height, y + int(margin * 0.7))
    img = img.crop((0, 0, width, final_h))
    img.save(out_path)
    return out_path


def main(argv: list[str]) -> int:
    scale = 3
    if "--scale" in argv:
        try:
            scale = int(argv[argv.index("--scale") + 1])
        except (ValueError, IndexError):
            scale = 3
    positional = [a for a in argv if not a.startswith("--") and not a.isdigit()]
    here = os.path.dirname(os.path.abspath(__file__))
    default = os.path.join(here, "..", "docs", "agentshield-banner.png")
    out = positional[0] if positional else default
    path = render(out, scale=scale)
    sys.stdout.write(os.path.abspath(path) + "\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
