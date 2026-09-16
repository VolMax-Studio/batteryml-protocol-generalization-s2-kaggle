# BatteryML protocol-generalization S2 — Kaggle preregistration candidate

Prepared: 2026-09-16 (Europe/Belgrade)  
Status: **FINAL CANDIDATE — RUN PROHIBITED pending Ivan/Operator ratification**

## Study class and prior knowledge

S2 is a **resource-adapted preregistered re-execution**, not a continuation of
S1 and not a fully blind confirmatory study.

S1 remains locked as `EXECUTION_BLOCKED_RESOURCE — model gate incomplete`.
Before this S2 freeze, the following S1 results were known from the partial S1 run:

- Primary83 Variance A: RMSE `136.12962341308594`, MAE `109.06492614746094` (`exposure: exposed`);
- Primary83 Variance B: RMSE `133.47593688964844`, MAE `109.73088836669922` (`exposure: exposed`);
- Primary83 Ridge A: RMSE `115.7891820959575`, MAE `80.41317165427543` (`exposure: exposed`).

In S1, Variance under B was strictly lower (better) than under A (relative change −1.9493%,
`RMSE_B < RMSE_A`).

The remaining model cells have not been exposed:
- Primary83 Ridge B: `exposure: unverified`;
- Primary83 XGBoost A: `exposure: unverified`;
- Primary83 XGBoost B: `exposure: unverified`;
- All Sensitivity84 combinations (Variance A/B, Ridge A/B, XGBoost A/B): `exposure: unverified`.

S1 values cannot be copied into, substituted for, or adjudicated as S2
results. S2 must execute its entire matrix from the beginning.

### Cross-environment divergence disposition

A cross-environment numerical tolerance of **1.0% relative** (`abs(S2 - S1) / S1 <= 0.010`)
is frozen for the three exposed S1 results (`primary83 Variance A`, `primary83 Variance B`,
and `primary83 Ridge A`).

If any of these three exposed metrics in S2 deviates from its frozen S1 reference value by
more than 1.0% relative, the disposition is:

`DEFERRED_ENVIRONMENT_DIVERGENCE`

Under `DEFERRED_ENVIRONMENT_DIVERGENCE`, S2 is not adjudicated for scientific gate triggers.
This threshold is established strictly below our 10% materiality boundary to prevent
confounding numerical or environmental shifts with scientific generalization signals.

## Primary question

> Under the pinned BatteryML pipeline, how much does predictive performance
> change when MATR1 evaluation is changed from the BatteryML code split to the
> minimum-change exact-size protocol-disjoint split, holding the 83-cell
> universe fixed?

The experiment tests transfer from a protocol-overlap evaluation to held-out
charging protocols. It does not label the original split as “leakage” and does
not assert that BatteryML is invalid.

## Pinned source, inputs, and L0 provenance

- Upstream repository: `microsoft/BatteryML`.
- Commit: `2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd`.
- Tracked-source manifest SHA-256:
  `5e239025955a160586a666b3cd50deb03c0e60e8ccf316fbb111156f197a516e`.
- MATR batch1 SHA-256:
  `9d928ab978f0e3c70b31cb833a749fedd35094d01af76475d69b40aa3497f5ba`.
- MATR batch2 SHA-256:
  `63ab200d09ecb237fee5ef3a5c5db76e3212e3206a0bd92f769e1427fed338b8`.
- Mounted raw filenames:
  `2017-05-12_batchdata_updated_struct_errorcorrect.mat` and
  `2017-06-30_batchdata_updated_struct_errorcorrect.mat`.
- Split-manifest SHA-256:
  `96695e534718733469ba108ee3c1372e29351710235d5b47020f6bd9ae2ce722`.
- Protocol identity is the exact normalized original `policy_readable` value,
  represented publicly by its SHA-256 group identifier.

### L0 raw dataset provenance and licensing

