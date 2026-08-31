"""Offline tests for BYOD fairness measurement and measured RAI pillars."""

from __future__ import annotations

import unittest
from pathlib import Path

from agentshield.responsible_ai import evaluate_responsible_ai
from agentshield_live.adapters import MockAdapter
from agentshield_live.fairness import (
    extract_decision,
    fairness_to_report,
    load_fairness_dataset,
    run_fairness_probe,
)
from agentshield_live.rai_measured import (
    any_measured,
    build_measured_pillars,
    fairness_maturity,
    privacy_maturity,
    safety_maturity,
)

SAMPLE = Path(__file__).resolve().parents[1] / "agentshield_live" / "data" / "fairness_sample.jsonl"


def _biased(messages):
    """Approve male/younger, deny female/older - a deliberately biased model."""
    u = messages[-1]["content"].lower()
    if "female" in u or "58-year-old" in u:
        return "Denied."
    return "Approved."


def _unbiased(messages):
    return "Approved."


class DecisionExtractionTests(unittest.TestCase):
    def test_favorable(self):
        self.assertEqual(extract_decision("Approved."), "favorable")

    def test_unfavorable(self):
        self.assertEqual(extract_decision("Application denied."), "unfavorable")

    def test_negation_is_unfavorable(self):
        self.assertEqual(extract_decision("I would not approve this."), "unfavorable")

    def test_unknown(self):
        self.assertEqual(extract_decision("It depends on many factors."), "unknown")


class FairnessHarnessTests(unittest.TestCase):
    def setUp(self):
        self.cases = load_fairness_dataset(SAMPLE)

    def test_dataset_loads(self):
        self.assertGreaterEqual(len(self.cases), 6)
        self.assertTrue(all(c.prompt and c.group for c in self.cases))

    def test_biased_model_shows_disparity_and_blocks(self):
        res = run_fairness_probe(MockAdapter(_biased), self.cases, subject="biased")
        self.assertAlmostEqual(res.demographic_parity_diff, 1.0, places=4)
        self.assertEqual(res.counterfactual_flip_rate, 1.0)
        self.assertEqual(res.equal_opportunity_gap, 1.0)
        self.assertEqual(res.worst_gap, 1.0)
        self.assertEqual(res.posture, "RAI-BLOCK")

    def test_unbiased_model_is_fair(self):
        res = run_fairness_probe(MockAdapter(_unbiased), self.cases, subject="fair")
        self.assertEqual(res.demographic_parity_diff, 0.0)
        self.assertEqual(res.counterfactual_flip_rate, 0.0)
        self.assertEqual(res.worst_gap, 0.0)
        self.assertEqual(res.posture, "RAI-PASS")

    def test_report_shape(self):
        block = fairness_to_report(
            run_fairness_probe(MockAdapter(_unbiased), self.cases)
        )
        self.assertTrue(block["measured"])
        self.assertIn("demographic_parity_diff", block)
        self.assertIn("worst_gap", block)


class MaturityMappingTests(unittest.TestCase):
    def test_safety_maturity_bands(self):
        self.assertEqual(safety_maturity(0.0, 1.0)[0], 4)
        self.assertEqual(safety_maturity(0.0, 0.5)[0], 3)  # dodged, not refused
        self.assertEqual(safety_maturity(0.5, 0.0)[0], 0)

    def test_privacy_maturity_bands(self):
        self.assertEqual(privacy_maturity(0.0, 1.0)[0], 4)
        self.assertEqual(privacy_maturity(0.5, 0.0)[0], 0)

    def test_fairness_maturity_bands(self):
        self.assertEqual(fairness_maturity(0.0)[0], 4)
        self.assertEqual(fairness_maturity(1.0)[0], 0)


class MeasuredRAITests(unittest.TestCase):
    def _good(self):
        return {
            "content_safety": {"measured": True, "harm_rate": 0.0, "refusal_rate": 1.0},
            "redteam": {"mode": "live", "leakage_rate": 0.0, "injection_resistance": 1.0},
            "fairness": {"worst_gap": 0.0},
        }

    def _bad(self):
        return {
            "content_safety": {"measured": True, "harm_rate": 0.8, "refusal_rate": 0.0},
            "redteam": {"mode": "live", "leakage_rate": 0.9, "injection_resistance": 0.0},
            "fairness": {"worst_gap": 1.0},
        }

    def test_good_model_scores_numerically(self):
        blocks = self._good()
        pillars = build_measured_pillars(
            content_safety=blocks["content_safety"],
            redteam=blocks["redteam"],
            fairness=blocks["fairness"],
        )
        self.assertTrue(any_measured(pillars))
        res = evaluate_responsible_ai("good", pillars=pillars)
        self.assertIsNotNone(res.score)
        self.assertGreater(res.score, 50)
        self.assertIn(res.posture.value, ("PASS", "WARN"))

    def test_bad_model_fails_closed(self):
        blocks = self._bad()
        pillars = build_measured_pillars(
            content_safety=blocks["content_safety"],
            redteam=blocks["redteam"],
            fairness=blocks["fairness"],
        )
        res = evaluate_responsible_ai("bad", pillars=pillars)
        self.assertEqual(res.posture.value, "BLOCK")

    def test_no_fairness_dataset_leaves_fairness_unevidenced(self):
        pillars = build_measured_pillars(
            content_safety={"measured": True, "harm_rate": 0.0, "refusal_rate": 1.0},
            redteam={"mode": "live", "leakage_rate": 0.0, "injection_resistance": 1.0},
            fairness=None,
        )
        rai01 = next(p for p in pillars if p.pillar_id == "RAI-01")
        self.assertIsNone(rai01.maturity)
        self.assertFalse(rai01.tested)


if __name__ == "__main__":
    unittest.main()
