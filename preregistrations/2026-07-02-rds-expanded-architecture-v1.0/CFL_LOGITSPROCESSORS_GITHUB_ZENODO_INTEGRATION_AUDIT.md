# cfl_logitsprocessors GitHub/Zenodo Integration Audit

## Verified repository identity

- Repository: `https://github.com/FacundoFirmenich/cfl_logitsprocessors`.
- Default branch: `Ulalito's-Island`.
- Current default-branch head: `174df3cde8d5358b0902db2815f6a09262f0b655` (2026-06-12T17:19:30+02:00), message `LAST UPLOADING FILES PRE RUNS`.
- Prior tagged commit: `8e281ef7534dc84ac63a95c4d15756a8d8d7aae0` (2026-06-12T13:03:21+02:00), message `Importante HASH pre executions upgrade`.
- Tags `0.64`, `0.64.0.8`, `0.64.0.8.11`, and `0.64.14` all resolve to that same prior commit.
- `main` currently ends at `8ea22528e6da5b66b2ef9d6bdf8efe93f525106a` and contains only `README.md` and `pre_execution_hashes.md`; it is not the repository's default historical preregistration branch.

## Verified Zenodo lineage

- Concept DOI: `10.5281/zenodo.20665449`.
- First published version DOI: `10.5281/zenodo.20665450`.
- Published version: `0.64.14`, date 2026-06-12.
- Related GitHub tree: `https://github.com/FacundoFirmenich/cfl_logitsprocessors/tree/0.64.14`.
- Zenodo archive MD5: `29ad03e450efd8cff967484ca77b6f5d` (matches the API record).
- Zenodo archive SHA-256: `d674b8bf7705dfaec027c77239af1d2e2553362075d3e5ade6822a637f0b55c6`.
- The archived snapshot resolves to commit `8e281ef...` and contains seven ZIP entries: the root directory plus two PDFs, README, `full_hash_per_ejecucion.txt`, `pre_execution_hashes.md`, and `pre_registro.txt`.

## Critical custody boundary

The following later artifacts exist at default-branch commit `174df3c...` but are absent from Zenodo version `0.64.14`:

- `PREREG_NATIVE_MULTILINGUAL_PROTOCOL_AND_SUBMERGED_MAP_V1 (1).zip`;
- `PREREG_TALM_TALON_NATIVE_MULTILINGUAL_MATRIX_V1_1_LINGUISTIC_PREEXEC.md`;
- `SUBMERGED_PROPERTY_MAP_NATIVE_MULTILINGUAL_TALM_TALON_V1.md`;
- their checksum companions.

Therefore:

1. Git commit `174df3c...` establishes repository chronology for those later artifacts.
2. Zenodo DOI `20665450` must not be cited as if its archived bytes already contained them.
3. The new RDS expanded preregistration should be deposited as a new Zenodo version under concept DOI `20665449`.
4. The new version DOI will establish Zenodo custody for the exact new release bytes.

## Historical design continuity

The original repository already fixes the methodological lineage now being extended:

- pre-execution hashing and immutable custody;
- local edge rather than global dominance;
- prompt/model/method hash preservation;
- TALM as more concentrated and TALON as more distributed prospective topology;
- tokenizer, language, template, quantization, and runtime dependence;
- explicit separation of design-derived expectations from results;
- Z_xpl as post-hoc local analysis rather than human-quality oracle;
- negative and local outcomes retained rather than averaged away.

The 2026-07-02 preregistration is consequently an architectural expansion of the same research programme, not a disconnected repository use.

## Commit integration contract

The new commit must:

1. descend from `174df3cde8d5358b0902db2815f6a09262f0b655` unless the remote advances and is reconciled explicitly;
2. preserve all historical commits, tags, filenames, and bytes;
3. add the new release under a new directory rather than replacing historical preregistrations;
4. include the exact deterministic ZIP with SHA-256 `a68a0222277c4ee4573fc688e1731014476cd7f30796071afcc5a3de151cef15`;
5. include the root payload prehash `d3aefcfe68528dd7d918675ded7b3c579fc96f586c89d3020958092e2c3d0510`;
6. preserve UTF-8 NFC and LF bytes; checkout-induced CRLF hashes are not custody hashes;
7. add release notes linking the old and new versions without claiming that v0.64.14 contained later files;
8. create a new immutable custody receipt after GitHub release and Zenodo publication.

## Recommended repository-relative destination

`preregistrations/2026-07-02-rds-expanded-architecture-v1.0/`

The directory should contain the preregistration Markdown, prediction ledger, claim traceability, frozen snapshot, manifest, checksum list, prehash, verifier, release instructions, deterministic Zenodo ZIP, and ZIP checksum.

## Required post-publication receipt

Record without editing the frozen preregistration:

- parent commit and new commit SHA;
- annotated/signed tag;
- GitHub release URL and timestamp;
- Zenodo concept DOI `10.5281/zenodo.20665449`;
- new Zenodo version DOI;
- public filename, size, and SHA-256;
- verification result against the local deterministic ZIP.