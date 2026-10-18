# CFL/RDSS Canon Recovery v2.0.0

## Estado

`PASS_RDSS_SEPTEMBER_PRIMARY_RECOVERY + PASS_GENEALOGY_RECONSTRUCTION + PASS_STATIC_PREFILL_NONIDENTIFIABILITY + DIRECTCOMP_RAW_GATE_OPEN`

Esta rama corrige el canon parcial anterior. **RSS nunca existió**: fue una mistranscripción del asistente y queda eliminado retroactivamente de toda genealogía, diagrama, registro y roadmap. No puede usarse como alias de RDS, RDSS, CFLDR, QAS, CAS ni de ningún otro componente.

## Genealogía canónica multieje

```text
CFL
├── TALM / TALON operator families
├── DIRECTCOMP (engine y campaña comparativa propia)
├── CFL_probe
├── CFL_dr mechanistic v0.3
│   ├── responder states
│   ├── Top-2
│   └── Z_PH post-hoc
├── CFLDR Plus v0.4
│   ├── preroute
│   ├── inline control
│   ├── support/OOD
│   └── blind evaluation / oracle ceiling
├── RDS engineering
│   ├── v1.2 unified
│   ├── v1.2.3 P100
│   ├── v1.3.1 three modes
│   └── v1.4.1 package / v1.4.0 runtime
├── RDS experimental
│   ├── RDS-944 fail-closed
│   ├── v3.3 QAS null / prior collapse
│   └── v3.5 post-warper QAS FINAL252
├── Bayesian RDS v0.2 priors
├── RDSS Qwen3.5 candidate-only Dual-T4 v2.1
│   ├── MERGED_COMPLETE_240_FINAL
│   ├── CPU rebuild / historical regression
│   ├── CPU interpretation
│   ├── semantic witness
│   ├── P09 conditional semantics
│   ├── local jurisdiction graph
│   ├── prefill-resolution audit
│   └── stage-local mechanical analysis
├── RDSS v2.4 assurance
├── QAS v3.8.2 / QAS-P2
└── CAS / KCH external authority and receipts
```

No es una única escalera de versiones. Ingeniería, campañas experimentales, priors bayesianos, assurance, localización de soporte y cartografía post-hoc son ejes distintos y no se superseden automáticamente.

## Bytes primarios RDSS septiembre recuperados

El artefacto exacto `MERGED_COMPLETE_240_FINAL.zip` fue recuperado desde MyDrive:

- SHA-256: `f0aa4df1c588a72adcde3942dd03ad7061e0ae6a999caaadd24b5dfb99423cb3`;
- 409.298 bytes;
- 24 miembros;
- 22/22 miembros del manifest interno verificados;
- 240 celdas prompt–seed–acción únicas;
- 18 prompts;
- seeds 11, 22 y 33;
- 0 errores;
- 0 think-tags;
- 0 flips post-proyección;
- integridad SQLite `ok`.

También fueron recuperados y hasheados siete sucesores forenses: CPU rebuild, CPU interpretation, semantic witness, P09 conditional semantics, local jurisdiction graph, prefill resolution y stage-local analysis.

## Cociente efectivo acción–rol

`talm_right_high` y `talon_head_right` producen exactamente el mismo output final en las 54 unidades prompt–seed compartidas. Bajo el operador observacional `final_text` constituyen una única acción generativa efectiva en esta campaña.

Sin embargo, sus fingerprints contrafactuales permanecen distintos. La distancia multifeature estandarizada media entre ambos probes sobre los 18 prompts es `2.584927`.

Por tanto:

```text
probe_action != generation_action
```

El action registry debe quotientar por observación **y por rol**; no basta contar nombres de ramas.

## Mecánica y utilidad no son equivalentes

En el probe primario p01, TALON mass-left y mass-right generan cambios distribucionales grandes —TV aproximadamente 0,169/0,176 y KL aproximadamente 0,089/0,077— preservando top-1. Los brazos TALM soft y head son casi nulos en esa celda. Left y right mueven la entropía en direcciones opuestas.

Eso certifica actividad mecánica y diferenciación de probe; no utilidad semántica.

## Diagnóstico del router histórico

La reconstrucción CPU reúne 378 observaciones sin regenerar texto: 138 filas históricas seleccionadas y 240 filas G0. La regresión histórica contiene 252 filas y cero mismatches.

En el score contractual legado:

- baseline: `0.567708`;
- talon_mass_right: `0.567708`;
- talm_right_high / talon_head_right: `0.557292`;
- talm_mass_left_soft: `0.546875`;
- talm_mass_right_soft: `0.526042`;
- talon_mass_left: `0.505208`.

