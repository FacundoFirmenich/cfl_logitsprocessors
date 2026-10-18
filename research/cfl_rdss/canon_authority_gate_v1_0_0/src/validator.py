from __future__ import annotations
from cfl_rdss_types import *

POSTHOC_MARKERS=('oracle','human_eval_current','z_ph_current','envelope_current','outcome_current')

def validate_decision(d: Decision, known_actions:set[str])->list[str]:
    e=[]
    if d.authority!='NONE': e.append('DECISION_CANNOT_CARRY_AUTHORITY')
    if d.evidence_epoch<0: e.append('NEGATIVE_EVIDENCE_EPOCH')
    if any(any(m in r.lower() for m in POSTHOC_MARKERS) for r in d.pre_execution_evidence_refs):
        e.append('POSTHOC_LEAKAGE_IN_PRE_EXECUTION_EVIDENCE')
    n=len(d.action_ids)
    if d.decision_type in (DecisionType.APPLY_P,DecisionType.APPLY_C) and n!=1:
        e.append('APPLY_REQUIRES_ONE_ACTION')
    if d.decision_type==DecisionType.TOP2 and n!=2:
        e.append('TOP2_REQUIRES_TWO_ACTIONS')
    if d.decision_type in (DecisionType.ASK,DecisionType.ABSTAIN,DecisionType.BASELINE) and n>1:
        e.append('NON_APPLY_HAS_TOO_MANY_ACTIONS')
    if len(set(d.action_ids))!=n: e.append('DUPLICATE_ACTIONS')
    if any(a not in known_actions for a in d.action_ids): e.append('UNKNOWN_ACTION')
    return e

def lease_eligibility(d:Decision, ce:CASECertificate, cv:CASVCertificate)->LeaseEligibility:
    reasons=[]
    if ce.decision_id!=d.decision_id: reasons.append('CAS_E_DECISION_MISMATCH')
    if ce.evidence_epoch!=d.evidence_epoch: reasons.append('CAS_E_EPOCH_MISMATCH')
    if ce.status!=CASEStatus.SUPPORTED: reasons.append('CAS_E_NOT_SUPPORTED')
    if cv.status==CASVStatus.CERTIFIED: mode=ExecutionMode.ACTIVE
    elif cv.status==CASVStatus.FRAGILE: mode=ExecutionMode.SHADOW
    else:
        mode=ExecutionMode.NONE
        reasons.append('CAS_V_NOT_EXECUTABLE')
    if d.decision_type in (DecisionType.ASK,DecisionType.ABSTAIN):
        mode=ExecutionMode.NONE
        reasons.append('DECISION_NON_EXECUTING')
    fatal={'CAS_E_DECISION_MISMATCH','CAS_E_EPOCH_MISMATCH','CAS_E_NOT_SUPPORTED','CAS_V_NOT_EXECUTABLE','DECISION_NON_EXECUTING'}
    if any(r in fatal for r in reasons):
        return LeaseEligibility(False,ExecutionMode.NONE,tuple(reasons))
    return LeaseEligibility(True,mode,tuple(reasons))

def qas_post_conforms(realized:set[str], certified:set[str])->bool:
    return realized.issubset(certified)
