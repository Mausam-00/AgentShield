"""Phase 2 workflow behavior tests (synthetic, mock-backed).

Covers the required behaviors 1-17 and 20 from the build brief. HTML report and
public-safety tests live in dedicated modules added in later phases.
"""

from __future__ import annotations

import unittest
from datetime import datetime, timezone

import fixtures as fx

from agentshield import (
    AgentShieldWorkflow,
    ApprovalBinding,
    ApprovalRecord,
    ApprovalResult,
    Decision,
    InMemoryEvidenceStore,
    Lifecycle,
    ObservedOutcome,
    PlanStep,
    Posture,
    PolicyConfig,
    SafetyInvariantError,
    build_safe_plan,
    evaluate_policy,
    execute_plan_with_validation,
    validate_outcome,
)


def govern(workflow, req, ident, assurance, impact, **kw):
    return workflow.govern(req, ident, assurance, impact, **kw)


class DecisionSeparationTests(unittest.TestCase):
    def test_1_assurance_and_runtime_are_separate(self):
        # BLOCK posture but a read-only in-scope op is still policy-eligible.
        wf = AgentShieldWorkflow()
        req = fx.request(action="read_config", read_only=True)
        result = govern(
            wf, req, fx.identity(), fx.blocking_assurance(), fx.low_impact()
        )
        self.assertEqual(result.assurance.posture, Posture.BLOCK)
        self.assertEqual(result.policy.decision, Decision.ALLOW)

    def test_1b_block_posture_denies_writes(self):
        wf = AgentShieldWorkflow()
        req = fx.request(
            action="add_disk", read_only=False, environment="non-production"
        )
        result = govern(
            wf, req, fx.identity(), fx.blocking_assurance(), fx.low_impact()
        )
        self.assertEqual(result.policy.decision, Decision.DENY)
        self.assertIn("ASP-003", [m.control_id for m in result.policy.matches])


class EvidenceConfidenceTests(unittest.TestCase):
    def test_2_missing_evidence_lowers_confidence_and_coverage(self):
        full = fx.passing_assurance()
        partial = fx.evaluate_assurance_partial()
        self.assertLess(partial.coverage, full.coverage)
        self.assertNotEqual(partial.confidence, full.confidence)
        self.assertTrue(partial.coverage_limitations)


class FailClosedTests(unittest.TestCase):
    def test_3_unknown_requester_fails_closed(self):
        wf = AgentShieldWorkflow()
        req = fx.request(action="read_config", read_only=True)
        ident = fx.identity(known=False, lifecycle=Lifecycle.UNKNOWN)
        result = govern(wf, req, ident, fx.passing_assurance(), fx.low_impact())
        self.assertEqual(result.policy.decision, Decision.DENY)

    def test_4_quarantined_requester_denied(self):
        wf = AgentShieldWorkflow()
        req = fx.request(action="read_config", read_only=True)
        ident = fx.identity(lifecycle=Lifecycle.QUARANTINED)
        result = govern(wf, req, ident, fx.passing_assurance(), fx.low_impact())
        self.assertEqual(result.policy.decision, Decision.DENY)

    def test_5_review_state_write_escalates(self):
        wf = AgentShieldWorkflow()
        req = fx.request(
            action="add_disk", read_only=False, environment="non-production"
        )
        ident = fx.identity(lifecycle=Lifecycle.REVIEW)
        result = govern(wf, req, ident, fx.passing_assurance(), fx.low_impact())
        controls = [m.control_id for m in result.policy.matches]
        self.assertIn("ASP-010", controls)
        self.assertEqual(result.policy.decision, Decision.ESCALATE)

    def test_6_stale_assurance_escalates_production_write(self):
        wf = AgentShieldWorkflow()
        req = fx.request(
            action="add_disk", read_only=False, environment="production"
        )
        ident = fx.identity(assurance_age_days=999.0)
        result = govern(wf, req, ident, fx.passing_assurance(), fx.low_impact())
        controls = [m.control_id for m in result.policy.matches]
        self.assertIn("ASP-011", controls)


