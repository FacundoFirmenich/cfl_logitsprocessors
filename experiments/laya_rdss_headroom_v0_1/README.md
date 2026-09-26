# Laya × RDSS headroom sensor replay v0.1

This experiment replaces the authenticated TypeSafe Jev API with the open-weight **Laya `typed-decisions` checkpoint** and evaluates the missing RDSS question: can a cheap external typed-decision sensor concentrate the sparse residual headroom left by a strong fixed authority?

## Scientific boundary

- Real data only: 18 adjudicable Qwen3.5 cases from the frozen historical Human-Eval matrix, paired with the already-executed seed-14 CFLDR pre-route mechanical fingerprints.
- No synthetic cases, labels, or model outputs.
- Laya never receives `evaluation_only`, human utility, oracle identity, or headroom.
- This is a **retrospective sensor replay**, not a prospective authority claim.
- Laya receives **sensor authority only**, never execution authority.

## Frozen ablations

1. `prompt_only`: exact prompt + cheap task metadata.
2. `mechanics_only`: task metadata + obfuscated pre-route TALM/TALON mechanical fingerprints.
3. `prompt_plus_mechanics`: both.

Branch names are hidden from Laya. `D0` is the frozen default representative; `C1...C5` are opaque candidate probes.

The primary output is the Noul probability for **default insufficiency**. A separate typed Choice always includes `ABSTAIN_UNCERTAIN`; the same Choice is rerun with reversed option order to measure order sensitivity. Complementary Noul questions measure internal probability coherence.

## Primary metrics

For materiality thresholds `epsilon ∈ {0, 0.5, 1.0}`:

- HCI (Headroom Concentration Index)
- Headroom Recall / Density at top 10%, 20%, 30%, 50%
- AUROC, Brier, NLL for material rescue labels
- Noul complement error
- Choice option-order TV / flip rate

Two existing ex-ante CFLDR quantities are scored as internal comparators, but are **not** passed into the Laya state.

## Reproducibility

The workflow is CPU-only, needs no TypeSafe/Jev account, no TypeSafe API key, and no Hugging Face token for the public checkpoint. It records raw responses, hashes, timings, package version and metrics as a GitHub Actions artifact.
