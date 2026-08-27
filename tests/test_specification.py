import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AGENT = ROOT / ".github" / "agents" / "agentshield.agent.md"
PROTOCOL = ROOT / "Protocols" / "AGENTSHIELD-PROTOCOL.md"
TEMPLATE = ROOT / "Templates" / "agentshield-assessment-report.md"
SKILL = ROOT / ".github" / "skills" / "agentshield-html-report" / "SKILL.md"
SCHEMA = (
    ROOT
    / ".github"
    / "skills"
    / "agentshield-html-report"
    / "references"
    / "report-schema.md"
)


def read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


class SpecificationTests(unittest.TestCase):
    def test_required_specification_files_exist(self) -> None:
        required = [
            AGENT,
            PROTOCOL,
            TEMPLATE,
            SKILL,
            SCHEMA,
            ROOT / "AGENTS.md",
            ROOT / ".github" / "copilot-instructions.md",
            ROOT / ".gitignore",
        ]
        self.assertEqual([], [str(path) for path in required if not path.is_file()])

    def test_agent_has_yaml_frontmatter_and_identity(self) -> None:
        agent = read(AGENT)
        self.assertTrue(agent.startswith("---\n"))
        self.assertIn("name: AgentShield AI", agent)
        self.assertIn("The Security Control Plane for the Agentic Enterprise", agent)

    def test_assurance_and_runtime_decisions_are_separate(self) -> None:
        protocol = read(PROTOCOL)
        template = read(TEMPLATE)
        for posture in ("PASS", "WARN", "BLOCK"):
            self.assertIn(f"`{posture}`", protocol)
        for decision in ("ALLOW", "TRANSFORM", "APPROVE", "ESCALATE", "DENY"):
            self.assertIn(f"`{decision}`", protocol)
        self.assertIn("Assurance posture and runtime decision are separate", template)
        self.assertRegex(template, r"`PASS` is not\s+certification")

    def test_protocol_defines_all_modes_and_gates(self) -> None:
        protocol = read(PROTOCOL)
        for mode in ("ASSESS", "OBSERVE", "GOVERN", "CONTROLLED LIVE"):
            self.assertIn(mode, protocol)
        for gate in range(8):
            self.assertRegex(protocol, rf"## \d+\. Gate {gate}:")

    def test_deterministic_policy_has_stable_unique_controls(self) -> None:
        protocol = read(PROTOCOL)
        controls = re.findall(r"\| (ASP-\d{3}) \|", protocol)
        self.assertGreaterEqual(len(controls), 21)
        self.assertEqual(len(controls), len(set(controls)))
        self.assertIn("DENY > ESCALATE > APPROVE > TRANSFORM > ALLOW", protocol)
        self.assertIn("Numerical scores cannot weaken these decisions", protocol)

    def test_missing_evidence_reduces_coverage_and_confidence(self) -> None:
        protocol = read(PROTOCOL)
        missing_section = protocol.split("### 4.3 Missing evidence", 1)[1].split(
            "### 4.4", 1
        )[0]
        self.assertIn("reduce the relevant coverage measure", missing_section)
        self.assertIn("reduce confidence", missing_section)
        self.assertIn("must never be treated as zero risk", missing_section)

    def test_lifecycle_and_approval_fail_closed_rules_exist(self) -> None:
        protocol = read(PROTOCOL)
        self.assertIn("| Review | Eligible reads may proceed; writes `ESCALATE` |", protocol)
        self.assertIn("| Quarantined | `DENY` every action |", protocol)
        self.assertIn("| Unknown | `DENY` |", protocol)
        self.assertIn("Timeout is not\napproval", protocol)
        self.assertIn("permits zero executed steps", protocol)

    def test_safety_invariants_are_explicit(self) -> None:
        protocol = read(PROTOCOL)
        self.assertIn("`add_disk` never becomes `remove_disk`", protocol)
        self.assertIn(
            "`provision_server` never becomes `decommission_server`", protocol
        )
        self.assertIn(
            "`apply_patch` never becomes `uninstall_patch` unless explicitly requested",
            protocol,
        )
        self.assertIn("failed validation stops all remaining steps", protocol)

    def test_every_outcome_requires_evidence(self) -> None:
        protocol = read(PROTOCOL)
        self.assertIn(
            "every allow, transform, approval,\n"
            "escalation, denial, rejection, timeout, failure, and observed deviation",
            protocol,
        )

    def test_html_generation_requires_explicit_request(self) -> None:
        agent = read(AGENT)
        skill = read(SKILL)
        self.assertIn("only when the end user explicitly", agent)
        self.assertIn("only when the end user explicitly", skill)
        self.assertIn("Do not trigger automatically", skill)

    def test_html_contract_requires_escaping_redaction_and_no_network(self) -> None:
        schema = read(SCHEMA)
        for requirement in (
            "Escape `&`, `<`, `>`, `\"`, and `'`",
            "Recursively redact",
            "embedded CSS only",
            "Do not include JavaScript",
            "No evidence available",
            "PASS is not certification",
        ):
            self.assertIn(requirement, schema)

    def test_controlled_live_is_disabled_and_not_claimed(self) -> None:
        combined = "\n".join((read(AGENT), read(PROTOCOL), read(SKILL)))
        self.assertIn("disabled by default", combined)
        self.assertIn("interface, mock, or dry-run transcript\nis not a live integration", combined)


if __name__ == "__main__":
    unittest.main()