class ScopeAndPrecedenceTests(unittest.TestCase):
    def test_7_out_of_scope_action_denied(self):
        wf = AgentShieldWorkflow()
        req = fx.request(action="delete_everything", read_only=False)
        ident = fx.identity(capabilities=["read_config"])
        result = govern(wf, req, ident, fx.passing_assurance(), fx.low_impact())
        self.assertEqual(result.policy.decision, Decision.DENY)
        self.assertIn("ASP-005", [m.control_id for m in result.policy.matches])

    def test_8_deterministic_rules_override_risk_score(self):
        # Perfect assurance (high score) must not rescue an out-of-scope write.
        wf = AgentShieldWorkflow()
        req = fx.request(action="add_disk", read_only=False)
        ident = fx.identity(capabilities=["read_config"])
        result = govern(wf, req, ident, fx.passing_assurance(), fx.low_impact())
        self.assertEqual(result.assurance.posture, Posture.PASS)
        self.assertEqual(result.policy.decision, Decision.DENY)

    def test_9_security_sensitive_action_routes_to_approval(self):
        wf = AgentShieldWorkflow()
        req = fx.request(
            action="add_disk",
            read_only=False,
            environment="non-production",
        )
        impact = fx.high_impact(security_sensitive=True)
        result = govern(wf, req, fx.identity(), fx.passing_assurance(), impact)
        controls = [m.control_id for m in result.policy.matches]
        self.assertIn("ASP-017", controls)

    def test_10_fleet_wide_change_requires_approval(self):
        wf = AgentShieldWorkflow()
        req = fx.request(
            action="add_disk", read_only=False, environment="non-production"
        )
        impact = fx.high_impact(fleet_wide=True)
        result = govern(wf, req, fx.identity(), fx.passing_assurance(), impact)
        self.assertIn("ASP-019", [m.control_id for m in result.policy.matches])


class ApprovalBindingTests(unittest.TestCase):
    def _binding(self, **overrides):
        base = dict(
            requester_id="svc-synthetic",
            action="add_disk",
            target="synthetic-target",
            plan_hash="hash-123",
            policy_version=PolicyConfig().version,
            expiry_utc="2999-01-01T00:00:00Z",
        )
        base.update(overrides)
        return ApprovalBinding(**base)

    def test_11_approval_is_action_and_target_bound(self):
        from agentshield import verify_approval

        binding = self._binding()
        record = ApprovalRecord(
            result=ApprovalResult.APPROVED, approver="a", binding=binding
        )
        # Same binding verifies.
        self.assertTrue(verify_approval(record, self._binding()))
        # Different target does not.
        self.assertFalse(
            verify_approval(record, self._binding(target="other-target"))
        )
        # Different action does not.
        self.assertFalse(
            verify_approval(record, self._binding(action="remove_disk"))
        )

    def test_12_expired_approval_cannot_execute(self):
        from agentshield import approval_permits_execution

        binding = self._binding(expiry_utc="2000-01-01T00:00:00Z")
        record = ApprovalRecord(
            result=ApprovalResult.APPROVED, approver="a", binding=binding
        )
        self.assertFalse(approval_permits_execution(record, binding))

    def test_13_rejected_approval_zero_steps(self):
        wf = AgentShieldWorkflow()
        req = fx.request(
            action="add_disk", read_only=False, environment="production"
        )
        rejected = ApprovalRecord(
            result=ApprovalResult.REJECTED, approver="a", binding=None
        )
        result = govern(
            wf,
            req,
            fx.identity(),
            fx.passing_assurance(),
            fx.low_impact(),
            approval=rejected,
        )
        self.assertEqual(result.policy.decision, Decision.DENY)


