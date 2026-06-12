# Submerged-Property Map — Native Multilingual TALM/TALON v1.0

**Document ID:** `SUBMERGED_PROPERTY_MAP_NATIVE_MULTILINGUAL_TALM_TALON_V1`  
**Relation to main protocol:** compact companion to `PREREG_TALM_TALON_NATIVE_MULTILINGUAL_MATRIX_V1_1_LINGUISTIC_PREEXEC.md`  
**Date:** 2026-06-12  
**Status:** pre-runtime certainty/uncertainty/expectation map.

---

## 1. Scope

This document maps the **certainties, uncertainties, expectables, and design-derived pseudo-predictions** of the native multilingual TALM/TALON matrix.

It does not report results. It does not add new hypotheses outside the main pre-registration. It isolates what may be called **submerged properties**: expectations already implicit in the design before empirical execution.

A submerged property is not an observed effect. It is a latent design-implied pattern that may or may not surface after runtime.

---

## 2. Linguistic pre-executions

The protocol contains pre-runtime linguistic executions, meaning native prompt-suite instantiations performed before model inference.

```text
L0: common conceptual seed
L1-ZH: ERNIE X1.1 native Chinese instantiation
L1-AR: Falcon-family Arabic MSA instantiation, admissible only after repair/freeze
L1-EN: Claude/Sonnet-family English instantiation, admissible only after freeze
L2: TALM/TALON runtime execution
```

L1 artifacts are not results. They are design-bearing artifacts and must be hashed.

---

## 3. Certainties fixed before runtime

| ID | Certainty | Status |
|---|---|---|
| C1 | The claim unit is local edge, not global dominance. | fixed |
| C2 | TALM/TALON are inference-time logit operators. | fixed |
| C3 | Z_xpl is post-hoc local edge analysis, not an independent decoder. | fixed |
| C4 | Each notebook must preserve model ID, prompt hash, method hash, runtime manifest and row status. | fixed |
| C5 | The Chinese ERNIE suite is a native pre-execution linguistic artifact, not a translation of an English prompt list. | fixed for ZH |
| C6 | Arabic and English suites must be treated as independent native pre-execution artifacts once fully locked. | pending/frozen per suite |
| C7 | No blind human-quality claim is allowed unless blind A/B data exists. | fixed |
| C8 | No global dominance is expected or required. | fixed |

---

## 4. Principal uncertainties

| ID | Uncertainty | Consequence |
|---|---|---|
| U1 | Tokenization differs sharply across Chinese, Arabic and English. | token-level metrics are operational, not directly linguistic |
| U2 | Native prompt generators carry their own training biases. | native instantiation mitigates translation bias but does not eliminate bias |
| U3 | Same TALM/TALON strength may have different effective force across models. | operator-strength drift must be interpreted cautiously |
| U4 | Arabic MSA morphology and clitics may increase metric variance. | Arabic local edges may be noisier |
| U5 | Small models may show instruction-following failures unrelated to operator quality. | format failures must be tracked separately |
| U6 | Model cards and runtime implementations may require chat templates or remote code. | smoke tests are mandatory |
| U7 | 4-bit quantization may alter logit geometry. | quantized runtime is part of the registered condition, not a neutral substrate |

---

## 5. Expectables by language-writing regime

### 5.1 Chinese / logographic axis

Expected favorable zones:

```text
deterministic_constraint
sequential_logic
symbolic-structural transformation
P18-like analytic anchors
```

Design-derived expectation:

```text
Chinese native execution may produce cleaner local edges where high semantic density and compact symbolic units reduce cumulative sequence hazard.
```

Registered caution:

```text
This is a hypothesis about model-tokenizer-decoder behavior, not a claim about intrinsic superiority of Chinese writing.
```

### 5.2 Arabic MSA / root-pattern axis

Expected favorable zones:

```text
entropy preservation
constraint rescue
sequential traces if prompt is fully specified
local margins under repetition/top-p rivals
```

Design-derived expectation:

```text
Arabic may show higher uncertainty but still expose local TALM/TALON edges where controls collapse into repetition or morphological drift.
```

Registered caution:

```text
Whitespace and word-level diversity metrics are secondary for Arabic unless normalized.
```

### 5.3 English / analytic baseline axis

Expected favorable zones:

```text
format compliance
Bayesian and cascade ground-truth anchors
formal sequential tasks
direct comparison against standard decoders
```

Design-derived expectation:

```text
English Granite execution should serve as the most legible baseline for validating whether the prompt architecture itself is coherent.
```

Registered caution:

```text
Granite is multilingual and not an English-only pure control.
```

---

## 6. Expectables by operator

### TALM

Expected topology:

```text
more concentrated local edges
candidate-specific activation
possible strong response in tail-sensitive creative or symbolic tasks
```

Submerged property:

```text
TALM may reveal narrow but interpretable local edge regimes.
```

### TALON

Expected topology:

```text
more distributed local edges
broader response surface
candidate family duplication possible, especially between hybrid variants
```

Submerged property:

```text
TALON may reveal a wider but more heterogeneous local edge map.
```

---

## 7. Pseudo-predictions before runtime

These are not claims. They are explicit pre-runtime expectations.

| ID | Pseudo-prediction | Testable observable |
|---|---|---|
| P1 | No global dominance will be necessary or expected. | global table may show no_global_win |
| P2 | Local edges will be more informative than aggregate means. | candidate_ci_supported rows by segment/rival |
| P3 | Chinese deterministic/sequential blocks may show favorable margins. | positive Z_xpl margins in ZH deterministic/sequential segments |
| P4 | Arabic may show larger confidence intervals. | wider bootstrap CI ranges in AR than EN/ZH |
| P5 | TALON may produce more distributed supported edges than TALM. | larger segment coverage in TALON local edge table |
| P6 | TALM may show fewer but sharper edges. | lower edge count but higher peak margin in some segments |
| P7 | `std_repetition_penalty` may remain a strong aggregate rival. | no global win against repetition penalty possible |
| P8 | Ground-truth anchors may expose logical degeneration under strong perturbation. | P18/P19 correctness failures by method |
| P9 | Chat template compliance is critical for InternLM and Granite. | smoke-test success/failure and prompt compliance |
| P10 | Tokenizer-normalized interpretation will be required. | metric tables stratified by token counts/character counts |

---

## 8. Excluded overclaims

The submerged-property map explicitly excludes:

```text
proof of cultural neutrality
proof of writing-system superiority
proof of global TALM/TALON dominance
proof that native generators are unbiased
claim that linguistic uncertainty disappears
claim that Z_xpl is a human-quality measure
```

---

## 9. Minimal result language after execution

Allowed language:

```text
Under model M, language L, prompt suite hash H, candidate C produced a candidate_ci_supported local edge against rival R on metric E within segment S.
```

Preferred interpretation:

```text
This surfaces a submerged design-predicted local regime.
```

Disallowed interpretation:

```text
This proves universal superiority of the operator or language.
```

---

## 10. Hashing note

This document is intended to be hashed and uploaded alongside the main pre-registration. It is smaller than the full protocol and can serve as a quick public map of what was expected before runtime.

**End of document.**
