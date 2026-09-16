# BatteryML protocol-generalization S2.1 — Kaggle preregistration candidate (Execution Repair)

Prepared: 2026-09-16 (Europe/Belgrade)  
Status: **FINAL CANDIDATE — RUN PROHIBITED pending Ivan/Operator ratification**

## Study class and prior knowledge

S2.1 is an **execution-repair instance** of S2, not a continuation of
S1 and not a fully blind confirmatory study. S2 was terminated following a pre-scientific
environment admission mismatch in child processes; S2.1 implements the exact governing
scientific design with an isolated pip freeze and verified module provenance.

S1 remains locked as `EXECUTION_BLOCKED_RESOURCE — model gate incomplete`.
Before this S2 freeze, the following S1 results were known from the partial S1 run:

- Primary83 Variance A: RMSE `136.12962341308594`, MAE `109.06492614746094` (`exposure: exposed`);
- Primary83 Variance B: RMSE `133.47593688964844`, MAE `109.73088836669922` (`exposure: exposed`);
- Primary83 Ridge A: RMSE `115.7891820959575`, MAE `80.41317165427543` (`exposure: exposed`).

In S1, Variance under B was strictly lower (better) than under A (relative change −1.9493%,
`RMSE_B < RMSE_A`).

Exposure status for the remaining model cells is unverified.
- Primary83 Ridge B: `exposure: unverified`;
- Primary83 XGBoost A: `exposure: unverified`;
- Primary83 XGBoost B: `exposure: unverified`;
- All Sensitivity84 combinations (Variance A/B, Ridge A/B, XGBoost A/B): `exposure: unverified`.

S1 values cannot be copied into, substituted for, or adjudicated as S2.1
results. S2.1 must execute its entire matrix from the beginning.

### S2 Attempt 001 execution failure and exposure status

S2 Attempt 001 on Kaggle CPU host (`volmax1/batteryml-s2-attempt-001`) deterministically aborted
during preflight environment admission inside child process `00-preprocess` prior to directory
creation (`PROCESSED.mkdir`) or loading of any MATR raw batch data (`load_batch`). The failure occurred
because `run_child` passed `PYTHONPATH=/kaggle/working/s2-site-packages`, causing child `pip freeze`
to enumerate offline wheels (`addict`, `fire`) as 874 lines instead of 872 base packages.
The Operator formally ratified the classification of Attempt 001 as `PRE-SCIENTIFIC_EXECUTION_FAILURE`.
Raw files were hashed in binary read mode during preflight input verification (`verify_inputs()`), but never
loaded into the BatteryML preprocessing pipeline (`load_batch` was never called). No additional scientific
exposure occurred from S2 Attempt 001 beyond the previously known S1 exposed metrics. S2 is formally closed,
and S2.1 executes the governing scientific design under the repaired driver.

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
- Split B is **not** a unique "natural" partition; it is the assignment reproduced by the original metadata-gate construction:
  1. For each universe independently, use its frozen Split A membership and positions (41 train / 42 test for primary83; 41 train / 43 test for sensitivity84).
  2. Define protocol identity as `unicodedata.normalize("NFKC", policy_readable).strip()`. Group cells by that exact string; sort the distinct normalized strings lexicographically using Python string order. SHA-256 identifies a protocol but does not determine group order.
  3. Assign each whole group to train (`0`) or test (`1`), preserving the exact A train/test counts. Minimize the number of cells whose side changes relative to A.
  4. Among equal minimum-cost assignments, choose the lexicographically smallest group-assignment bit vector in the string order from step 2, with `0 < 1`. Dynamic programming retains the minimum `(move_cost, bit_vector)` for each reachable test-cell count after each group. Assigning a group to train costs its A-test count; assigning it to test costs its A-train count and adds its full size to the test count. Initialize test count zero with `(0, ())`; select the exact target test count after the last group.
  5. Sort B train and B test cell IDs independently using Python string order; assign zero-based positions. Serialize rows in universe order `primary83`, `sensitivity84`, then lexicographic cell-ID order, using the frozen CSV column order, UTF-8, comma delimiters and CRLF line endings (including the final line). A positions are preserved.