class SafePlanTests(unittest.TestCase):
    def _step(self, action, capability):
        return PlanStep(
            id="s1",
            action=action,
            target_scope="synthetic-target",
            reason="synthetic reason",
            validation="synthetic validation",
            rollback="synthetic rollback",
            stop_condition="stop on failure",
            required_capability=capability,
        )

    def test_14_add_disk_never_becomes_remove_disk(self):
        req = fx.request(action="add_disk", read_only=False)
        with self.assertRaises(SafetyInvariantError):
            build_safe_plan(
                req,
                ["add_disk", "remove_disk"],
                [self._step("remove_disk", "remove_disk")],
            )

    def test_15_provision_never_becomes_decommission(self):
        req = fx.request(action="provision_server", read_only=False)
        with self.assertRaises(SafetyInvariantError):
            build_safe_plan(
                req,
                ["provision_server", "decommission_server"],
                [self._step("decommission_server", "decommission_server")],
            )

    def test_16_failed_validation_stops_remaining_steps(self):
        req = fx.request(action="add_disk", read_only=False)
        steps = [
            PlanStep("s1", "add_disk", "t", "r", "v", "rb", "stop", "add_disk"),
            PlanStep("s2", "add_disk", "t", "r", "v", "rb", "stop", "add_disk"),
            PlanStep("s3", "add_disk", "t", "r", "v", "rb", "stop", "add_disk"),
        ]
        plan = build_safe_plan(req, ["add_disk"], steps)
        executed, stopped = execute_plan_with_validation(
            plan, {"s1": True, "s2": False, "s3": True}
        )
        self.assertEqual(executed, ["s1"])
        self.assertEqual(stopped, "s2")


class DeviationTests(unittest.TestCase):
    def test_16b_deviation_stops_and_flags(self):
        req = fx.request(action="add_disk", read_only=False)
        steps = [PlanStep("s1", "add_disk", "t", "r", "v", "rb", "stop", "add_disk")]
        plan = build_safe_plan(req, ["add_disk"], steps)
        observed = ObservedOutcome(
            action="remove_disk", target="synthetic-target", outcome="success"
        )
        validation = validate_outcome("add_disk", "synthetic-target", plan, observed)
        self.assertTrue(validation.deviated)
        from agentshield import deviation_finding, lifecycle_recommendation

        finding = deviation_finding(validation, req.trace_id)
        self.assertIsNotNone(finding)
        self.assertEqual(lifecycle_recommendation(validation), "Quarantined")


class EvidenceTests(unittest.TestCase):
    def test_17_all_outcomes_create_evidence(self):
        store = InMemoryEvidenceStore()
        wf = AgentShieldWorkflow(evidence_store=store)
        # Denial path.
        govern(
            wf,
            fx.request(action="x", read_only=False),
            fx.identity(capabilities=["read_config"]),
            fx.passing_assurance(),
            fx.low_impact(),
        )
        # Allow path.
        govern(
            wf,
            fx.request(action="read_config", read_only=True),
            fx.identity(),
            fx.passing_assurance(),
            fx.low_impact(),
        )
        self.assertEqual(len(store), 2)
        for record in store.all():
            self.assertTrue(record.outcome)
            self.assertTrue(record.accountability_statement)
            self.assertTrue(record.trace_id)

    def test_evidence_store_is_append_only(self):
        store = InMemoryEvidenceStore()
        wf = AgentShieldWorkflow(evidence_store=store)
        govern(
            wf,
            fx.request(action="read_config", read_only=True),
            fx.identity(),
            fx.passing_assurance(),
            fx.low_impact(),
        )
        snapshot = store.all()
        snapshot[0].outcome = "tampered"
        self.assertNotEqual(store.all()[0].outcome, "tampered")


class EngineFailureTests(unittest.TestCase):
    def test_policy_engine_failure_fails_closed(self):
        req = fx.request(action="read_config", read_only=True)
        result = evaluate_policy(
            req,
            fx.identity(),
            fx.passing_assurance(),
            fx.low_impact(),
            config=PolicyConfig(engine_healthy=False),
        )
        self.assertEqual(result.decision, Decision.DENY)
        self.assertTrue(result.engine_failed)


if __name__ == "__main__":
    unittest.main()