- Original data provider: Toyota Research Institute (TRI) — Experimental Data Platform (MATR).
- Portal URL: `https://data.matr.io/1/`.
- Project URL: `https://data.matr.io/1/projects/5c48dd2bc625d700019f3204`.
- EDP API configuration endpoint: `https://data.matr.io/1/api/v1/edp/configuration`.
- Verbatim license grant: `"license": {"label": "CC BY 4", "url": "https://creativecommons.org/licenses/by/4.0/"}`.
- Verbatim platform UI statement: `"All data is released under [CC BY 4](https://creativecommons.org/licenses/by/4.0/)"`.
- License standard: Creative Commons Attribution 4.0 International (CC BY 4.0).
- Scientific citation: Severson, K. A., Attia, P. M., Jin, N., et al., *Data-driven prediction of battery cycle life before capacity degradation*, Nature Energy 4, 383–391 (2019). DOI: 10.1038/s41560-019-0356-8.
- Non-reliance on third-party rehost: The third-party Kaggle rehost license tag ("MIT" on `rickandjoe/mit-battery-degradation-dataset`) is third-party metadata and is NOT relied upon as proof of original licensing. S2 establishes provenance exclusively from the original TRI/MATR provider grant.
- Operational disposition: To maintain fail-closed protocol integrity and avoid unnecessary redistribution, S2 does not upload a new raw HDF5 dataset. S2 attaches the existing Kaggle dataset `rickandjoe/mit-battery-degradation-dataset` read-only, where pre-ratification hash probing independently established bit-for-bit identity (`d2e33a03c4f8...`) with the verified MATR source files.
- L0 receipt: `l0-provenance-receipt.json`.

The private S2 control dataset may contain only the exact tracked BatteryML
source snapshot, the public S2 control files, and two offline dependency
wheels. It may not contain S1 predictions as executable inputs.

## Universes, assignments, and split multiplicity

### Multiplicity and tie-breaking

Dynamic programming and combinatorial enumeration confirm:
- In both universes, the minimum number of cell moves from A to achieve protocol-disjointness is exactly **20**.
- There exist **185,471** distinct minimal-cost protocol-disjoint assignments for `primary83`, and **190,476** for `sensitivity84`.
- Split B is **not** a unique "natural" partition; it is one specific assignment selected by the deterministic, self-contained lexicographic tie-break algorithm:
  1. Primary universe assignments are initialized from Split A (`MATRPrimaryTestTrainTestSplitter`).
  2. The objective function strictly minimizes cell transitions between train and test such that no normalized `policy_readable` protocol-group SHA-256 appears in both sets, while preserving exact partition sizes (41 train / 42 test for primary83; 41 train / 43 test for sensitivity84).
  3. Among all 185,471 (or 190,476) partitions achieving the optimal cost of 20 cell moves, the tie-break deterministically selects the lexicographically earliest assignment ordered by `(protocol_group_sha256, cell_id)`.
  4. This algorithm is self-contained and does not depend on S1 references.

### Primary universe (83 cells)

- BatteryML-code universe of 83 cells; `b2c1` is excluded from A and B.
- A: 41 train / 42 test using the pinned BatteryML primary assignment.
- B: 41 train / 42 test using the minimum-change, exact-size, protocol-disjoint assignment.
- B has zero protocol-group overlap between train and test.

### Sensitivity universe (84 cells)

- Original 84-cell universe including `b2c1`.
- A and B each contain 41 train / 43 test cells.
- B is the same deterministic minimum-change protocol-disjoint construction.
- Sensitivity is reported separately and cannot activate the primary gate.

The assignment file is `batteryml-protocol-generalization-split-manifest.csv` (SHA-256 `96695e534718...`).

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

## Kaggle-native environment and hardware admission

- Private Kaggle CPU kernel; internet disabled; GPU disabled.
- Python exactly `3.12.13`.
- Linux x86_64; at least `31 GiB` total RAM.
- **CPU admission**: Exactly **4 logical CPU cores** required (`logical_cpus == 4`). Hosts with core counts different from 4 fail admission closed. This requirement freezes XGBoost threading semantics without altering upstream BatteryML code.
- **Memory tracking**: Both `/proc/meminfo MemTotal` and cgroup memory limit (`memory.max` under cgroup v2, or `memory.limit_in_bytes` under cgroup v1) are recorded in the environment receipt.
- Kaggle base `pip freeze` SHA-256 exactly
  `e137b12924bbb4fbb83f45c8ccb3419ba4e5556d01d977a05a7ab4e175155c35` (872 lines).
- Offline wheels: `addict-2.4.0-py3-none-any.whl` (`249bb56b...`) and `fire-0.7.1-py3-none-any.whl` (`e43fd8a5...`).
- CUDA must be unavailable.
- Frozen XGBoost resolved execution parameters are documented in `environment-resource-receipt.json`.

## Pre-run determinism verification rule

