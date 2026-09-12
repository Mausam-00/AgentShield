"""AgentShield remediate CLI: fix an assessed agent definition, then re-assess.

This is the "make findings into action" companion to the ASSESS engine. It:

  1. assesses an agent definition (the same engine the website "Run the Engine"
     panel uses),
  2. applies the deterministic, text-only remediation (``agentshield.remediate``),
     writing a corrected copy of the definition, and
  3. re-assesses the corrected copy so you can see the posture/score move.

Typical loop:

    python scripts/agentshield_remediate.py examples/showcase/infra-bot.agent.md

writes ``examples/showcase/infra-bot.remediated.agent.md`` and prints a
before -> after summary. Upload either file into the engine to reproduce the
numbers. The remediation never executes the agent, never contacts a network,
and only rewrites the definition text it was given.

Honesty note: a static assessment never certifies (PASS). Remediation clears
findings and, where it substantively implements a control, records an
evidence-cited attestation that raises the *score* while the *posture* stays
WARN. Attested is not independently tested.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentshield import assess_agent_file, remediate  # noqa: E402


def _default_out(path: Path) -> Path:
    # foo.agent.md -> foo.remediated.agent.md ; bar.md -> bar.remediated.md
    name = path.name
    if name.endswith(".agent.md"):
        stem = name[: -len(".agent.md")]
        return path.with_name(f"{stem}.remediated.agent.md")
    return path.with_name(f"{path.stem}.remediated{path.suffix}")


def _print_assessment(label: str, assessment) -> None:
    a = assessment.assurance
    print(f"  {label:8} : {a.posture.value:5} score {a.score}/100  "
          f"coverage {a.coverage}  confidence {a.confidence.value}  "
          f"({len(assessment.findings)} findings)")
    for f in assessment.findings:
        print(f"             - [{f.severity.value:8}] {f.id}  {f.title}")


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(
        description="Remediate an agent definition and re-assess it."
    )
    ap.add_argument("agent", help="Path to the agent definition (.md).")
    ap.add_argument("-o", "--out", help="Where to write the remediated definition "
                    "(default: <name>.remediated.agent.md).")
    ap.add_argument("--diff", help="Also write the unified remediation diff here.")
    ap.add_argument("--version", default="1.0.0",
                    help="Version to insert when the definition is unversioned.")
    ap.add_argument("--resolve-root", action="append", default=[],
                    help="Extra base directory for resolving referenced assets.")
    args = ap.parse_args(argv)

    src = Path(args.agent)
    if not src.exists():
        print(f"error: file not found: {src}", file=sys.stderr)
        return 2

    out = Path(args.out) if args.out else _default_out(src)

    before = assess_agent_file(str(src), resolve_roots=args.resolve_root)
    result = remediate(before, version=args.version)

    if not result.changed:
        print(f"AgentShield REMEDIATE - {before.subject}")
        _print_assessment("before", before)
        print("  Nothing to remediate: no auto-fixable findings.")
        return 0

    out.write_text(result.patched_text, encoding="utf-8")
    if args.diff:
        Path(args.diff).write_text(result.diff, encoding="utf-8")

    after = assess_agent_file(str(out), resolve_roots=args.resolve_root)

    ba, aa = before.assurance, after.assurance
    print(f"AgentShield REMEDIATE - {before.subject}")
    print("-" * 64)
    _print_assessment("before", before)
    print("  applied :")
    for line in result.applied:
        print(f"             + {line}")
    for line in result.skipped:
        print(f"             ~ (skipped) {line}")
    _print_assessment("after", after)
    print("-" * 64)
    delta = (aa.score or 0) - (ba.score or 0)
    sign = "+" if delta >= 0 else ""
    print(f"  Result  : {ba.posture.value} {ba.score} ({len(before.findings)} findings)"
          f"  ->  {aa.posture.value} {aa.score} ({len(after.findings)} findings)"
          f"   [{sign}{delta} pts]")
    print(f"  Remediated definition: {out}")
    if args.diff:
        print(f"  Diff written: {args.diff}")
    if aa.posture.value == "WARN":
        print("  Note    : posture stays WARN by design - a static assessment is "
              "never enough to certify (PASS).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
