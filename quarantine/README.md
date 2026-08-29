# Quarantine

`forge_surrogate.py` historically dumped `model.joblib` (sklearn
`TfidfVectorizer → LogisticRegression`). That file is **not** an approved
load path. GitHub CI refuses `joblib.load` / `pickle.load` under
`scripts/`, `tests/`, and `szl_nemo/`.

The Hub ID `SZLHOLDINGS/szl-nemo` currently has **no** `model.joblib`.
Do not invent one. Ground truth is `szl_nemo.rule_check`.