To guarantee reproducibility prior to the scientific run, the execution driver implements
a frozen determinism verification protocol:
1. Executes a non-MATR synthetic fixture (4 synthetic cells with complete cycle data).
2. Generates canonical processed fixture data, per-cell predictions, and metrics across Variance, Ridge, and XGBoost with seed 0.
3. Moves canonical outputs, re-executes the exact pipeline from the beginning, and asserts byte-identical recreation (`rename -> rerun -> byte-identical match`).
4. Timestamps and host metadata are excluded from canonical byte comparison.
5. Receipt `determinism-receipt.json` records `byte_identical_match: true` across all models.

## Execution attempt policy and ledger

Execution is governed by a strict attempt policy frozen in `attempt-policy-receipt.json`:
- **Maximum 2 scientific attempts** are permitted.
- Attempt 001 executes the full 12-run matrix from an empty workspace.
- Attempt 002 is permitted **ONLY IF** Attempt 001 failed to complete all twelve runs due to an unexpected platform/resource failure (e.g. host OOM, platform timeout, or session disconnection).
- Attempt 002 must be a **full restart** of all twelve runs from the beginning with identical governing hashes and environment.
- Partial results from different attempts are **never combined or spliced**.
- The first complete attempt is governing.
- If Attempt 002 also fails to complete all twelve runs, the terminal disposition is **`EXECUTION_BLOCKED_RESOURCE`**.
- An immutable attempt ledger (`attempt-ledger.json`) records for each attempt:
  - Kaggle kernel version / URL;
  - Attempt number (1 or 2);
  - Start and end UTC timestamps;
  - Governing preregistration SHA-256 and driver SHA-256;
  - Exit code and disposition;
  - Generated receipts, including partial/failed execution logs.

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

## Frozen gate triggers and exposure classification

Subject to passing the 1.0% cross-environment divergence check on exposed S1 metrics,
the 83-cell primary gate is signal-positive if at least one condition holds:

1. **Trigger 1**: At least one model has `relative_RMSE_change >= 10%`.
   - *Exposure classification*: Partially exposed / decision weight on unverified models.
   - *Status*: S1 Variance change was −1.95% (well below 10%). Variance cannot activate Trigger 1 unless environmental divergence occurs. Decision weight rests entirely on unverified Ridge B and XGBoost A/B.
2. **Trigger 2**: Unrounded RMSE model ordering changes between A and B.
   - *Exposure classification*: Partially exposed / decision weight on unverified models.
   - *Status*: Relative ordering cannot be evaluated without unverified Ridge B and XGBoost A/B.
3. **Trigger 3**: All three models have strictly higher unrounded RMSE under B than A.
   - *Exposure classification*: Pre-exposed / no independent confirmatory weight.
   - *Status*: In S1, Variance B is strictly lower than Variance A (133.48 < 136.13). If S2 reproduces Variance within the 1.0% cross-environment tolerance, Trigger 3 is guaranteed to be false a priori. It remains implemented in code for exhaustive protocol fidelity, but carries no independent confirmatory weight.

If no trigger fires, adjudication is `STOP_NO_MATERIAL_SIGNAL`. Sensitivity results do
not independently activate the primary gate. No neural phase starts
automatically under either outcome.

## Interpretation boundary

If signal-positive, the strongest initial statement allowed is:

> Performance under the published protocol-overlap MATR1 evaluation does not
> transfer unchanged to held-out charging protocols under the preregistered
> minimum-change split and tested models.

Because there exist ~185,000 equivalent minimal-cost protocol-disjoint partitions,
we measure the effect of one preregistered minimum-change protocol-disjoint split,
not a unique "natural" disjoint partition. Interpretation is strictly bounded
under the preregistered split. S2 cannot by itself establish leakage, misconduct,
universal failure on unseen protocols, or invalidity of other BatteryML datasets.

## Ratification requirements

The driver requires a receipt containing all of:

- `status=RATIFIED`;
- `instance=batteryml-protocol-generalization-s2-kaggle`;
- this final preregistration SHA-256;
- the final S2 driver SHA-256;
- operator name and ratification timestamp;
- `operator_verbatim_statement` (verbatim text of operator ratification);
- `operator_statement_location` (identifier of the message or session where uttered).

Until that receipt exists, preprocessing, feature extraction, fitting,
prediction, and adjudication are prohibited. Environment, determinism, and import-only probes
are not scientific runs and may occur before ratification. Direct-to-main push is
acceptable for this instance; merge-click is not required. Operator ratification
remains an independent step following Claude PASS.
