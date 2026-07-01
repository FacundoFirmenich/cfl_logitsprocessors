# RDS Expanded Architecture: Prospective Preregistration v1.0

**Author:** Facundo Firmenich  
**Freeze date:** 2026-07-02  
**Status:** prospective, pre-experimental, immutable after public release  
**Scope:** Qwen3.5-4B, Phi-4-mini-instruct, Gemma4-E4B  
**Evidence boundary:** hypotheses and analysis commitments, not results.

## 1. Purpose and claim firewall

This document freezes the architecture, mechanistic expectations, sequence, outcomes, analysis, falsifiers, and custody before fresh integrated generation. Earlier generations are forensic lineage only: they cannot calibrate, validate, authorize, or supply results for this fresh programme.

The tested system comprises one unified operator family with TALM and TALON as its two subfamilies; BZ and ZX as separate internal operators; Top-H and TFS as the only natively admitted external operators in this version; RDS as ex-ante authority selection/abstention; QAS as qualified support localization; Z_post as post-generation evidence; and OBL as delayed Bayesian learning for later decisions.

No universal champion, global dominance, universal QAS fidelity, monotone activity-to-utility relation, or architectural equivalence with output competitors is predicted. Hashes establish integrity; repository/DOI timestamps establish custody, not empirical truth.

## 2. Frozen causal order

`OBL memory_<n -> RDS inference_n -> route freeze_n -> QAS/full generation_n -> Z_post,n -> typed admission_n -> OBL update_n+1`.

Candidate outputs and current Z_post evidence are unavailable to the route that generated them. Oracle is post hoc only. Same-decision leakage invalidates the affected routing claim.

## 3. Frozen identities and models

An executable action is `branch_id + implementation_lineage + canonical_configuration_sha256`. Family containers, unconfigured names, set-level hashes, aliases, controls, rejected lineages, and unresolved records are not routable.

The package snapshots the exact action registry v1.0, model registry, phases, and every prompt suite. At freeze: 44 registered records, 39 source-derived exact configurations, five initially generation-enabled actions, 40 probe-capable actions, and three unresolved historical records that cannot become authorities.

Central models:

1. `Qwen/Qwen3.5-4B` @ `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`;
2. `microsoft/Phi-4-mini-instruct` @ `cfbefacb99257ffa30c83adab238a50856ac3083`;
3. `google/gemma-4-E4B-it` @ `fee6332c1abaafb77f6f9624236c63aa2f1d0187`.

Primary common protocol: NF4 4-bit, double quantization, FP16 compute, temperature 1.0, top-p 1.0, top-k 0, stochastic generation, model-appropriate template, and verified thinking disable where applicable. Model, prompt, template, precision, order, or revision drift is fail-closed.

## 4. Initial roles

Generation-enabled exact actions: `talon_mass_right`, `talm_mass_right_soft`, `talm_mass_left_soft`, Top-H (`alpha=.4`, `top_n=100`, safe official greedy semantics), and TFS (`z=.95`, normalized absolute second derivative).

`talon_mass_right` receives the weak favourable pillar prior; `talm_mass_right_soft` the principal complementary prior. These are falsifiable priors, never guaranteed winners. No action is assigned zero probability from doctrine alone.

Development-only promotion requires coherent mechanics in all three models, exact identity, contract compliance, nonredundancy, and favourable local evidence in at least two prompts and two coherent categories. Selection data cannot confirm the promoted hypothesis; confirmation uses untouched reserve.

BZ owns the least-probable 0.25% of original mass and ZX the next disjoint 5.00%, with fractional boundary ownership. They are probe-only at this freeze because `q_BZ` and `q_ZX` are not mathematically fixed. Generative use requires a new prospective hashed amendment defining transformations, controls, invariants, and tests before inspecting corresponding outputs.

## 5. Experimental sequence

1. Mechanical factibilization: 12 prompts, seed 1729, <=128 steps, all probe-capable actions, no semantic selection.
2. Development microcartography: 18 prompts, six coherent categories, seeds 11/22, 944 tokens, three models, baseline plus enabled candidates.
3. Long heterodox laboratory: 12 fresh prompts, 2,048--4,096 tokens, seed 11 and adaptive seed 22 under frozen triggers.
4. QAS: six prompts/model, seeds 11/22, identical action and random stream for full/QAS pairs.
5. Z_post/OBL: four waves; updates affect later waves only.
6. Bayes validation: prior predictive, parameter recovery, SBC, NUTS diagnostics, posterior predictive, sensitivity.
7. Prospective mini-RDS: 12 untouched prompts, seeds 11/22, 944 tokens, frozen routes and full counterfactual matrix.
8. Confirmation: 20 untouched prompts, seeds 11/22/33, 944 tokens, three models, NF4 plus paired preregistered BF16 audit subset.

