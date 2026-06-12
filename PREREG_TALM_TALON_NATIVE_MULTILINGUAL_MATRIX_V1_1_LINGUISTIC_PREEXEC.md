# Pre-Registration Protocol — TALM/TALON Native Multilingual Matrix v1.0

**Protocol ID:** `PREREG_TALM_TALON_NATIVE_MULTILINGUAL_MATRIX_V1`  
**Status:** Pre-execution registration draft for repository upload and external redistribution.
**Protocol minor revision:** linguistic pre-execution layer and submerged-property map explicitly registered.  
**Date:** 2026-06-12  
**Engines:** TALM v1.0.0 / TALON v1.0.0  
**Primary analysis unit:** local edge, not global aggregate.

---

## 1. Purpose

This pre-registration defines a native multilingual experimental matrix for evaluating inference-time logit interventions under TALM and TALON across three language-writing regimes:

1. Chinese native genesis and execution using InternLM2.5-1.8B-Chat.
2. Arabic MSA native genesis and execution using Jais-family-2.7B.
3. English native genesis and execution using Granite-4.1-3B.

The purpose is not to demonstrate global dominance of TALM or TALON. The purpose is to test whether specific operator candidates generate reproducible **local regimes of advantage** under segment-specific, rival-specific and metric-specific conditions.

The intended claim unit is:

```text
origin_suite × execution_language × model × segment × operator_candidate × decoder_rival × metric_edge
```

Global aggregate performance is treated as a diagnostic guardrail, not as the principal scientific object.


---

## 1.1. Prior architecture, provenance, and continuity with earlier pre-registration

This multilingual protocol is not an isolated post-hoc construction produced after observing the present experimental outputs. It is registered as a continuation of a broader pre-existing research architecture concerning inference-time logit modulation, local decoder behavior, post-hoc edge analysis, and stress-response taxonomies.

The following distinction is registered explicitly:

```text
formal pre-registration anchors
supporting provenance material
current multilingual pre-registration
```

### 1.1.1. Formal pre-registration anchors from the prior Phi/Nemotron/Phi execution line

The immediately prior TALM/TALON execution line was anchored before execution through frozen artifacts and public repository material. The relevant known hashes are:

```text
14d5fdb73ae70cda79112b8b671d6e17b37c82e5c91b7f836edbcb6f32f2e1d7  PRE_REG_TALM_TALON_NEMOTRON_PHI_FROZEN.zip
2c02a3ebc862500a3a2a73647062a95c877addb7b748a41b854ba4959f2b7dbe  TALM_TALON_Nemotron_Phi_PREREG_EXECUTION_PACKAGE.zip
```

The repository-level provenance previously included the file:

```text
pre_execution_hashes.md
```

under the GitHub repository:

```text
https://github.com/FacundoFirmenich/cfl_logitsprocessors
```

with the referenced commit:

```text
8ea2522
```

These anchors are registered here as prior continuity evidence for the experimental line that produced the Phi/Nemotron/Phi execution packages. They are not substituted for the current multilingual prompt-suite hashes, model-runtime manifests, or method-configuration hashes. The current multilingual matrix requires its own frozen artifacts and hashes.

### 1.1.2. Supporting provenance material

In addition to formal hash anchors, there exists abundant lower-formality provenance material, including chats, emails, documents, drafts, notebooks, conceptual outlines, and working notes. These materials are not treated as formal pre-registration in the strict sense. Their role is narrower and evidentiary:

```text
to support chronology, conceptual continuity, and architectural priority
```

They support the claim that the present outputs and analyses derive from a larger pre-existing architecture rather than being invented after the fact from the observed results.

The registered position is:

```text
The broader architecture predates the present factual experimental runs.
```

This broader architecture framed and motivated several later formalizations, including TALM/TALON-style logit intervention, Z_xpl-style local post-hoc edge analysis, and earlier related constructs such as NESE and ABTD. These constructs are not all part of the present execution scope, and their inclusion here is genealogical rather than evidentiary for the current multilingual results.

### 1.1.3. Scope of the provenance claim

The provenance claim does **not** imply that every later implementation detail, hyperparameter, model choice, or metric was already fixed in the older materials. It implies that the logical architecture, research direction, and local-edge orientation existed before the present runtime outputs.

The allowed provenance claim is:

```text
The present multilingual TALM/TALON/Z_xpl experiment is a specific operationalization of a broader pre-existing architecture.
```

