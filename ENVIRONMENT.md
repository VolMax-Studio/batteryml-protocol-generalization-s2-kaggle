# S2 Kaggle environment closure

The private probe kernel `volmax1/batteryml-frozen-environment-probe` completed
on 2026-09-16 before S2 was frozen. It executed no BatteryML preprocessing,
feature extraction, fitting, or prediction.

## Direct observations

- Python: `3.12.13` at `/usr/bin/python3`.
- Platform: Linux `6.12.90+`, x86_64, glibc 2.35.
- Logical CPUs: 4.
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

## Closure decision

S2 adopts this Kaggle-native environment instead of pretending it is the S1
environment. Exact Python and base-freeze checks are fail-closed. Minimum RAM
is 31 GiB because that is below the directly observed 31.348 GiB while still
excluding the 15 GiB local host that blocked S1.

`addict` and `fire`, absent from the Kaggle base image, are supplied as hashed
offline wheels and installed into a run-local target directory without
internet access. No other package mutation is permitted.

## Raw-input mount closure

A separate private, CPU-only, internet-off hash probe attached
`rickandjoe/mit-battery-degradation-dataset` as a read-only Kaggle input. Both
in-scope raw files matched the frozen local byte sizes and SHA-256 values.

Raw hash-probe receipt SHA-256:
`d2e33a03c4f8034449f42eb5e235f5ae0279a09fa9a41b15fe0a1dfa7c9fe66a`.

The first probe version failed before hashing because it assumed the obsolete
mount path `/kaggle/input/mit-battery-degradation-dataset`. Version 2 discovered
the actual mount root under `/kaggle/input/datasets/rickandjoe/` and completed.

## Compatibility and driver closure

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

The frozen S2 driver then ran its own `verify` command against both mounted
datasets. It returned exit code 0 and `PASS`, with no stderr. It directly
confirmed the 872-line base freeze hash, Python 3.12.13, 33,659,379,712 bytes
RAM, four CPUs, 205 tracked source files, both raw hashes, all three config
hashes, wheel hashes, split hash, and the four frozen membership counts.

Driver-verification receipt SHA-256:
`20434aa672f72af0fb8a995d23a664caa1027828c859ddf9d6022937aa1fc698`.

Both probes explicitly record `scientific_run_executed=false`. No raw
preprocessing, feature extraction, fitting, prediction, or adjudication has
occurred in S2.
