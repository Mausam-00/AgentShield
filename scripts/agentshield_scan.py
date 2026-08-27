"""AgentShield scan CLI: assess an agent definition, emit SARIF, gate CI.

Usage:
    python scripts/agentshield_scan.py AGENT.md [--sarif out.sarif]
                                       [--fail-on BLOCK|WARN]
                                       [--fix patched.md] [--diff patch.diff]

Exit code is non-zero when the assurance posture meets the ``--fail-on``
threshold, so the command can gate a pull-request pipeline. With ``--fix`` it
also writes a remediated copy of the definition and (optionally) a unified diff.

No network calls; nothing is executed against a target.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from agentshield import (  # noqa: E402
    assess_agent_file,
    assurance_to_sarif,
    gate_should_fail,
    remediate,
)


def main(argv: list[str]) -> int:
    ap = argparse.ArgumentParser(description="AgentShield agent scanner (SARIF + CI gate).")
    ap.add_argument("agent", help="Path to the agent definition (.md).")
    ap.add_argument("--sarif", help="Write SARIF 2.1.0 output to this path.")
    ap.add_argument("--fail-on", default="BLOCK", choices=["BLOCK", "WARN"],
                    help="Posture at or above which the process exits non-zero.")
    ap.add_argument("--fix", help="Write a remediated copy of the definition here.")
    ap.add_argument("--diff", help="Write the remediation unified diff here.")
    ap.add_argument("--resolve-root", action="append", default=[],
                    help="Extra base directory for resolving referenced assets.")
    args = ap.parse_args(argv)

    path = Path(args.agent)
    if not path.exists():
        print(f"error: file not found: {path}", file=sys.stderr)
        return 2

    assessment = assess_agent_file(str(path), resolve_roots=args.resolve_root)
    a = assessment.assurance

    print(f"AgentShield ASSESS - {assessment.subject}")
    print(f"  Posture : {a.posture.value}   Score: {a.score}   "
          f"Coverage: {a.coverage}   Confidence: {a.confidence.value}")
    print(f"  Findings: {len(assessment.findings)}")
    for f in assessment.findings:
        print(f"    [{f.severity.value:8}] {f.id}  {f.title}")

    if args.sarif:
        sarif = assurance_to_sarif(a, artifact_uri=path.name)
        Path(args.sarif).write_text(json.dumps(sarif, indent=2), encoding="utf-8")
        print(f"  SARIF written: {args.sarif}")

    if args.fix or args.diff:
        rem = remediate(assessment)
        if args.fix:
            Path(args.fix).write_text(rem.patched_text, encoding="utf-8")
            print(f"  Patched definition: {args.fix}")
        if args.diff:
            Path(args.diff).write_text(rem.diff, encoding="utf-8")
            print(f"  Diff written: {args.diff}")
        for line in rem.applied:
            print(f"    fixed  {line}")
        for line in rem.skipped:
            print(f"    skip   {line}")

    fail = gate_should_fail(a, fail_on=args.fail_on)
    print(f"  CI gate ({args.fail_on}): {'FAIL' if fail else 'pass'}")
    return 1 if fail else 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