El router histórico congelado obtiene `0.5625` frente a `0.567708` del baseline: 2 wins, 2 losses y 44 ties. El hindsight upper bound `0.651042` es post-hoc, mezcla procedencias y no es un router desplegable. Excluyendo los verificadores débiles p09/p15, baseline queda primero en todas las comparaciones.

## Testigos semánticos y límites

- p09: 10 programas pasan los inputs probados, 8 quedan semánticamente/subconjuntamente irresueltos y 3 poseen contraejemplos numéricos.
- Las interpretaciones condicionales posteriores preservan varias convenciones posibles; no corrigen silenciosamente el dialecto.
- p15 recibe testigo primal/dual exacto, pero 21/21 outputs alcanzan max tokens y 0/21 EOS.

La evaluación contractual histórica es parcial y no debe tratarse como utilidad semántica total.

## Cartografía local

El grafo jurisdiccional contiene:

- 378 nodos;
- 54 contextos prompt–seed completos;
- 2.268 relaciones dirigidas;
- 252 aristas blind excluidas de adjudicación.

Ordena cuatro componentes contractuales históricos; no calidad semántica completa. `talon_mass_right` en p15 domina baseline en las tres seeds observadas, pero p15 pertenece a una región de evaluador débil. Es una hipótesis local, no una jurisdicción validada.

## No-identificabilidad del prefill estático

La auditoría de resolución prefill encuentra 33 conflictos locales sobre 10 prompts. La misma representación prompt–acción, con settings fijos, conduce a distintos vectores contractuales según seed/trayectoria.

Así, en esas celdas observadas no existe una función determinista identificada:

```text
static_prefill_fingerprint -> exact_contract_vector
```

El RDSS prospectivo debe estimar una distribución condicionada e incluir trayectoria, estado responder, soporte/OOD e incertidumbre; o abstenerse.

## Análisis por etapas

El analizador distingue:

1. sin efecto observado;
2. diferencia eliminada por la proyección común;
3. diferencia eliminada por los warpers efectivos;
4. diferencia presente después de warpers.

Formaliza que, sobre soporte finito común, dos logits producen exactamente la misma softmax si y sólo si difieren por una constante. El software pasa 17 tests y 10 subtests. La ejecución científica sobre tensores Qwen reales permanecía abierta en ese release; sus fixtures son sólo de software.

## DIRECTCOMP

DIRECTCOMP es un objeto separado:

- Qwen3.5-4B-Base;
- 480/480 outputs;
- locked-20 hash `187e3f676685389601bce68126044c131f1ce4aec6a89104f44091446d7bd5f3`;
- budget 384, prompt mode direct;
- TALM/TALON versus Min-P, p-LESS, Min-K y controles estándar.

La evidencia E3 recuperada autoriza sólo:

- no hay victoria contractual CFL en ese protocolo;
- las seis comparaciones superficiales retenidas son `no_local_win`;
- `std_repetition_penalty` es un rival fuerte en distinct-2, repetición y entropía.

No autoriza inferioridad semántica de CFL. El bundle primario de 480 outputs aún no está montado, por lo que el bootstrap no se declara reproducido.

DIRECTCOMP no es COMPETITOR944, G0 ni RDS-944.

## Próximo gate verdadero

El experimento prospectivo no empieza hasta montar y hashear:

1. DIRECTCOMP 480-output bundle y las dos slices no idénticas del local-claim table;
2. RDS v3.5 FINAL252 completo con coordenadas exactas QAS;
3. CFLDR Plus v0.4 multi-seed y reviewer-corrected;
4. resultados QAS v3.8.2/QAS-P2 si existen; en otro caso siguen siendo preregistración.

El portfolio debe incluir baseline, controles externos comparables, TALM/TALON quotientados por rol, ABTD/HPDC, Top-2, probe-only, ASK y ABSTAIN.

Políticas comparadas en un holdout future-only:

- baseline;
- mejor acción fija;
- mejor externo fijo;
- heurística RDS v3.5;
- Bayesian RDS v0.2;
- CFLDR preroute;
- CFLDR inline;
- RDSS canónico CAS-E → QAS-pre → CAS-V → lease externo;
- Top-2;
- oracle exclusivamente post-hoc.

Promoción sólo si reduce regret local frente a baseline y mejor acción fija comparable, sin aumentar false-active/OOD/CAS violations, y si el gain sobrevive reporte jurisdiccional, no sólo una media agregada.

## Autoridad

`authority = NONE`. Esta rama es un recovery/audit draft; no se fusiona ni promueve automáticamente.
