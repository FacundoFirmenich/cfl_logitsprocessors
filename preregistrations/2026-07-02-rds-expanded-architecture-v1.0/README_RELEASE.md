# Public release instructions

Target repository: `https://github.com/FacundoFirmenich/cfl_logitsprocessors`. Continue the default `Ulalito's-Island` lineage; audited parent head is `174df3cde8d5358b0902db2815f6a09262f0b655`. If the remote advances, fetch and reconcile before staging.

1. Run `python verify_preregistration.py`; it must return `"valid": true`.
2. Add the release under `preregistrations/2026-07-02-rds-expanded-architecture-v1.0/`; do not replace historical files.
3. Verify that checkout or editor settings did not rewrite LF/NFC payload bytes.
4. Commit intentionally and create an annotated or signed tag, for example `rds-expanded-prereg-v1.0`.
5. Create a GitHub release from that exact tag using `GITHUB_RELEASE_NOTES_v1.0.md`.
6. Create a **new version** under Zenodo concept DOI `10.5281/zenodo.20665449`; do not create a disconnected concept record.
7. Upload the unchanged `RDS_EXPANDED_ARCHITECTURE_PREREGISTRATION_v1.0_ZENODO.zip`.
8. Verify public SHA-256 equals `a68a0222277c4ee4573fc688e1731014476cd7f30796071afcc5a3de151cef15`.
9. Record parent/new commit, tag, release URL, new Zenodo version DOI, concept DOI, public filename, bytes, SHA-256, and timestamps in a new immutable custody receipt. Never edit the frozen preregistration or manifest to backfill identifiers.

The root prehash commits to the ordered payload ledger. The deterministic ZIP hash commits to the upload archive. Neither hash is an empirical result.