The disallowed provenance claim is:

```text
All current results were predetermined or guaranteed by prior documents.
```

The prior materials may be used to establish continuity, motivation, and intellectual priority, but the validity of the present experimental claims must still be derived from the frozen prompt suites, runtime manifests, method hashes, generated outputs, and local Z_xpl analyses produced in this multilingual execution line.


---

## 1.2. Linguistic pre-execution layer: native prompt instantiation before model runtime

Before any TALM/TALON runtime execution, the multilingual protocol contains a distinct **linguistic pre-execution layer**. This layer is not model inference under TALM or TALON. It is the pre-runtime construction and freezing of native prompt suites.

This layer is registered explicitly because it determines the semantic and structural boundary conditions later received by InternLM, Jais, and Granite.

The linguistic pre-execution layer is defined as:

```text
common abstract conceptualities
→ native conceptual instantiation
→ frozen prompt suite
→ prompt-suite hash
→ model-runtime execution
```

The current protocol distinguishes three phases:

```text
Phase L0 - conceptual seed:
  shared abstract stress concepts and structural task families

Phase L1 - native linguistic instantiation:
  Chinese suite by ERNIE X1.1
  Arabic MSA suite by Falcon-family Arabic workflow, once fully repaired and frozen
  English suite by Claude/Sonnet-family workflow, once fully frozen

Phase L2 - runtime execution:
  TALM/TALON evaluation on InternLM, Jais, and Granite
```

Only Phase L2 produces experimental output rows. Phase L1 produces pre-execution linguistic artifacts. Those artifacts are not result data, but they are part of the experimental design and must be preserved because they define what the runtime models are asked to process.

### 1.2.1. Registered role of the linguistic pre-execution layer

The role of the linguistic pre-execution layer is to mitigate direct translation bias by preventing the experiment from becoming an English-authored benchmark merely rendered into other scripts.

The registered formulation is:

```text
native prompt-suite instantiation before runtime
```

not:

```text
translation-free proof of cultural neutrality
```

The linguistic pre-execution layer may reduce direct source-language contamination, but it cannot eliminate generator bias, training-data bias, tokenizer bias, or cultural priors embedded in the native generators.

### 1.2.2. Hash discipline for pre-execution linguistic artifacts

Each frozen native prompt suite must produce:

```text
raw_prompt_suite_file
raw_prompts_sha256
prompt_suite_hash
generator_chain_metadata
origin_language
execution_language
ground_truth_anchor_table, when applicable
```

Runtime output is inadmissible as primary evidence unless the corresponding linguistic pre-execution artifact is frozen and hashable.

### 1.2.3. Relation to "submerged properties"

The expected local behaviors in the multilingual matrix are not treated as spontaneous emergent properties discovered after execution. They are registered as **submerged properties**: latent, design-implied response patterns expected to become observable only after the runtime matrix unfolds.

A submerged property is defined as:

```text
a pre-runtime, design-derived expectation about where local TALM/TALON edges may become detectable, without asserting that the edge will necessarily appear.
```

Examples include:

```text
Chinese symbolic-structural compression may favor deterministic and sequential local edges.
Arabic MSA morphology may increase variance while preserving possible entropy-rescue edges.
TALON may produce broader edge distribution than TALM under fixed operator settings.
TALM may show more concentrated candidate behavior.
```

These are registered as pseudo-predictions derived from the design architecture, not as factual results.

---

## 2. Model registry

The planned execution models are:

| Language axis | Model ID | Role | Runtime note |
|---|---|---|---|
| Chinese / logographic axis | `internlm/internlm2_5-1_8b-chat` | Chinese native execution | Transformers-compatible; `trust_remote_code=True`; 1.8B-class model |
| Arabic MSA / root-pattern axis | `inceptionai/jais-family-2p7b` | Arabic MSA execution | Arabic-centric bilingual family model; `trust_remote_code=True`; 2.7B-class model |
| English / analytic axis | `ibm-granite/granite-4.1-3b` | English native execution baseline | 3B-class instruction-following model |

The earlier informal `<5B` threshold is treated as a pragmatic sizing convention, not a theoretical boundary. The registry remains valid if a model slightly exceeds that threshold only after explicit deviation logging. In the current selected set, all three target model IDs are within or near the intended small-model regime.


---

## 2.1. Model-selection rationale: non-canonical but solid native axes

