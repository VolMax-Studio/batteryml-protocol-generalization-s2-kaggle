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

