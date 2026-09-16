# BatteryML protocol generalization — S2 Kaggle

This repository is the preregistration and evidence index for a separate,
resource-adapted replication of the BatteryML MATR1 protocol-generalization
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
protocols. It does not characterize the original benchmark as data leakage.

## Files

- `PREREGISTRATION.md` — governing S2 design candidate.
- `ENVIRONMENT.md` — observed Kaggle host and closure rules.
- `environment-lock.txt` — exact relevant versions and closure hashes.
- `raw-hash-probe.json` — Kaggle-side byte-identity receipt for raw inputs.
- `compatibility-probe.json` — import and estimator-constructor smoke receipt.
- `driver-verify.json` — full frozen-driver pre-run verification receipt.
- `batteryml-protocol-generalization-split-manifest.csv` — frozen assignments.
- `batteryml-source-files.sha256` — pinned BatteryML source manifest.
- `s2_kaggle_driver.py` — fail-closed execution driver.

Raw HDF5 inputs, private Kaggle dataset material, credentials, and S1 local
scratch data are intentionally excluded from this public repository. S2 reads
the raw files from Kaggle dataset `rickandjoe/mit-battery-degradation-dataset`;
a hash-only probe independently established byte identity with the frozen local
inputs before ratification.

## Prior knowledge boundary

Before S2 was designed, S1 had already exposed three results:

| S1 result | RMSE | MAE |
|---|---:|---:|
| Variance A | 136.1296 | 109.0649 |
| Variance B | 133.4759 | 109.7309 |
| Ridge A | 115.7892 | 80.4132 |

They are disclosed as prior knowledge and are not S2 execution results.
