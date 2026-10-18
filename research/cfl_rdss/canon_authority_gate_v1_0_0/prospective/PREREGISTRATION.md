# CFL/RDSS Prospective Jurisdictional Authority Gate · preregistration

**Status:** `PREREGISTERED_NOT_EXECUTED`

## Primary question

Can an ex-ante CFL/RDSS policy reduce local regret relative to fixed and external controls while respecting support, sufficiency, abstention, cost, fidelity and future-only constraints?

## Frozen context

```text
(model_id, revision, prompt_id, prompt_protocol, seed, budget,
 warper_order, candidate_action_registry, pre-generation fingerprints)
```

## Actions

- BASELINE
- eligible TALM/TALON branches
- comparable external controls/samplers
- TOP2
- ASK
- ABSTAIN

Post-hoc oracle, envelope, Human Eval and Z_PH are not actions.

## Policy comparators

1. best fixed action selected only on training;
2. BASELINE;
3. best external fixed action selected only on training;
4. CFLDR preroute;
5. CFLDR inline;
6. canonical CFL/RDSS with CAS-E, QAS-pre and CAS-V;
7. TOP2;
8. abstention;
9. post-hoc oracle as an unattainable ceiling only.

## Leakage boundary

- Prompt identifiers, model revisions and protocols are group-split.
- No current output, Human Eval, oracle, envelope, termination outcome or Z_PH label enters routing.
- Priors come from a named frozen predecessor release and are attenuated by lineage/support distance.
- Selection and confirmation are disjoint.
- Current outcomes update only a successor evidence epoch.

## Primary outcomes

- local regret to the frozen post-hoc oracle;
- oracle capture rate;
- W/T/L/damage against best fixed, baseline and best external;
- machine-checkable contract, completeness and coherence metrics;
- ASK/ABSTAIN calibration;
- false-active rate outside certified support;
- CAS-E and CAS-V violation rates;
- QAS-post support-conformance rate;
- token, forward-equivalent, latency and tuning costs;
- switches and dwell/cooldown violations for inline routing.

## Kill criteria

Discrimination failure, support non-identifiability, insufficient effective sample size, prior collapse, outcome leakage, CAS mismatch, QAS support escape, excessive censoring, failure versus fixed policies within uncertainty, or local external dominance.

## Result states

`SUPPORTED`, `REJECTED`, `NOT_IDENTIFIABLE`, `INSUFFICIENT_POWER`, `OUT_OF_SCOPE`, `PROTOCOL_VIOLATION`.
