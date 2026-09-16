# BatteryML protocol-generalization S2 — Kaggle preregistration candidate

Prepared: 2026-09-16 (Europe/Belgrade)  
Status: **FINAL CANDIDATE — RUN PROHIBITED pending Ivan/Operator ratification**

## Study class and prior knowledge

S2 is a **resource-adapted preregistered replication**, not a continuation of
S1 and not a fully blind confirmatory study.

S1 remains locked as `EXECUTION_BLOCKED_RESOURCE — model gate incomplete`.
Before this S2 freeze, the following S1 results were known:

- Variance A: RMSE `136.12962341308594`, MAE `109.06492614746094`;
- Variance B: RMSE `133.47593688964844`, MAE `109.73088836669922`;
- Ridge A: RMSE `115.7891820959575`, MAE `80.41317165427543`.

S1 values cannot be copied into, substituted for, or adjudicated as S2
results. S2 must execute its entire matrix from the beginning.

## Primary question

> Under the pinned BatteryML pipeline, how much does predictive performance
> change when MATR1 evaluation is changed from the BatteryML code split to the
> minimum-change exact-size protocol-disjoint split, holding the 83-cell
> universe fixed?

The experiment tests transfer from a protocol-overlap evaluation to held-out
charging protocols. It does not label the original split as “leakage” and does
not assert that BatteryML is invalid.

## Pinned source and inputs

- Upstream repository: `microsoft/BatteryML`.
- Commit: `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd`.
- Tracked-source manifest SHA-256:
  `5e239025955a160586a666b3cd50deb03c0e60e8ccf316fbb111156f197a516e`.
- MATR batch1 SHA-256:
  `9d928ab978f0e3c70b31cb833a749fedd35094d01af76475d69b40aa3497f5ba`.
- MATR batch2 SHA-256:
  `63ab200d09ecb237fee5ef3a5c5db76e3212e3206a0bd92f769e1427fed338b8`.
- Kaggle raw source: `rickandjoe/mit-battery-degradation-dataset`.
- Mounted raw filenames:
  `2017-05-12_batchdata_updated_struct_errorcorrect.mat` and
  `2017-06-30_batchdata_updated_struct_errorcorrect.mat`.
- Pre-ratification hash-only probe receipt SHA-256:
  `d2e33a03c4f8034449f42eb5e235f5ae0279a09fa9a41b15fe0a1dfa7c9fe66a`;
  both files matched the frozen byte sizes and SHA-256 values.
- Split-manifest SHA-256:
  `96695e534718733469ba108ee3c1372e29351710235d5b47020f6bd9ae2ce722`.
- Protocol identity is the exact normalized original `policy_readable` value,
  represented publicly by its SHA-256 group identifier.

The raw files are attached read-only from the identified public Kaggle dataset.
The private S2 control dataset may contain only the exact tracked BatteryML
source snapshot, the public S2 control files, and two offline dependency
wheels. It may not contain S1 predictions as executable inputs.

## Universes and assignments

### Primary

- BatteryML-code universe of 83 cells; `b2c1` is excluded from A and B.
- A: 41 train / 42 test using the pinned BatteryML primary assignment.
- B: 41 train / 42 test using the minimum-change, exact-size,
  protocol-disjoint assignment.
- B has zero protocol-group overlap between train and test.

### Sensitivity

- Original 84-cell universe including `b2c1`.
- A and B each contain 41 train / 43 test cells.
- B is the same deterministic minimum-change protocol-disjoint construction.
- Sensitivity is reported separately and cannot activate the primary gate.

The assignment file is
`batteryml-protocol-generalization-split-manifest.csv`. Split construction,
tie-breaking, membership order, and protocol hashes are unchanged from S1.

## Model matrix and fixed order

Exactly twelve runs execute in this order:

1. primary83: Variance A, Variance B, Ridge A, Ridge B, XGBoost A, XGBoost B;
2. sensitivity84: Variance A, Variance B, Ridge A, Ridge B, XGBoost A,
   XGBoost B.

Pinned BatteryML configurations:

