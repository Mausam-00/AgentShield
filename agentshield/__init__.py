"""AgentShield AI: assurance and deterministic governance for agentic systems.

Public surface for the synthetic, mock-backed workflow. No live connector,
credential, or real integration is included. CONTROLLED LIVE is disabled.
"""

from __future__ import annotations

from .models import (  # noqa: F401
    AUDIT_VERSION,
    POLICY_VERSION,
    ActionRequest,
    ApprovalBinding,
    ApprovalRecord,
    ApprovalResult,
    AssuranceResult,
    Confidence,
    Decision,
    EvidenceRecord,
    EvidenceState,
    FamilyEvaluation,
    Finding,
    IdentityContext,
    ImpactDimension,
    Lifecycle,
    Mode,
    ObservedOutcome,
    OperationalImpact,
    PlanStep,
    PolicyMatch,
    PolicyResult,
    Posture,
    SafePlan,
    Severity,
    ValidationResult,
    WorkflowResult,
)
from .assurance import evaluate_assurance  # noqa: F401
from .impact import compute_impact  # noqa: F401
from .policy import PolicyConfig, evaluate_policy  # noqa: F401
from .approvals import (  # noqa: F401
    approval_permits_execution,
    is_expired,
    verify_approval,
)
from .planning import (  # noqa: F401
    SafetyInvariantError,
    assert_invariants,
    build_safe_plan,
    execute_plan_with_validation,
)
from .validation import (  # noqa: F401
    deviation_finding,
    lifecycle_recommendation,
    validate_outcome,
)
from .evidence import InMemoryEvidenceStore, build_evidence  # noqa: F401
from .reporting import workflow_to_report  # noqa: F401
from .responsible_ai import (  # noqa: F401
    PillarEvaluation,
    RaiFinding,
    RaiResult,
    default_pillars,
    evaluate_responsible_ai,
    rai_to_report,
)
from .redteam import (  # noqa: F401
    RedTeamResult,
    combine_posture,
    load_probes,
    redteam_to_report_section,
    run_static_redteam,
)
from .static_assess import (  # noqa: F401
    StaticAssessment,
    assess_agent_file,
)
from .interception import (  # noqa: F401
    ExecutionResult,
    GatedExecutor,
    MockExecutionTarget,
)
from .sarif import (  # noqa: F401
    assurance_to_sarif,
    gate_should_fail,
)
from .remediation import (  # noqa: F401
    RemediationResult,
    remediate,
)
from .determinism import (  # noqa: F401
    ReplayReport,
    policy_bundle_hash,
    replay,
)
from .ledger import (  # noqa: F401
    HashChainedEvidenceStore,
    LedgerEntry,
    VerificationResult,
)
from .metrics import (  # noqa: F401
    AsrReduction,
    GovernanceMetrics,
    asr_reduction,
    compute_metrics,
)
from .integrations import (  # noqa: F401
    ContentSafetyPromptShield,
    EntraIdentityProvider,
    ShieldVerdict,
    entra_claims_to_identity,
)
from .workflow import AgentShieldWorkflow  # noqa: F401

__all__ = [
    "AgentShieldWorkflow",
    "evaluate_assurance",
    "compute_impact",
    "evaluate_policy",
    "PolicyConfig",
    "build_safe_plan",
    "execute_plan_with_validation",
    "assert_invariants",
    "SafetyInvariantError",
    "validate_outcome",
    "deviation_finding",
    "lifecycle_recommendation",
    "verify_approval",
    "approval_permits_execution",
    "is_expired",
    "InMemoryEvidenceStore",
    "build_evidence",
    "workflow_to_report",
    "run_static_redteam",
    "redteam_to_report_section",
    "combine_posture",
    "load_probes",
    "RedTeamResult",
    "evaluate_responsible_ai",
    "rai_to_report",
    "default_pillars",
    "PillarEvaluation",
    "RaiFinding",
    "RaiResult",
    # Prototypes
    "StaticAssessment",
    "assess_agent_file",
    "ExecutionResult",
    "GatedExecutor",
    "MockExecutionTarget",
    "assurance_to_sarif",
    "gate_should_fail",
    "RemediationResult",
    "remediate",
    "ReplayReport",
    "policy_bundle_hash",
    "replay",
    "HashChainedEvidenceStore",
    "LedgerEntry",
    "VerificationResult",
    "AsrReduction",
    "GovernanceMetrics",
    "asr_reduction",
    "compute_metrics",
    "ContentSafetyPromptShield",
    "ShieldVerdict",
    "EntraIdentityProvider",
    "entra_claims_to_identity",
]

__version__ = "1.0.0"


