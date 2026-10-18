# CFL/RDSS canonical intermediate representation · v1.0

## Scope

This IR materializes the source-supported pipeline without assigning global superiority to any operator. Its unit is the local jurisdiction of authority.

```text
o_t
 → (P_t ∥ C_t)                         complete procedural/configurational candidates
 → ECH-Core / AAD_pre                  hard non-LLM admissibility gates
 → A_macro ⊕ RDSS                      APPLY(P), APPLY(C), TOP2, ASK, ABSTAIN, BASELINE
 → CAS-E                               evidentiary certification of the decision
 → QAS-pre / QAS-P                     prospective support localization S_t
 → CAS-V                               CERTIFIED, FRAGILE, INSUFFICIENT, NOT_IDENTIFIABLE
 → ECH / AAD_exec                      assurance, fallback, shadow assignment
 → KCH                                 external lease bound to CAS-E, CAS-V, evidence epoch
 → KwanTau                             execution plus receipt
 → QAS-post                            realized-support conformance
 → y_t → Z-post                        future-only reinformation
```

## Ownership boundary

The interface `A_macro ⊕ RDSS` is frozen. Whether the macro callosal adjudicator and RDSS are implemented as one module or two cooperating modules remains an internal implementation choice. No claim depends on that unresolved partition.

## Non-inheritance invariants

```text
probe utility != generation utility
activity != semantic utility
support prediction != support certification
evidence != permission != authority != execution
post-hoc oracle != ex-ante router
Z_PH != semantic score
current outcome != current prior
```

## Decision types

- `APPLY_P(action_id)`
- `APPLY_C(action_id)`
- `TOP2(action_id_1, action_id_2)`
- `ASK(question_or_missing_information)`
- `ABSTAIN(reason)`
- `BASELINE(reason)`

## Fail-closed mapping

| Gate result | Permitted downstream state |
|---|---|
| discrimination fails | BASELINE or equivalence-class collapse |
| sufficiency fails | ASK, ABSTAIN, or BASELINE |
| support absent/OOD | ABSTAIN or BASELINE |
| CAS-E rejects | ASK, ABSTAIN, or BASELINE |
| CAS-V = NOT_IDENTIFIABLE | no active lease |
| CAS-V = INSUFFICIENT | no active lease |
| CAS-V = FRAGILE | SHADOW unless an explicit separate override certificate exists |
| CAS-V = CERTIFIED | eligible for KCH lease, not automatically leased |

## Future-only rule

No outcome, Human Eval, oracle, envelope, Z_PH label, or post-execution receipt from evidence epoch `t` may enter the decision at epoch `t`. It may only update a successor release/epoch.
