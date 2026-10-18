from __future__ import annotations
from dataclasses import dataclass
from enum import Enum
from typing import Any

class DecisionType(str, Enum):
    APPLY_P='APPLY_P'; APPLY_C='APPLY_C'; TOP2='TOP2'; ASK='ASK'; ABSTAIN='ABSTAIN'; BASELINE='BASELINE'
class CASEStatus(str, Enum):
    SUPPORTED='SUPPORTED'; REJECTED='REJECTED'; INSUFFICIENT='INSUFFICIENT'; NOT_IDENTIFIABLE='NOT_IDENTIFIABLE'
class CASVStatus(str, Enum):
    CERTIFIED='CERTIFIED'; FRAGILE='FRAGILE'; INSUFFICIENT='INSUFFICIENT'; NOT_IDENTIFIABLE='NOT_IDENTIFIABLE'
class ExecutionMode(str, Enum):
    ACTIVE='ACTIVE'; SHADOW='SHADOW'; NONE='NONE'

@dataclass(frozen=True)
class Decision:
    decision_id: str
    evidence_epoch: int
    decision_type: DecisionType
    action_ids: tuple[str,...]=()
    pre_execution_evidence_refs: tuple[str,...]=()
    posthoc_refs: tuple[str,...]=()
    reason: str=''
    authority: str='NONE'

@dataclass(frozen=True)
class CASECertificate:
    certificate_id: str
    decision_id: str
    evidence_epoch: int
    status: CASEStatus
    evidence_refs: tuple[str,...]=()
    claim_ceiling: str=''
    authority: str='NONE'

@dataclass(frozen=True)
class Support:
    model_id: str
    model_revision: str
    protocol_id: str
    budget: dict[str,Any]
    lineage: str=''
    operator_ids: tuple[str,...]=()
    sampler_warpers: tuple[str,...]=()
    prompt_protocol: str=''

@dataclass(frozen=True)
class CASVCertificate:
    certificate_id: str
    proposal_id: str
    status: CASVStatus
    support: Support
    claim_ceiling: str=''
    authority: str='NONE'

@dataclass(frozen=True)
class LeaseEligibility:
    eligible: bool
    mode: ExecutionMode
    reasons: tuple[str,...]
