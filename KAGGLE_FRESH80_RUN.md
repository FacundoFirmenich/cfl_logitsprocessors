# TÁLAMO — Kaggle FRESH80 run

Kaggle es la ruta preferente para la corrida completa cuando no hay self-hosted GPU runner en GitHub.

## Setup mínimo

1. Crear un notebook Kaggle privado.
2. Activar GPU.
3. Activar internet.
4. Subir el zip `TALAMO_FRESH80_EXEC_READY_v0_3.zip` como input dataset privado o copiar el repo completo.
5. Definir `HF_TOKEN` como Kaggle secret si algún modelo lo requiere.

## Ejecución canónica

Ejecutar en este orden:

```text
TALM_Qwen35_2B_FRESH80.ipynb
TALON_Qwen35_2B_FRESH80.ipynb
TALM_Gemma4_E2B_FRESH80.ipynb
TALON_Gemma4_E2B_FRESH80.ipynb
02_TALAMO_complementarity_router.ipynb
04_TALAMO_Z_xpl_batch.ipynb
03_TALAMO_blind_semantic_eval.ipynb
```

## Outputs mínimos obligatorios

```text
results/fresh80/raw/*.jsonl
results/fresh80/tables/*.csv
results/fresh80/analysis/**
results/fresh80/manifests/*.json
results/fresh80/SHA256SUMS.txt
```

## Criterio de validez

La corrida sólo queda cerrada si:

- las cuatro familias completan el número esperado de generaciones;
- los prompts conservan hash registrado;
- cada salida queda en JSONL crudo;
- los CSV agregados derivan de los JSONL;
- hay manifest con modelos, seeds, hiperparámetros y SHA-256;
- no hay filas fabricadas ni proxies.

Si un notebook se corta, se retoma desde checkpoint. Si un checkpoint no permite trazabilidad, se descarta y se relanza el job.