A failed mandatory gate blocks the later phase.

## 6. Outcomes and reporting

Primary row: `model x prompt x seed x exact action x budget x precision x protocol x representation`. Rows remain primary. Summaries are allowed only within coherent categories. Heterogeneous global adjudication, universal rankings, and global-superiority claims are prohibited.

Primary semantic outcome is local net utility versus matched baseline, retaining benefit/neutral/harm and magnitude. Response, utility, support, fidelity, harm, and cost are separate axes. Activity, KL, mass movement, and Z_post intensity cannot substitute for utility.

## 7. Frozen prospective predictions

### Mechanics

- **H01 TALON projection:** every contract-bearing TALON execution preserves final top-1. Any violation blocks the implementation/cell.
- **H02 TALM crossings:** TALM usually preserves top-1 in many contexts but permits nonzero intentional crossings; crossings are logged, never repaired.
- **H03 pillar response:** `talon_mass_right` shows coherent nonzero mechanical response across all three models more often than left/balanced TALON probes; this is not universal utility.
- **H04 complementarity:** `talm_mass_right_soft` supplies nonredundant response or utility cells beyond fixed `talon_mass_right`.
- **H05 activity != utility:** utility is not monotone in intervention intensity; some highly active cells are neutral or harmful.
- **H06 Top-H/TFS nonredundancy:** their masks/fingerprints differ contextually.
- **H07 C/F/R informativeness:** consensus core, disagreement frontier, and jointly discarded residual differ on at least one registered mechanical/decisional axis.
- **H08 frontier uncertainty:** frontier mass/instability associates with branch disagreement or route uncertainty and may increase Top-2 value.
- **H09 BZ/ZX exactness:** partitions are disjoint, conserve mass, and allocate .0025/.05 up to tolerance with fractional boundaries.
- **H10 portability with heterogeneity:** mechanisms remain numerically stable in all three architectures, while magnitudes and useful jurisdictions remain model-dependent.

### Generation and routing

- **H11 no global champion:** fresh data retain local win/tie/loss/baseline-abstention/out-of-support regions; apparent universality triggers audit.
- **H12 fixed-pillar boundary:** `talon_mass_right` is a strong comparator, but reserve cells exist where baseline or another admitted action is preferable.
- **H13 complementary RDS:** calibrated abstention-aware RDS exploits some nonredundant cells beyond the fixed pillar; failure is reported, not rescued.
- **H14 native external duality:** Top-H/TFS may be more useful as delimiters/probes than frequent generators; native status predicts no route frequency.
- **H15 full vs internal-only RDS:** Top-H/TFS fingerprints/authority improve at least one held-out property: calibration, abstention, support, Top-2 coverage, or false-positive control; unconditional mean is not the target.
- **H16 model heterogeneity:** action ordering and abstention differ across Qwen/Phi/Gemma; Qwen priors require learned attenuation.
- **H17 category heterogeneity:** coherent categories have different useful-action/abstention profiles; category summaries beat pooled ranking descriptively.
- **H18 long-context novelty:** long heterodox prompts expose response, repetition, termination, coherence, or safety phenomena absent from 944-token microcartography.

### QAS, Z_post, OBL, Bayes

- **H19 conditional QAS fidelity:** high for some action-context pairs, not universal; deployment requires a fidelity gate.
- **H20 QAS efficiency:** fidelity-admitted cells reduce support size, memory, latency, or compute proxy without breaching tolerance.
- **H21 Z_post limits:** Z_post predicts response/support better than semantic utility unless combined with independent semantic evidence.
- **H22 Z_post transfer:** some development jurisdictions transfer to fresh prompts better than unconditioned global rankings; otherwise remain retrospective.
- **H23 delayed learning:** OBL changes later route probabilities/lifecycle while base weights and revision hashes remain fixed.
- **H24 no leakage:** current outputs/Z_post never influence their already frozen route.
- **H25 hierarchical transfer:** partial pooling with learned attenuation improves at least one held-out calibration criterion over branch-independent or unchanged-Qwen transfer.
- **H26 typed evidence:** six-axis modelling improves calibration or error localization over scalar success updates.
- **H27 dynamic controller:** full dynamic hierarchy improves at least one held-out decision/calibration criterion over static priors without exceeding harm tolerance.
- **H28 abstention:** uncertainty/harm gates yield nonzero abstention and reduce unsupported interventions versus forced selection.
- **H29 hysteresis:** reduces lifecycle thrashing versus matched single-threshold logic.
- **H30 bench reentry:** at least one branch may recover after material context shift; inability to reevaluate makes bench archival.

