# BatteryML protocol generalization — S2.1 Kaggle (Execution Repair)

This repository is the preregistration and evidence index for `batteryml-protocol-generalization-s2.1-kaggle`, an execution-repair instance of the BatteryML MATR1 protocol-generalization experiment.

Status: **PRE-RUN — execution blocked pending Operator ratification of S2.1**

## S2 Closure & Precedent
The previous instance `batteryml-protocol-generalization-s2-kaggle` deterministically aborted on Attempt 001 during child process environment admission due to `PYTHONPATH` site pollution. The Operator formally classified Attempt 001 as `PRE-SCIENTIFIC_EXECUTION_FAILURE`. S2 is formally closed and preserved under git tag [`s2-closed`](https://github.com/VolMax-Studio/batteryml-protocol-generalization-s2-kaggle/releases/tag/s2-closed) (commit `2ad8e8c`).

There is **no additional scientific exposure from S2 Attempt 001**: raw `.mat` files were hashed during preflight input verification, but never loaded into BatteryML (`load_batch` was never called). S2.1 executes the governing scientific design under a repaired driver that isolates `pip freeze` and validates module file-path provenance.

## Scope

- Primary universe: 83 cells, excluding `b2c1`.
- Sensitivity universe: 84 cells, including `b2c1`.
- Split A: BatteryML MATR1 primary assignment.
- Split B: minimum-change, exact-size, protocol-disjoint assignment.
- Models: Variance, Ridge, and XGBoost.
- Metrics: test RMSE (primary) and MAE (secondary).
- No neural models before gate adjudication.

The experiment tests whether performance under the published protocol-overlap evaluation transfers unchanged to held-out charging protocols under a preregistered minimum-change partition. It does not characterize the original benchmark as data leakage.

## Prior knowledge boundary and exposure classification

Before S2 was designed, S1 had already exposed three results:

| S1 result | RMSE | MAE | Exposure status |
|---|---:|---:|---|
| Variance A | 136.1296 | 109.0649 | exposed |
| Variance B | 133.4759 | 109.7309 | exposed (relative change −1.95%, RMSE_B < RMSE_A) |
| Ridge A | 115.7892 | 80.4132 | exposed |
| Ridge B | unverified | unverified | exposure: unverified |
| XGBoost A | unverified | unverified | exposure: unverified |
| XGBoost B | unverified | unverified | exposure: unverified |

Cross-environment relative tolerance is frozen at **1.0%**. If any exposed S1 result in S2.1 deviates by >1.0% relative, disposition is `DEFERRED_ENVIRONMENT_DIVERGENCE` and scientific triggers are not adjudicated.

Trigger 3 is pre-exposed and carries no independent confirmatory weight because S1 already established Variance B < Variance A. Triggers 1 and 2 derive their decision weight exclusively from unverified models.

## Receipts and frozen artifacts

- `PREREGISTRATION.md` — governing S2.1 design candidate.
- `PREREGISTRATION_DIFF.md` — unified diff against S2 (`2ad8e8c`) proving zero scientific lines changed.
- `FAILURES.md` — S2 Attempt 001 failure documentation and Operator verbatim ratification statement.
- `s2_kaggle_driver.py` — fail-closed execution driver with isolated `pip freeze` and module path verification.
- `smoke-test-receipt.json` — pre-ratification Kaggle CPU smoke test PASS receipt.
- `exposure-receipt.json` — frozen prior knowledge boundary and trigger classifications.
- `attempt-policy-receipt.json` — attempt policy requiring formal Operator classification for Attempt 002.
- `determinism-receipt.json` — pre-run synthetic fixture determinism verification (`rename -> rerun -> byte-identical match`).
- `l0-provenance-receipt.json` — official TRI/MATR CC BY 4.0 provenance and licensing receipt.
- `environment-resource-receipt.json` — hardware admission (exact 4 CPUs, cgroup limit tracking, frozen XGBoost parameters).
- `batteryml-protocol-generalization-split-manifest.csv` — frozen assignments.
- `batteryml-source-files.sha256` — pinned BatteryML source manifest.

Raw HDF5 inputs, private Kaggle dataset material, credentials, and S1 local scratch data are intentionally excluded from this public repository. S2.1 reads the raw files from Kaggle dataset `rickandjoe/mit-battery-degradation-dataset` read-only; independent hash probing established byte identity with verified MATR source files before ratification.
