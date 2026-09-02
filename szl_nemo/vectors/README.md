# Test vectors (shipped as package data)

Labelled prompt/answer pairs that pin the doctrine checker's behavior.
They live inside the package (`szl_nemo/vectors/`) so `szl-nemo selftest`
works identically from a source checkout and from an installed wheel —
a lesson measured in CI when the source-tree-relative path broke in
installed mode.

- `allow.jsonl` — answers that conform to doctrine (R1–R5). All must ALLOW.
- `deny.jsonl` — answers that violate doctrine. All must BLOCK with the exact
  listed rule ids.

## Provenance (honest)

Expectations are **computed by `rule_check` itself** via
`scripts/build_vectors.py`, which refuses to write a vector whose
hand-assigned bucket (`allow` vs `deny`) disagrees with the checker. These
vectors pin current ground-truth behavior; they are not an independent
oracle. When the doctrine rules change intentionally, regenerate with:

```bash
python scripts/build_vectors.py
```

and review the diff the same way you would review a rule change.

## Known conservative edges (fail-closed, deliberate)

- "Λ is **not** a theorem" still trips R4: the checker is regex-based and
  does not parse negation. Doctrine prefers a false BLOCK over a false
  ALLOW on the honesty boundary. Rephrase: "Λ is Conjecture 1 — open."
- R3 fires on any prompt mentioning fine-tuning unless the answer carries
  an explicit not-fine-tuned disclosure ("not fine-tuned", "wrapper",
  "system-prompt", ...). Silence about provenance is a violation.

## Regression anchors

- `deny-003` — R3 gate must fire on the phrase "fine-tune" (word-boundary
  bug fixed in doctrine-v11.1).
- `deny-006` — R5 must fire on "100%" (word-boundary bug fixed in
  doctrine-v11.1).
