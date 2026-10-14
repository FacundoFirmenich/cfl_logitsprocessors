# QAS-P2 v3.8 GPU execution matrix

## What is frozen

This package preserves the label-complete Qwen3.5-4B campaign:
- model `Qwen/Qwen3.5-4B`;
- revision `851bf6e806efd8d0a36b00ddf55e13ccb7b8cd0a`;
- 20 frozen prompts, seeds `[11,22,33]`;
- exact QAS support IDs;
- pre-operator top-64 candidate IDs/probabilities;
- embedded v3.8 runtime;
- SQLite/WAL transactional campaign state;
- no event rerouting;
- authority boundary: evidence only.

It adds schema-valid `qas.p2.evidence.v1` receipts and the frozen structural test
`S_t ⊆ C_64,t` for every audited step.

## Execution lanes

### Lane A — GitHub Actions CPU preflight
Standard `ubuntu-latest`. No scientific GPU claim. It reconstructs the portable
notebook from frozen chunks, validates exact SHA/hashes/invariants, and materializes
the notebook on this branch for direct Colab use.

### Lane B — GitHub Actions self-hosted GPU
Workflow: `.github/workflows/qas_p2_label_complete_selfhosted_gpu.yml`.
It is triggered only by changing `execution/qas_p2/TRIGGER_GPU` and requires a
runner labeled:

`self-hosted, linux, x64, gpu`

plus `HF_TOKEN` if Hugging Face requires authentication.

### Lane C — Google Colab GPU
Open `notebooks/RDS_V3_8_QAS_P2_LABEL_COMPLETE_QWEN35_4B_COLAB_GPU.ipynb`
from this GitHub branch in Colab, select a GPU runtime, add `HF_TOKEN` as a
Colab secret if needed, and Run All. If the frozen stack is repaired, Colab
restarts once; Run All again after reconnect.

Colab hardware and usage limits are not assumed or encoded in scientific claims.

## Closure criterion

A GPU run is not accepted merely because the notebook reaches the end.
`scripts/qas_p2_validate_results.py` must pass over the final ZIP.

Required new artifacts:
- `qas_p2_evidence_receipts.jsonl`
- `qas_p2_universal_top64_test.json`
- `qas_p2_receipt_manifest.json`

No result is preregistered as positive.