The selected Chinese and Arabic models are intentionally not the most globally visible or most benchmark-saturated models in their respective ecosystems. This is a methodological choice.

For the Chinese axis, the experiment deliberately uses InternLM2.5-1.8B-Chat rather than the more internationally prominent Chinese model families that are likely to dominate mainstream open-source comparison circuits. In this context, such families include Qwen, DeepSeek, GLM, Kimi/K2, ERNIE and related high-visibility Chinese systems.

For the Arabic axis, the experiment deliberately uses Jais-family-2.7B rather than centering the design on Falcon-family models, which are treated here as the dominant or near-dominant reference point in the Arabic-oriented open-source model space.

The rationale is not that InternLM or Jais are uncontaminated, isolated, or culturally pure. No such claim is registered. The rationale is that using solid but less globally canonical models may reduce immediate coupling to the mainstream Anglo-Latin evaluation circuit and may provide a cleaner first-pass estimate of native-script decoder behavior under TALM/TALON interventions.

This choice creates a future contrast axis. After the initial runs, later experiments may compare the present model choices against more mainstream Sino-Arabic and globally circulated alternatives in order to estimate the degree to which apparent local edges are:

```text
model-family specific
language-topology specific
tokenizer specific
mainstream-training-circuit specific
or operator-specific
```

The registered expectation is therefore cautious:

```text
Using less canonical but capable native-axis models may reduce one source of mainstream benchmark contamination, while preserving enough model competence for meaningful local-edge testing.
```

This model-selection strategy is a contamination-control heuristic, not a proof of independence from Anglo-Latin training influence.


---

## 3. Prompt-suite design

The experiment uses 20 prompts per native suite, distributed into four structural blocks:

| Block | Count | Function |
|---|---:|---|
| Deterministic containment and state constraints | 5 | strict formatting, lexical veto, insufficiency detection, compression, structural mirroring |
| Complete traceability and sequential logic | 5 | finite-state machines, topological ordering, hidden fallacy localization, pseudocode transduction, matrix/index tracing |
| Stochastic diversity and latent-space expansion | 5 | orthogonal scenarios, interdisciplinary isomorphism, paradox synthesis, nonlinear extrapolation, atypical solution recovery |
| Complex correlation and systemic stress | 5 | game theory, feedback loops, Bayesian updating, cascade failure, multiscale invariants |

The Chinese ERNIE-generated suite is considered locked for the Chinese axis. Arabic MSA and English native suites must be frozen before runtime with their own prompt-suite hashes. No results from an incomplete or placeholder prompt suite will be admitted as primary evidence.

---

## 4. Native genesis principle

The prompt suites are not treated as literal translations of a single English source. The design starts from shared abstract conceptualities, but each final suite must be generated as a native conceptual instantiation inside its own language-writing regime.

This distinction is essential. The experiment does not claim to eliminate cultural or training-distribution bias. Instead, it aims to reduce the specific confound produced by direct translation from a single source language.

The registered formulation is:

```text
native conceptual instantiation from common abstract constraints
```

not:

```text
literal translation equivalence
```

Therefore, the experiment tests logit-intervention stability under native linguistic topologies, while explicitly acknowledging generator bias, model-family bias, tokenizer bias, and writing-system effects as residual uncertainties.

---

## 5. Main hypotheses

### H1 — No global dominance prediction

We do **not** predict global dominance of TALM or TALON over all standard decoders.

Global summaries may be reported, but they cannot support claims of overall superiority unless a separately registered global criterion is met. The default expectation is that strong standard controls, especially repetition penalty or no-repeat-ngram controls, may dominate several aggregate metrics.

### H2 — Local-edge dominance regimes

We predict local regimes of advantage, especially where the operator modifies the probability distribution without fully reproducing the behavior of high-temperature or high-repetition-penalty decoders.

A valid local regime requires evidence at the level of:

```text
segment × candidate × decoder_rival × metric_edge
```

The expected successful result is not “TALM/TALON wins globally”; it is:

```text
candidate_ci_supported local edge with positive margin and interpretable telemetry
```

### H3 — TALON distribution hypothesis

Based on prior Phi-4 runs, TALON is expected to produce a more distributed local-edge topology than TALM. TALM is expected to show more concentrated candidate behavior, while TALON may show broader but segment-dependent responses.

This is a directional expectation, not a guaranteed claim. It will be tested independently for each model-language axis.

### H4 — No expected systematic linguistic degradation

