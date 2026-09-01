---
license: apache-2.0
library_name: sklearn
tags:
  - sklearn
  - joblib
  - surrogate
  - recipe-conformance
  - szl-holdings
  - doctrine-v11
---

# szl-nemo — SOFTWARE/SURROGATE (NOT Nemotron, NOT an LLM, NOT a Kernel Hub CUDA kernel)

Canonical GitHub source: [`szl-holdings/szl-nemo`](https://github.com/szl-holdings/szl-nemo).
Hub ID `SZLHOLDINGS/szl-nemo` is a **sklearn recipe-conformance surrogate card**.
It is **not** NVIDIA Nemotron. It is **not** a generative model. It is **not**
a Triton/CUDA kernel. Tags `nemotron` and `ollama` were misleading and are **stripped**.
Do not `from_pretrained` this as an LLM. SZL has **not** fine-tuned Nemotron and does **not** republish NVIDIA weights.

Approved GitHub path: `szl_nemo.rule_check` + `szl_nemo.evaluate` (stdlib, R1–R5). `model.joblib` is quarantined.

## What it is / is NOT

- **IS:** a deterministic doctrine kernel. `szl_nemo.rules.rule_check` (R1–R5)
  is ground truth; `szl_nemo.engine.evaluate` wraps it in a typed, hashed
  decision contract; `szl_nemo.cli` exposes it as `szl-nemo` /
  `python -m szl_nemo`. `quarantine/forge_surrogate.py` (historical
  `scripts/forge.py`) + `scripts/eval.py` + `TRAINING_RECEIPT.json` describe a
  quarantined `Pipeline(TfidfVectorizer → LogisticRegression)` triage
  surrogate. Optional `Modelfile` is prompt text only.
- **NOT:** NVIDIA Nemotron 3 Nano 4B. Not ollama-ready Nemotron weights. Not a
  chatbot. Not a fine-tune. `BASE_MODEL_MANIFEST.json` is an observation of an
  upstream Ollama tag (mutable); it is **not** weights in this repo.

## Decision contract

```json
{
  "schema_version": "szl.nemo.decision.v1",
  "decision": "ALLOW | BLOCK | REVIEW",
  "violated_rules": ["R1_no_fabrication_label"],
  "reasons": ["human-readable reason per violated rule"],
  "rule_version": "doctrine-v11/R1-R5",
  "input_hash": "sha256:<canonical {prompt, answer} JSON>",
  "receipt_status": "UNSIGNED_HONEST"
}
```

`REVIEW` is exactly one case: an empty/blank prompt or answer carries no
doctrine signal, and the kernel refuses to silently allow it. Every input
with real content gets the binary `rule_check` verdict — there is no
fuzzy middle tier, because that would claim a capability the checker does
not have. `receipt_status` is always `UNSIGNED_HONEST` — this repository
holds no signing key, and an unsigned receipt must say so. Signing belongs
to the Evidence Plane (`szl-guardrail-receipt`), not to the kernel.

## Receipts

`szl_nemo.receipt` binds decisions into a hash-chained receipt ledger
(`szl.nemo.receipt.v1`): every receipt carries its own `receipt_sha256`,
a `sequence`, and `prev_receipt_sha256` (genesis = 64 zeroes). Deterministic
— no clocks, no RNG — so the same decision sequence always yields the same
bytes. `verify_receipt()` / `verify_chain()` recompute and check without
ever raising; `szl-nemo receipt-verify file.json` does it from the shell.
Integrity and ordering are checkable by anyone; identity is not claimed
(unsigned, honestly).

## Usage

```bash
pip install -e .            # stdlib-only; no dependencies

szl-nemo check \
  --prompt "What's your MMLU?" \
  --answer "UNKNOWN - no benchmarks have been run."
# {"decision":"ALLOW",...}                              exit 0

szl-nemo check --prompt "What's your MMLU?" --answer "My MMLU is 73."
# {"decision":"BLOCK","violated_rules":["R1_no_fabrication_label",...]}  exit 1

szl-nemo check --jsonl pairs.jsonl --out decisions.jsonl   # batch mode
szl-nemo selftest                                          # labelled vectors
szl-nemo receipt-verify chain.json                         # receipt ledger
szl-nemo version
```

Exit codes: `0` ALLOW, `1` BLOCK, `2` usage/IO error, `3` REVIEW (BLOCK
dominates in batch mode).

Library use:

```python
from szl_nemo import evaluate

decision = evaluate(prompt, answer)   # typed Decision, deterministic
assert decision.input_hash.startswith("sha256:")
```

## Status

| Thing | Label | Method / N / date / what-NOT |
|---|---|---|
| Doctrine kernel (`rule_check` R1–R5 + engine + CLI + receipts) | **MEASURED — operational** | `pytest` suite + 20 labelled vectors + `szl-nemo selftest` + hash-chained receipt verification, CI on every push/PR. doctrine-v11.1 fixes two word-boundary bugs (R3 gate never fired on "fine-tune"; R5 never fired on "100%"); regression vectors `deny-003`/`deny-006` pin both. What-NOT: regex ground truth is deliberately conservative — it can false-BLOCK negated phrasing (see `test_vectors/README.md`); receipts prove integrity and ordering, not identity (unsigned). |
| `model.joblib` on Hub | **UNAVAILABLE** | Hub file list 2026-08-28 ~6:56pm ET. Files on main: `.gitattributes`, `BASE_MODEL_MANIFEST.json`, `LICENSE`, `Modelfile`, `README.md`, `SZL_ESTATE_MANAGED.json`, `TRAINING_RECEIPT.json`, `scripts/eval.py`, `scripts/forge.py`. **No `model.joblib`.** Receipt names file `model.joblib` sha256 `d3f0cd7bebbb73fedbc9a0f098148f46f5834bf9184b43cd29b07f286a77ff5b` — that blob is **not published here**. Do not invent it. |
| Receipt-bound scorer metrics | **REPORTED in `TRAINING_RECEIPT.json`** | `trained_at_utc` 2026-07-21T02:52:42Z, host replit 2-vCPU, sklearn 1.9.0, seed 20260721. N=5620 checker-labelled rows (2638 conform / 2982 violation), 80/20 stratified. `fidelity_vs_rule_checker` **1.0**; unseen paraphrases **0.8333** (N=**12**). Generator script now quarantined at `quarantine/forge_surrogate.py`. What-NOT: not LLM quality; not a Nemotron benchmark; **cannot be replayed from Hub bytes until `model.joblib` is present**. |
| Nemotron / generative evals | **UNAVAILABLE** | None on this card. Quality of any Nemotron run on SZL hardware: **UNAVAILABLE**. |
| NVIDIA weights | **NOT REPUBLISHED** | Never copy upstream tensors into this ID. |

When `model.joblib` is actually committed, load with `joblib.load("model.joblib")` and sha256-check against the receipt. Until then, this ID is scripts + a receipt, not a loadable sklearn artifact.

Apache-2.0 for SZL files here. Upstream Nemotron, if you fetch it yourself, stays under NVIDIA's license. Λ = Conjecture 1.
