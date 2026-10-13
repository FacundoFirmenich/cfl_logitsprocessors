# CFL macro P/C gate v0.5 — specification audit

The first real macro P/C execution used the recovered CFL Decoder p08 prompt.

That run is **real execution evidence** but its semantic outcome is **quarantined** for macro-learning purposes.

Reason: the p08 prompt says that exactly one reasoning step contains a structural inference fallacy, while the chain as written permits more than one defensible structural criticism. The recovered validator hard-codes step 3 (affirming the consequent), yet the generated candidates selected later steps for reasons that are not obviously nonsensical from the literal chain. Therefore the p08 W/L labels are not sufficiently specification-clean to update macro P/C authority.

The historical v0.5 artifact remains immutable and auditable. Its successor posterior must not be promoted.

v0.5.1 moves to recovered CFL Decoder p06, a deterministic finite-state-machine trace with exhaustive transition rules and an exact 12-step validator. That benchmark has an unambiguous outcome under the source specification.
