# CFL macro P/C gate v0.5.2 — admissibility protocol

## Source benchmark

Recovered from `CFLDECODER_V2_p01_p10_constraints_sequence.ipynb`, prompt `p01`.

Source output budget: **96 tokens**.

Source validator semantics:

- response must parse as one JSON object and contain no text outside it;
- `primary_coolant_temp_celsius` must equal 847;
- `crew_count` must equal 9;
- `avg_radiation_dose_mSv` must equal 4.7.

## P protocol

- L1: same full p01 prompt, seed 101, source budget 96.
- L2: same full p01 prompt, seed 202, source budget 96.
- L3: one third inference, seed 303, receives prompt + L1 + L2.
- L3 has a separate orchestration wrapper and a 256-token meta budget because it must emit RAW and INFORMED sections in one call.
- Only the contents of INFORMED are frozen and evaluated as the P candidate.

The 256-token L3 meta budget is **not** a claim that the source benchmark used 256 tokens; it is orchestration overhead required by the authorial P architecture. The frozen candidate itself remains subject to the exact p01 output contract.

## C protocol

- same full p01 prompt;
- seed 404;
- source budget 96;
- TALM v0.5.2 mass-right-soft specialization;
- no access to L1/L2/L3.

## Decision/outcome firewall

The macro decision is frozen before the exact validator is evaluated. The exact p01 validator is then applied to both frozen candidates. Only after that may a successor posterior be created.

No operational authority is transferred from a single case.
