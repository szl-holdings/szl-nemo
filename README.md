---
license: apache-2.0
tags:
  - governance
  - inference-witness
  - deterministic
  - evidence-grounding
  - receipts
  - recipe-conformance
  - szl-holdings
  - doctrine-v11
---

# szl-nemo — deterministic witness, not Nemotron

Canonical GitHub source: [`szl-holdings/szl-nemo`](https://github.com/szl-holdings/szl-nemo).

`SZL Nemo` is **software**: a deterministic doctrine checker and structured
inference-envelope witness. It is **not** NVIDIA Nemotron, an LLM, a generative
model, an Ollama model, or a Triton/CUDA kernel. SZL has not fine-tuned Nemotron
and does not republish NVIDIA weights.

Approved package paths:

- `szl_nemo.rule_check` / `szl_nemo.evaluate`: prompt-and-answer doctrine checks
  R1–R5.
- `szl_nemo.envelope_check` / `szl_nemo.evaluate_envelope`: proof-carrying
  inference-envelope checks E1–E10.

`model.joblib` and its historical scorer generator remain quarantined. They are
not an approved runtime or publication path.

## Canonical role inside SZL Forge

Forge owns model lifecycle, evaluation, qualification, and publication. Nemo is
an independent witness around a replaceable inference engine:

```text
Second Brain handles
  -> controller-side tenant authorization + content-digest verification
  -> Nemo PRE_GENERATION witness
  -> proposal-only model
  -> Nemo POST_GENERATION witness
  -> A11oy PRE_TOOL admission + human approval + signed receipt
  -> execution outside the model
  -> Nemo POST_TOOL/postcondition witness
  -> sanitized Living Anatomy observation
```

Nemo may return `ALLOW`, `BLOCK`, or `REVIEW`. `ALLOW` means only that the
checks for the inspected stage passed. It never grants tool authority by itself.
Living Anatomy is an observer, not a decision authority.

## R1–R5 prompt/answer contract

The original deterministic API remains stable:

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

For this API, `REVIEW` is the empty-input case: no doctrine signal exists, so the
kernel refuses to silently allow it. Every non-empty pair receives a binary
R1–R5 result.

## E1–E10 proof-carrying envelope

Version `0.4.0` adds a structured, stdlib-only witness over inference metadata and
digests. It does not store raw prompts, hydrated content, private graph state, or
private chain-of-thought.

| Rule | Enforced boundary |
|---|---|
| E1 | Envelope schema and Nemo identity: `SOFTWARE_KERNEL`, non-generative, not Nemotron |
| E2 | Pinned model, adapter, tokenizer, template, runtime, and hardware identity |
| E3 | Principal/tenant authorization plus Second Brain handle/source/content-digest binding |
| E4 | Exact locked-eight formula set, pinned formal/kernel sources, applicability evidence, no invented F-ID-to-callable mapping, Lambda advisory only |
| E5 | Model remains `PROPOSAL_ONLY`; A11oy is the only execution authority |
| E6 | Raw content, private graph data, and private reasoning are forbidden |
| E7 | Tool intent requires A11oy admission, human approval, and a verified signed receipt |
| E8 | PRE/POST generation and PRE/POST tool witness stages are ordered exactly |
| E9 | Executed tool results and postconditions are digest-bound |
| E10 | Persisted claims use only `MEASURED`, `REPORTED`, `MODELED`, `CONJECTURE`, `UNKNOWN`, or `UNAVAILABLE` and carry statement digests |

The formal locked-proven formula set is exactly:

```text
F1, F4, F7, F11, F12, F18, F19, F22
```

The separate `szl-formulas` software kernel exposes 21 callable functions. Nemo
does **not** fabricate a mapping between those callable names and the formal
F-number corpus; the mapping remains `UNKNOWN_NOT_ASSERTED` until a proved
binding artifact exists. F23/Lambda remains `CONJECTURE_1_ADVISORY` and cannot be
an authorization basis.

A valid `PRE_TOOL` envelope with pending human approval returns `REVIEW`. A valid
`POST_TOOL` envelope with a failed bound postcondition also returns `REVIEW`.
Structural, provenance, privacy, or authority drift returns `BLOCK`.

## Receipts

`szl_nemo.receipt` binds decisions into a deterministic hash-chained ledger
(`szl.nemo.receipt.v1`). Every receipt carries `sequence`,
`prev_receipt_sha256`, and its own `receipt_sha256`; genesis is 64 zeroes.
`verify_receipt()` and `verify_chain()` recompute integrity without raising.

These receipts prove content integrity and ordering, not signer identity. This
repository holds no signing key, so receipt status remains honestly unsigned.
A11oy/Evidence Plane signing must occur before a consequential action.

## Usage

```bash
pip install -e .

szl-nemo check \
  --prompt "What's your MMLU?" \
  --answer "UNKNOWN - no benchmarks have been run."
# ALLOW, exit 0

szl-nemo check --prompt "What's your MMLU?" --answer "My MMLU is 73."
# BLOCK, exit 1

szl-nemo envelope-check inference-envelope.json
# ALLOW=0, BLOCK=1, malformed input=2, REVIEW=3

szl-nemo selftest
szl-nemo receipt-verify chain.json
szl-nemo version
```

Library use:

```python
from szl_nemo import evaluate, evaluate_envelope

text_decision = evaluate(prompt, answer)
envelope_decision = evaluate_envelope(envelope)
assert text_decision.input_hash.startswith("sha256:")
assert envelope_decision.input_hash.startswith("sha256:")
```

## Status

| Surface | Label | Evidence and limitations |
|---|---|---|
| R1–R5 doctrine checker, typed decisions, CLI, and receipts | **MEASURED — operational** | CI, labelled vectors, deterministic decision tests, installed-wheel self-test, and receipt-chain verification. Regex ground truth is deliberately conservative and may false-block negated phrasing. |
| E1–E10 structured inference-envelope witness | **MEASURED — operational contract** | Adversarial tests cover formula-set drift, invented formula mappings, formula applicability, tenant denial, evidence tampering, mutable revisions, Nemo/Nemotron confusion, private-state leakage, model self-execution, unsigned tool calls, stage order, postconditions, and truth-label drift. This validates envelopes; it does not prove a model is high quality or that a live deployment executed. |
| Historical TF-IDF/logistic-regression triage scorer | **QUARANTINED / not an approved path** | `TRAINING_RECEIPT.json` reports N=5,620 checker-labelled rows and a 12-example paraphrase set. `model.joblib` is absent from the approved package path, so the historical scorer is not loadable or replayable from published bytes. |
| Nemotron or generative-model evaluation | **UNAVAILABLE** | No Nemotron weights or qualified Nemotron benchmark are published here. |
| NVIDIA weights | **NOT REPUBLISHED** | Upstream weights, when independently fetched, remain governed by their upstream license. |

Apache-2.0 applies to SZL-authored files in this repository. Lambda uniqueness
remains Conjecture 1; never describe it as proven.