The read-only `tie_break_verifier.py` includes the normalized protocol identities,
checks their SHA-256 identifiers against the frozen manifest, and regenerates B
using only A membership and protocol identity before comparing with frozen B.
Its optimization functions are copied from the original metadata-gate generator
`extract_matr_primary_metadata.py`, SHA-256
`d8d2fa56596e608cc8eb45b0d631c84d7568917d61ef1aa571e0f46b9de70efd`.
The verifier is self-contained and requires no S1 runtime or scientific execution.
Run `python3 tie_break_verifier.py` to emit the receipt; `tie-break-receipt.json`
records exact ordered-cell matches for both universes and byte-identical
regeneration of the complete frozen manifest.

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
- Linux x86_64; at least `31 GiB` total RAM (`mem_total_bytes >= 31 GiB`). Hardware admission evaluates `/proc/meminfo MemTotal` (observed: 31.35 GiB / 33,659,383,808 bytes). The container cgroup memory limit (`memory.max`) in Kaggle CPU containers is tracked (observed: 30.00 GiB / 32,212,254,720 bytes).
- **CPU admission**: Exactly **4 logical CPU cores** required (`logical_cpus == 4`). Hosts with core counts different from 4 fail admission closed. This requirement freezes XGBoost threading semantics without altering upstream BatteryML code.
- **Memory tracking**: Both `/proc/meminfo MemTotal` and cgroup memory limit (`memory.max` under cgroup v2, or `memory.limit_in_bytes` under cgroup v1) are recorded in the environment receipt.
- Kaggle base `pip freeze` SHA-256 exactly
  `e137b12924bbb4fbb83f45c8ccb3419ba4e5556d01d977a05a7ab4e175155c35` (872 lines). In both parent and child processes, `pip freeze` is executed with `PYTHONPATH` stripped to guarantee that the base platform package image is verified without pollution from working directories.
- Offline wheels: `addict-2.4.0-py3-none-any.whl` (`249bb56b...`) and `fire-0.7.1-py3-none-any.whl` (`e43fd8a5...`). Provenance is verified by asserting that imported module file paths reside strictly within the dedicated `s2-site-packages` directory.
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
- Any unhandled failure in Attempt 001 records initial disposition `FAILED_PENDING_OPERATOR_CLASSIFICATION`; it never automatically transitions to `FAILED_PLATFORM_RETRY_ALLOWED`.
- Attempt 002 is permitted **ONLY IF** Attempt 001 failed to complete all twelve runs and the Operator formally classifies the failure under [L3] as an unexpected platform/resource failure (e.g. host OOM, platform timeout, or session disconnection). Any deterministic code or pre-scientific failure remains non-retryable without a new execution-repair instance.
- Attempt 002 must be a **full restart** of all twelve runs from the beginning with identical governing hashes and environment.
- Partial results from different attempts are **never combined or spliced**.
- The first complete attempt is governing.
- If Attempt 002 also fails to complete all twelve runs, the terminal disposition is **`EXECUTION_BLOCKED_RESOURCE`**.
- An immutable attempt ledger (`attempt-ledger.json`) records for each attempt:
  - the configured Kaggle kernel slug and URL, with the version explicitly marked
    `POST_RUN_API_BINDING_PENDING` during execution;
  - Attempt number (1 or 2);
  - Start and end UTC timestamps;
  - Governing preregistration SHA-256 and driver SHA-256;
  - Exit code and disposition;
  - Generated receipts, including partial/failed execution logs.

Runner-only preflight failure before the scientific driver process starts is an
operational failure and does not consume a scientific attempt. Once the runner
starts `execute-all`, Attempt 001 is consumed and the frozen attempt policy applies.

### Post-run Kaggle identity binding

Kaggle kernel and control-dataset version numbers are not asserted from inside
the running kernel. The runner records only facts available at runtime: the
configured slugs/URLs, mount paths, the unique ratification-receipt SHA-256, and
a canonical SHA-256 listing of every regular file in the mounted control root.

After the run, and before scientific adjudication is accepted, the dispatcher must:

1. query the Kaggle API for the completed kernel slug, version, URL, and status;
2. query the Kaggle API for the attached control-dataset version;
3. download that exact dataset version and reproduce the runner's canonical
   listing (`SHA-256`, two spaces, POSIX relative path, newline; rows sorted by
   POSIX relative path; symlinks inadmissible);
4. require byte equality of the reproduced listing and equality of its SHA-256
   with `control_dataset_listing_sha256` in `EXECUTION_REPORT.json`;
5. bind the API observations to the execution-report SHA-256, ratification-receipt
   SHA-256, runner SHA-256, and output-file hashes in a post-run binding receipt.

Missing API observations, a non-complete kernel, or any listing/hash mismatch
produces `EXECUTION_IDENTITY_UNBOUND`; no scientific verdict is permitted and no
scientific retry is automatically authorized.

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
- `instance=batteryml-protocol-generalization-s2.1-kaggle`;
- this final preregistration SHA-256;
- the final S2.1 driver SHA-256;
- operator name and ratification timestamp;
- `operator_verbatim_statement` (verbatim text of operator ratification);
- `operator_statement_location` (identifier of the message or session where uttered).

Until that receipt exists, preprocessing, feature extraction, fitting,
prediction, and adjudication are prohibited. Environment, determinism, and import-only probes
are not scientific runs and may occur before ratification. Direct-to-main push is
acceptable for this instance; merge-click is not required. Operator ratification
remains an independent step following Claude PASS.
