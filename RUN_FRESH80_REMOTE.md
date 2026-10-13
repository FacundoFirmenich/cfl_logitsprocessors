# TÁLAMO — FRESH80 remote execution gate

Este documento fija el gate material correcto para ejecutar FRESH80 fuera del sandbox local.

## Principio operativo

FRESH80 no debe ejecutarse en CPU local ni en un runtime sin GPU/Hugging Face/cache suficiente. El gate material correcto es:

1. **Kaggle GPU**: vía notebook/kernel con GPU activada, preferente para corrida completa.
2. **Colab GPU**: fallback manual si Kaggle no está disponible.
3. **GitHub Actions con self-hosted GPU runner**: válido sólo si existe runner propio con GPU.
4. **GitHub Actions hosted**: válido sólo para preflight, empaquetado, orquestación Kaggle, descarga de artefactos y análisis; no para 12.000 generations sobre modelos HF.

## Jobs esperados

- `TALM_Qwen35_2B_FRESH80`: 2.880 generaciones.
- `TALON_Qwen35_2B_FRESH80`: 3.120 generaciones.
- `TALM_Gemma4_E2B_FRESH80`: 2.880 generaciones.
- `TALON_Gemma4_E2B_FRESH80`: 3.120 generaciones.

Total: **12.000 generations**.

## Reglas fail-closed

No se permite:

- fabricar outputs;
- usar datos sintéticos para simular corrida;
- cambiar prompts sin registrar hash;
- tocar hiperparámetros entre confirmation runs;
- mezclar resultados de corridas incompletas como si fueran cierre final;
- reemplazar generación real por métricas proxy.

Si falta `prompts/FRESH80_prompts_v1.json`, notebooks, modelos o GPU, el workflow debe abortar antes de producir resultados.

## Ruta A — Kaggle GPU desde GitHub Actions

Workflow: `.github/workflows/talamo_fresh80_kaggle_submit.yml`

Requiere secrets del repo:

- `KAGGLE_USERNAME`
- `KAGGLE_KEY`
- `HF_TOKEN` si el modelo lo requiere

El workflow crea un directorio Kaggle ejecutable, escribe `kernel-metadata.json`, sube el kernel con `kaggle kernels push` y deja el run trazado. Kaggle es el runtime que ejecuta la GPU; GitHub Actions sólo orquesta.

## Ruta B — GitHub self-hosted GPU

Workflow: `.github/workflows/talamo_fresh80_selfhosted_gpu.yml`

Requiere runner propio con labels:

```text
self-hosted, linux, x64, gpu
```

Sin ese runner, el workflow no debe usarse para corrida completa.

## Ruta C — Colab

Usar los notebooks FRESH80 ya preparados. Colab sirve como fallback operativo, pero el cierre debe exportar JSONL/CSV crudos y manifest SHA-256 para que el análisis posterior sea reproducible.

## Cierre esperado del gate

Una ejecución válida deja como artefactos mínimos:

```text
results/fresh80/raw/*.jsonl
results/fresh80/tables/*.csv
results/fresh80/manifests/*.json
results/fresh80/SHA256SUMS.txt
```

Luego corre:

```bash
python -m talamo.cli complementarity --input results/fresh80/raw --out results/fresh80/analysis/complementarity
python -m talamo.cli zxpl --input results/fresh80/raw --out results/fresh80/analysis/zxpl
```

El cierre material no es el submit remoto. El cierre material es: outputs crudos + hashes + análisis confirmatorio + tabla de claims.