| Model | Config | SHA-256 |
|---|---|---|
| Variance | `configs/baselines/sklearn/variance_model/matr_1.yaml` | `ab0849c3a021273629c1a6e90c09aa29eb425fdfb17aef2376888524f6984b5b` |
| Ridge | `configs/baselines/sklearn/ridge/matr_1.yaml` | `ad554e8c459a85278ce125a20c179dd3ed65046d5abeab455a3738d3ca793a54` |
| XGBoost | `configs/baselines/sklearn/xgb/matr_1.yaml` | `ce3e35629429b988426d0a0b9da867e7c4411a949715dad61597b5684483a0f7` |

Seed is `0` for every run. Hyperparameters, feature extraction, labels,
transformations, estimator construction, and metrics are not tuned or changed
after ratification. No neural model is part of S2.

## Kaggle-native environment

- Private Kaggle CPU kernel; internet disabled; GPU disabled.
- Python exactly `3.12.13`.
- Linux x86_64; at least `31 GiB` total RAM; at least 4 logical CPUs.
- No swap requirement.
- Kaggle base `pip freeze` SHA-256 exactly
  `e137b12924bbb4fbb83f45c8ccb3419ba4e5556d01d977a05a7ab4e175155c35`.
- Relevant versions and offline-wheel hashes are frozen in
  `environment-lock.txt`.
- CUDA must be unavailable.

The observed closure host provided 31.348 GiB RAM, Python 3.12.13, four CPUs,
and no swap. Any execution host that fails these exact/minimum checks stops
before raw preprocessing.

## Cache, isolation, and membership

- BatteryML dataset cache is disabled; no prior cache is admissible.
- Preprocessing starts in an absent output namespace and directly calls the
  pinned `load_batch` and `clean_batches` functions.
- The processed 89-file manifest is hashed and reused by all twelve runs.
- Every `(universe, split, model)` has a distinct absent-before-run namespace.
- Before dataset construction and again before fitting, ordered loaded cell IDs
  must byte-for-byte match the frozen assignment manifest.
- Any label filtering or membership change aborts execution.
- Each model run occurs in its own child process so memory is released between
  runs; this is operational isolation, not a scientific intervention.

## Metrics and receipts

Primary metric: test RMSE in cycle-life units.  
Secondary metric: test MAE in cycle-life units.

For each model `m`:

`relative_RMSE_change_m = (RMSE_B_m - RMSE_A_m) / RMSE_A_m`

Required evidence includes:

- literal stdout, stderr, command, exit code, and timestamps for preprocessing
  and each run;
- environment, raw, source, config, split, processed, and driver hashes;
- resolved estimator parameters;
- ordered loaded train/test IDs;
- one prediction row per test cell with target and protocol-group hash;
- unrounded aggregate RMSE and MAE;
- a final artifact-file SHA-256 manifest.

## Frozen gate triggers

The 83-cell primary gate is signal-positive if at least one condition holds:

1. at least one model has `relative_RMSE_change >= 10%`;
2. unrounded RMSE model ordering changes between A and B;
3. all three models have strictly higher unrounded RMSE under B than A.

Otherwise adjudication is `STOP_NO_MATERIAL_SIGNAL`. Sensitivity results do
not independently activate the primary gate. No neural phase starts
automatically under either outcome.

## Interpretation boundary

If signal-positive, the strongest initial statement allowed is:

> Performance under the published protocol-overlap MATR1 evaluation does not
> transfer unchanged to held-out charging protocols under the preregistered
> split and tested models.

S2 cannot by itself establish leakage, misconduct, universal failure on unseen
protocols, or invalidity of other BatteryML datasets.

## Ratification and prohibition

The driver requires a receipt containing all of:

- `status=RATIFIED`;
- `instance=batteryml-protocol-generalization-s2-kaggle`;
- this final preregistration SHA-256;
- the final S2 driver SHA-256;
- operator name and ratification timestamp.

Until that receipt exists, preprocessing, feature extraction, fitting,
prediction, and adjudication are prohibited. Environment/import-only probes
are not scientific runs and may occur before ratification.
