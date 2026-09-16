# BatteryML protocol generalization — S2 Kaggle

This repository is the preregistration and evidence index for a separate,
resource-adapted preregistered re-execution of the BatteryML MATR1 protocol-generalization
experiment.

Status: **PRE-RUN — execution blocked pending operator ratification**

S2 does not continue the partially executed S1 run. It starts a complete new
execution chain on Kaggle CPU infrastructure. All twelve combinations of two
universes, two splits, and three models must run again from frozen inputs.

## Scope

- Primary universe: 83 cells, excluding `b2c1`.
- Sensitivity universe: 84 cells, including `b2c1`.
- Split A: BatteryML MATR1 primary assignment.
- Split B: minimum-change, exact-size, protocol-disjoint assignment.
- Models: Variance, Ridge, and XGBoost.
- Metrics: test RMSE (primary) and MAE (secondary).
- No neural models before gate adjudication.

The experiment tests whether performance under the published
protocol-overlap evaluation transfers unchanged to held-out charging
protocols under a preregistered minimum-change partition. It does not characterize
the original benchmark as data leakage.

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

Cross-environment relative tolerance is frozen at **1.0%**. If any exposed S1 result
in S2 deviates by >1.0% relative, disposition is `DEFERRED_ENVIRONMENT_DIVERGENCE`
and scientific triggers are not adjudicated.

Trigger 3 is pre-exposed and carries no independent confirmatory weight because
S1 already established Variance B < Variance A. Triggers 1 and 2 derive their
decision weight exclusively from unverified models.

## Receipts and frozen artifacts

- `PREREGISTRATION.md` — governing S2 design candidate.
- `s2_kaggle_driver.py` — fail-closed execution driver.
- `ENVIRONMENT.md` — observed Kaggle host, hardware admission, and closure rules.
- `environment-lock.txt` — exact relevant versions and closure hashes.
- `exposure-receipt.json` — frozen prior knowledge boundary and trigger classifications.
- `attempt-policy-receipt.json` — 2-attempt maximum policy and ledger requirements.
- `determinism-receipt.json` — pre-run synthetic fixture determinism verification (`rename -> rerun -> byte-identical match`).
- `l0-provenance-receipt.json` — official TRI/MATR CC BY 4.0 provenance and licensing receipt.
- `environment-resource-receipt.json` — hardware admission (exact 4 CPUs, cgroup limit tracking, frozen XGBoost parameters).
- `raw-hash-probe.json` — Kaggle-side byte-identity receipt for raw inputs.
- `compatibility-probe.json` — import and estimator-constructor smoke receipt.
- `driver-verify.json` — full frozen-driver pre-run verification receipt.
- `batteryml-protocol-generalization-split-manifest.csv` — frozen assignments.
- `batteryml-source-files.sha256` — pinned BatteryML source manifest.

Raw HDF5 inputs, private Kaggle dataset material, credentials, and S1 local
scratch data are intentionally excluded from this public repository. S2 reads
the raw files from Kaggle dataset `rickandjoe/mit-battery-degradation-dataset`
read-only; independent hash probing established byte identity with verified
MATR source files before ratification.
