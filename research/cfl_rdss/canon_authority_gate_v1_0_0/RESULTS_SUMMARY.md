# CFL/RDSS Canon & Jurisdictional Authority Gate v1.0.0

## Gate verdict

```text
PASS_EXACT_SOURCE_RECOVERY
+ PASS_CANONICAL_TYPED_IR
+ PASS_HISTORICAL_GATE_REPLAY
+ PASS_ACTION_EQUIVALENCE_AUDIT
+ PASS_QAS_METHOD_LOCAL_CERTIFICATION
+ PROSPECTIVE_AUTHORITY_EXPERIMENT_OPEN
```

## RDS v3.3 — prior-collapse/null

- 180 rows and 60 complete baseline/full/QAS triplets.
- 60/60 final-text identical and 60/60 raw-text identical.
- All 20 route plans selected `talm_right_high`.
- Human prior contributed a mean 77.10% of the selected score.
- Without the human-prior term, counterfactual winners were: `talon_mass_right` 10, `talm_mass_right_soft` 5, `talm_right_high` 4, `talm_mass_left_soft` 1.

Canonical replay: `BASELINE`, CAS-E `REJECTED`, CAS-V `NOT_IDENTIFIABLE` for branch utility.

## G0 240 — generation equivalence and probe distinction

- 240 candidate rows, 54 prompt-seed units and six nominal actions.
- 53 rows hit the 944-token cap.
- `talm_right_high` and `talon_head_right` are final-text identical in 54/54 common units.
- Their probe fingerprints remain distinct: mean standardized distance 2.568078 across 18 prompts.

Canonical replay: collapse them into one generation-equivalence class under the frozen final-text operator, but preserve both as distinct probes. This is the material separation `probe_action != generation_action`.

## COMPETITOR944 — QAS is method-local

- 840 rows, 420 full/QAS pairs, seven external methods and zero recorded errors.
- Text identity: 387/420 (92.14%).
- Score identity: 419/420.
- Termination identity: 418/420.
- Exact 60/60 text/score/termination fidelity occurs for Min-K and Min-P 0.05/0.10/0.20.
- Mirostat text identity is 31/60 (51.67%).
- All seven methods have higher mean QAS time than full execution.

Canonical replay: method-local CAS-V certificates; no universal QAS neutrality and the speedup claim is rejected for this campaign.

## Canonical architecture

```text
A_macro ⊕ RDSS
 → CAS-E
 → QAS-pre
 → CAS-V
 → ECH/AAD_exec
 → KCH lease
 → KwanTau execution
 → QAS-post
 → Z-post future-only
```

The action portfolio includes baseline, TALM/TALON, external controls, TOP2, ASK and ABSTAIN. Oracle, envelope, Human Eval and Z_PH remain post hoc.

## Boundaries

- CFLDR Plus v0.4 remains E1/E3 with exact package pending.
- RDSS v3.5 remains historically supported at 252 rows / 96 full-QAS pairs / 70 non-vacuous pairs, but its complete exact package was not recovered in this gate.
- Chinese/Jais lines are outside the active canon.
- `RDFS`, `FD/F` and `C Schema` remain unresolved terms; no invented module is introduced.
- The prospective authority experiment is preregistered but not executed.