We do not pre-register an expectation of systematic degradation merely because the prompt is Chinese or Arabic rather than English. On the contrary, we allow the possibility that non-English writing systems may reveal operator advantages that are muted in English.

This hypothesis is deliberately local: it concerns the probability of detecting segment-specific, rival-specific operator edges, not global model performance.

### H5 — Chinese logographic compression hypothesis

For the Chinese axis, we pre-register a stronger exploratory hypothesis: the ideographic/logographic writing regime may improve local operator detectability by reducing sequence fragmentation and increasing semantic density per generated unit.

This is not a claim that Chinese characters are literally binary or quaternary encodings, nor a claim that all Chinese characters are pure ideograms. It is a model-side information hypothesis about the interaction between:

1. character-level graphic-semantic compression,
2. tokenizer segmentation,
3. per-step logit perturbation,
4. cumulative decoding error.

The heuristic “8 → 64 → 4096” is formalized as a latent compositional codebook hypothesis:

```text
8 primitive graphic-informational classes
64 meso-compositional signatures
4096 higher-order symbolic-graphic configurations
```

This is used as an abstract combinatorial model, not as a paleographic assertion. The intended empirical test is whether Chinese native execution shows stronger or cleaner local Z_xpl margins under TALM/TALON for constraints involving structure, sequence, and symbolic transformation.

---

## 6. Formal derivation of the Chinese compression hypothesis

Let a prompt-response task carry an abstract semantic load \(S\). Let \(T_L(S)\) be the number of generated tokens required by language/runtime \(L\) to express or satisfy the task. Let \(\lambda_L\) be the per-step probability of a constraint-relevant decoding failure under a fixed decoding regime.

A minimal hazard model gives:

```text
P(no failure | L, S) ≈ exp(-λ_L · T_L(S))
```

If Chinese native execution yields lower effective sequence length for the same structural constraint, and if \(\lambda_L\) does not increase enough to offset this reduction, then the probability of maintaining a strict constraint may improve.

Let \(C_L = I(S) / T_L(S)\) be a crude semantic-density coefficient, where \(I(S)\) is the information load of the task. A logit processor acts at the token-distribution level:

```text
p_t(v) → p'_t(v)
```

When \(C_L\) is higher, a successful local perturbation may move probability mass among more semantically loaded units. This can amplify local surface effects measured by:

```text
z_xpl_score_margin
distinct_2_delta
bigram_repetition_reduction
token_entropy_delta
ratio_vs_control
```

The “octofundamental” 8 → 64 → 4096 notation is therefore interpreted as a nested symbolic-combinatorial prior:

```text
b = 8 primitive graphic-information classes
b² = 64 local compositional pairings
b⁴ = 4096 high-order graphic-semantic signatures
```

The prediction is not that the Unicode system or the historical Chinese writing system is literally organized this way. The prediction is that a compressed graphic-symbolic writing regime may interact favorably with token-level logit perturbation by changing the effective granularity of semantic movement in the decoder.

The empirical observable is:

```text
positive local margins in Chinese native execution, especially in deterministic, sequential, and symbolic-structural segments
```

---

## 7. Arabic MSA uncertainty hypothesis

The Arabic axis is expected to increase uncertainty due to root-pattern morphology, clitics, orthographic variation, right-to-left rendering, and tokenizer segmentation. This does not imply expected degradation.

We pre-register the following cautious expectation:

```text
Arabic MSA may produce higher variance in token-level metrics but still exhibit local TALM/TALON edges under deterministic containment, sequential logic, and entropy-preservation metrics.
```

All Arabic outputs must be serialized with Unicode-safe encoding and raw text preservation. Any analysis requiring whitespace-defined word counts must be treated as secondary, not primary.

---

## 8. Metrics and primary edges

The primary post-hoc edge metrics are:

```text
z_xpl_score_margin
distinct_2_delta
bigram_repetition_reduction
token_entropy_delta
mean_ratio_vs_control
sequence_distance
jaccard_distance
```

The main confirmatory label is:

```text
candidate_ci_supported
```

A local candidate edge is considered supported when its bootstrap paired confidence interval excludes zero in the predicted direction, subject to sufficient valid pair count and no runtime contamination.

No blind human-quality claim is allowed unless a non-empty blind A/B candidate file is explicitly produced and analyzed under a separately registered procedure.

---

## 9. Decoder controls and candidates

Each notebook must retain the same method topology unless a deviation is logged.

### Reference controls

