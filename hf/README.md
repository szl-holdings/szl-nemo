# Hugging Face import: `SZLHOLDINGS/szl-nemo`

This repository is the planned source of the model repo `SZLHOLDINGS/szl-nemo`
(plan P7: one mirror, model target only). Today no workflow here writes it.

| Path | What it is |
| --- | --- |
| `hub-import/model.README.md` | The Hub card exactly as the Hub served it. |
| `hub-import/IMPORT.json` | The imported revision, the card digests, the full Hub file list, and how each Hub file compares with this repository. |

`scripts/hf_hub_import.py fetch` writes both from the anonymous public Hub API
(read-only, no token). `tests/test_hf_hub_import.py` checks offline that the
committed bytes still match their recorded digests.

## Who writes the Hub repo today

- **Card.** `README.md` and `card/holo-banner.svg` are written by
  `szl-holdings/szl-forge` `publish-kernel-mirror-cards.yml` from
  `szl-forge:nemo/card/`. The imported card has the same git blob id as
  `szl-forge:nemo/card/README.md`, so its text is already held on GitHub. The
  plan retires that cross-writer only after this repository's mirror is green,
  so no second card source is staged here: one asset, one card source.
- **Code.** `szl_nemo/rules.py` on the Hub is uploaded by
  `szl-holdings/a11oy` `atelier-hub-publish.yml` (a cross-writer the plan
  retires); it differs from this repository's `szl_nemo/rules.py`.
- **Hub-only files.** `BENCH.laptop-blackwell.json`, `OPERATIONAL.json`,
  `PROMOTION_READINESS_AUDIT.json`, `ollama_probe.laptop.json`,
  `bom/model-bom.cdx.json` and `scripts/forge.py` exist only on the Hub (this
  repository keeps a different, quarantined `quarantine/forge_surrogate.py`).
  A future mirror must keep them or retire them explicitly, never by deletion
  sync.

## Publish status: blocked on owner actions

Moving the writer here needs:

1. **An HF credential for this repository.** Preferred: a Trusted Publisher
   for `SZLHOLDINGS/szl-nemo` bound to this repository's mirror workflow on
   `main`. Fallback: a repository secret `HF_TOKEN` scoped to that repo. This
   repository has no HF secret today. (Owner action.)
2. **The shared mirror.** `reusable-hf-mirror.yml` is not merged in
   `szl-holdings/.github`; workflow changes there wait for the owner's
   trust-root review.

Then: move `szl-forge:nemo/card/` here as the card source, add a thin caller
of the shared mirror, and retire the `szl-forge` and `a11oy` cross-writers for
this asset.
