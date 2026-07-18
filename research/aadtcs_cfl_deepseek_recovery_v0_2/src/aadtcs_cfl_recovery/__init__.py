"""Shadow-only recovery primitives for AAD–TCS–{Kwâncødë}."""

from .adequacy import (
    AdequacyAssessment,
    AdequacyBound,
    AdequacyCertificateContext,
    AdequacyDimensionSpec,
    AdequacyOverallStatus,
    DimensionRequirement,
    DimensionStatus,
    EvidenceGap,
    IntervalType,
    assess_adequacy,
)
from .claims import ClaimDisposition, ClaimEvidenceState, ClaimRecord
from .oversufficiency import (
    OriginOversufficiencyAssessment,
    OriginOversufficiencyStatus,
    OriginOversufficiencyVector,
    OversufficiencyAction,
    assess_origin_oversufficiency,
    combine_adequacy_and_origin,
)
from .process_integrity import (
    ProcessEvent,
    ProcessHashChain,
    ProcessIntegrityCertificate,
    merkle_root,
)
from .tails import (
    ExactBudgetRankTailSelector,
    FrozenThresholdTailSelector,
    MetricOrientation,
    NonFiniteKind,
    RobustTailMetrics,
    RobustTailScorer,
    TailPoint,
    TailReference,
    TailRegion,
    TailSelectionV2,
    TiePolicy,
    expected_shortfall,
)

__all__ = [name for name in globals() if not name.startswith("_")]