```text
baseline
baseline_control
```

### Standard decoder rivals

```text
std_temperature_low
std_temperature_high
std_top_p_low
std_top_p_high
std_repetition_penalty
std_no_repeat_ngram_3
std_temperature_eff_match, when available
```

### TALM candidates

```text
talm_mass_right_soft
talm_mass_left_soft
talm_hybrid_right_mid
talm_balanced_high
```

### TALON candidates

```text
talon_mass_right
talon_mass_left
talon_hybrid_right
talon_hybrid_balanced
```

All claims must name the rival decoder explicitly.

---

## 10. Ground-truth anchors

Some prompts are structural or stylistic and do not possess a single scalar ground truth. Others do.

Ground-truth prompts must be registered per suite because native suites may instantiate different numerical parameters. For example:

### Chinese ERNIE P18

```text
P(H) = 0.15
P(E|H) = 0.92
P(E|¬H) = 0.08
P(¬H) = 0.85
P(E) = 0.92×0.15 + 0.08×0.85 = 0.206
P(H|E) = 0.138 / 0.206 = 0.6699029126
Rounded to four decimals: 0.6699
```

### English Claude P18, if using the D-defect variant

```text
P(D) = 0.04
P(+|D) = 0.92
P(+|¬D) = 0.08
P(¬D) = 0.96
P(+) = 0.92×0.04 + 0.08×0.96 = 0.1136
P(D|+) = 0.0368 / 0.1136 = 0.3239436620
Rounded percentage: 32.39%
```

No scalar correctness metric may be shared across suites unless the numerical parameters are identical.

---

## 11. Uncertainty and limitations

We pre-register increased uncertainty in the Chinese and Arabic axes because the experiment adds several sources of variance:

```text
native prompt generator bias
model-family bias
tokenizer segmentation
script morphology
Unicode normalization
right-to-left rendering for Arabic
prompt-suite non-equivalence beyond abstract conceptuality
ground-truth parameter differences between native instantiations
```

This uncertainty does not invalidate the experiment. It limits claims to local, hashed, runtime-specific findings.

---

## 12. Exclusion and deviation rules

A run or row may be excluded from primary analysis if:

1. model loading fails or uses an unregistered fallback;
2. generated status is not `ok`;
3. runtime produces meta tensors or device-map contamination;
4. the prompt suite differs from the frozen hash;
5. the method configuration differs from the frozen hash;
6. the output file is corrupted or cannot be parsed;
7. a placeholder prompt is discovered after execution;
8. a metric is synthetic, mocked, or not derived from actual generated tokens/logits.

All exclusions and deviations must be listed in a runtime manifest.

---

## 13. Custody artifacts

Each execution must preserve:

```text
prompt_suite_hash
raw_prompts_sha256
method_config_hash
standard_control_hash
operator_method_config_hash
notebook_sha256_at_runtime, if available
model_id
model_label
engine
engine_version
run_started_utc
n_rows
planned_rows
deviations_count
save_every
runtime_device
quantization_config
```

The expected row count per single-engine notebook is:

```text
20 prompts × 3 seeds × 13 methods = 780 rows
```

If a method count differs, the reason must be recorded.

---

## 14. Claim policy

Allowed claim type:

```text
local candidate edge under a specified model, language, segment, rival decoder, and metric
```

Disallowed claim types unless separately demonstrated:

```text
global dominance
language-universal dominance
human-quality superiority
translation-bias elimination
cultural-bias elimination
proof of intrinsic writing-system superiority
```

The preferred result language is:

```text
TALM/TALON produced candidate_ci_supported local edges in [segment] against [rival] on [metric], under [model/runtime/prompt-suite hash].
```

---

## 15. Pre-registered expected pattern

The expected qualitative pattern is:

1. TALM may show concentrated local edges.
2. TALON may show more distributed local edges.
3. Chinese native execution may show favorable local margins in symbolic, deterministic, and sequential segments due to compressed graphic-symbolic token regimes.
4. Arabic MSA may show higher variance but may still produce local entropy-preservation and constraint-rescue edges.
5. English Granite execution will serve as a general instruct baseline for native English structural prompts.
6. No global dominance is expected or required.

---

## 16. Repository note

This document is intended for GitHub upload before final multilingual runtime execution. Any later change to model ID, prompt suite, candidate list, standard control list, or Z_xpl criterion must be committed as a new protocol version rather than silently edited into this registration.

**End of pre-registration.**