### Quantization and reproducibility

- **H31 NF4 boundary:** exact invariants and qualitative signatures survive NF4; utility magnitudes and routes may differ from BF16.
- **H32 reproducibility:** identical frozen inputs reproduce deterministic contracts, static hashes, row keys, and completeness counts; stochastic text identity is required only where the runtime guarantees it.

### Conditional active-Z and scale predictions

These predictions are timestamped now but cannot be activated or tested until a pre-output amendment freezes `q_BZ`, `q_ZX`, and their controls.

- **H33 BZ rare-yield structure:** BZ has low win frequency, high variance, high leverage conditional on a win, and heavier-tailed local utility than ZX or ordinary truncators.
- **H34 ZX coverage:** ZX increases residual-shell coverage and reduces repeated visitation of identical residual bands relative to matched ordinary sampling.
- **H35 BZ/ZX contrast:** BZ produces fewer useful events, more extreme rank movement, larger conditional trajectory change, and greater failure risk than broader ZX exploration.
- **H36 structured-Z controls:** active BZ must outperform equal-mass random reallocation on its registered rare-yield target, and ZX must outperform shuffled residual reallocation on coverage; otherwise the corresponding mechanism is falsified.
- **H37 structural scale covariance:** the macro-to-micro role map is supported only if branch autonomy, heteropolarity, higher-order authority, abstention, generation/arbitration separation, and delayed post-hoc learning are operationally measurable invariants; failure to operationalize them falsifies this claim.
## 8. Falsifiers and gates

- Nonzero final TALON top-1 change falsifies that implementation contract.
- Effective Top-H/TFS identity weakens native nonredundancy.
- C/F/R unrelated to every registered axis falsifies its informativeness.
- Treating activity as semantic utility invalidates analysis.
- QAS divergence beyond tolerance blocks that jurisdiction.
- Same-decision leakage invalidates route-derived claims.
- Failed prior predictive, SBC, recovery, zero-divergence NUTS, `R-hat <= 1.01`, ESS, or BFMI gates block Bayesian scientific use.
- A router without held-out improvement over fixed-pillar/static comparators cannot support the corresponding RDS claim.
- No aggregate may erase prompt-level losses, harm, ties, abstentions, censoring, or missingness.

## 9. Bayesian and evaluation commitment

The controller is generative, hierarchical, dynamic, calibrated, decision-theoretic, and abstention-awareâ€”not an additive score. Hierarchy: portfolio -> typed parent -> TALM/TALON subfamily where applicable -> exact action -> model -> coherent category -> prompt -> correlated seed/time. Six axes remain distinct with regularized dependence. Prompt is the held-out cluster; seeds are correlated repetitions.

Offline comparators on identical candidates: baseline/abstention, fixed `talon_mass_right`, historical heuristic, prior-only, likelihood-only, full posterior, and oracle post hoc. Validation: LOPO, leave-category/model/seed-out, calibration, coverage, harm, abstention, regret, compute-normalized utility, and threshold/prior sensitivity.

Formal tasks use deterministic validators. Open-ended creativity, philosophy, methodology, and safety quality use blinded humans or separately validated semantic evaluation. Evaluators receive randomized IDs without action labels. Missing/censored termination is explicit.

## 10. Amendments and custody

After public freeze this file is immutable. Changes require numbered hashed amendments stating reason, affected fields/hypotheses, and whether relevant outputs were inspected. Post-inspection changes lose prospective status for affected claims.

Canonical package: UTF-8 NFC, LF, no BOM, SHA-256 per payload, canonical JSON manifest, `SHA256SUMS.txt`, and root prehash over the ordered payload ledger. Record Git commit/tag, GitHub release, Zenodo version DOI, and concept DOI after upload. Timestamp proves prior existence of hypotheses, not correctness.