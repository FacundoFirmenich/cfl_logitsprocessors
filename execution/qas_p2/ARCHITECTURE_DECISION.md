# QAS-P2 architecture decision after execution

Let `C_t` be the pre-operator top-64 baseline candidate set and `S_t` the exact
QAS support.

Measure

[
R_{64,t}=|C_tcap S_t|/|S_t|.
]

This metric is descriptive of the executed heuristic support, not a proof of
causal necessity.

## Branch A — reranker regime

If held-out candidate recall is sufficiently high under a threshold frozen
before evaluation, train a candidate-membership ranker over `C_t` and certify
its proposed support against full intervention fidelity.

## Branch B — generator regime

If a material fraction of support lies outside `C_t`, the baseline candidate
pool is structurally insufficient for exact-mask imitation. Add a candidate
generator using only ex-ante information (for example support memory or cheap
microprobes), then repeat the observability/identifiability gate.

## Stronger endpoint

Do not make exact imitation of `S_t` the final scientific target unless support
uniqueness/minimality is established. Prefer a fidelity-qualified quotient

[
[S]_F={S':Phi_F(S')=Phi_F(S)}
]

and optimize cost subject to the chosen fidelity and robustness constraints.
