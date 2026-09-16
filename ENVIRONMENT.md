# S2 Kaggle environment closure

The private probe kernel `volmax1/batteryml-frozen-environment-probe` completed
on 2026-09-16 before S2 was frozen. It executed no BatteryML preprocessing,
feature extraction, fitting, or prediction.

## Direct observations

- Python: `3.12.13` at `/usr/bin/python3`.
- Platform: Linux `6.12.90+`, x86_64, glibc 2.35.
- Logical CPUs: Exactly 4.
- Total RAM: 33,659,383,808 bytes (31.348 GiB).
- Available RAM during probe: 32,722,042,880 bytes (30.475 GiB).
- Swap: 0 bytes.
- `/kaggle/working` free space: 20,940,562,432 bytes (19.502 GiB).
- GPU is prohibited for S2.

Probe receipt SHA-256:
`6791fb6565c113b3e46fc4820db85146c66be93dbcacac6a86b3d400113bd7ee`.

Complete observed base `pip freeze`: 872 lines, canonical trailing newline,
SHA-256:
`e137b12924bbb4fbb83f45c8ccb3419ba4e5556d01d977a05a7ab4e175155c35`.

## Hardware admission rules

1. **CPU logical core count**: Exactly **4** logical CPUs are required (`logical_cpus == 4`). Hosts with core counts differing from 4 fail admission closed to preserve XGBoost threading semantics without modifying upstream scientific model code.
2. **Memory tracking**: Both `/proc/meminfo MemTotal` and cgroup memory limits (`memory.max` under cgroup v2, or `memory.limit_in_bytes` under cgroup v1) are read and recorded in execution receipts.
3. **Package freeze**: Complete 872-line base freeze hash must match `e137b12924bbb4fbb83f45c8ccb3419ba4e5556d01d977a05a7ab4e175155c35`.
4. **XGBoost parameters**: Resolved constructor parameters are frozen and recorded in `environment-resource-receipt.json`.

`addict` and `fire`, absent from the Kaggle base image, are supplied as hashed
offline wheels and installed into a run-local target directory without
internet access. No other package mutation is permitted.

## Raw-input mount closure and L0 license

A separate private, CPU-only, internet-off hash probe attached
`rickandjoe/mit-battery-degradation-dataset` as a read-only Kaggle input. Both
in-scope raw files matched the frozen local byte sizes and SHA-256 values.

Raw hash-probe receipt SHA-256:
`d2e33a03c4f8034449f42eb5e235f5ae0279a09fa9a41b15fe0a1dfa7c9fe66a`.

L0 raw data licensing is verified against the official Toyota Research Institute (TRI)
MATR repository (`https://data.matr.io/1/`), which publishes the dataset under the
**Creative Commons Attribution 4.0 International (CC BY 4.0)** license.
License provenance is documented in `l0-provenance-receipt.json`.

## Compatibility, driver, and determinism closure

The private control dataset was created as version 1 and reached status
`ready`. Kaggle expanded its source and wheel directories into the expected
read-only mount tree.

An import-only compatibility probe verified:

- `addict 2.4.0` and `fire 0.7.1` from the frozen offline wheels;
- BatteryML preprocessing, task, and MATR splitter imports;
- construction, without fitting, of Variance, Ridge, and XGBoost wrappers;
- frozen split and source-manifest hashes.

Compatibility receipt SHA-256:
`b201d608050e65673afd12838611727435bca4a8c858fa98a86801147646892a`.

Determinism verification confirmed bit-identical reproduction (`rename -> rerun -> byte-identical match`)
across all three models on synthetic test cells prior to scientific runs (`determinism-receipt.json`).

The driver `verify` command directly confirms the 872-line base freeze hash, Python 3.12.13,
exact 4 CPUs, RAM minimum, 205 tracked source files, both raw hashes, all three config
hashes, wheel hashes, split hash, and the four frozen membership counts.
