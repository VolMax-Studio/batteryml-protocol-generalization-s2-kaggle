# Unified Diff: S2 (`2ad8e8c`) vs S2.1 (`PREREGISTRATION.md`)

This diff proves that all modifications between S2 and S2.1 are strictly confined to:
1. Instance name (`batteryml-protocol-generalization-s2.1-kaggle`);
2. Documentation of the S2 Attempt 001 failure, Operator formal classification, and exact exposure status (*"no additional scientific exposure from S2 Attempt 001; raw files hashed, not loaded"*);
3. Clarification of isolated `pip freeze` execution, module path provenance, and container cgroup memory tracking in environment admission;
4. Updated attempt policy with initial disposition `FAILED_PENDING_OPERATOR_CLASSIFICATION` and mandatory `--kernel-id` tracking in the ledger;
5. Instance name in ratification requirements.

**All scientific sections (data universes, split manifest, models, configs, seeds, metrics, triggers, and interpretation boundary) are 100% byte-identical.**

```diff
--- a/PREREGISTRATION.md (S2 @ 2ad8e8c)
+++ b/PREREGISTRATION.md (S2.1)
@@ -1,12 +1,14 @@
-# BatteryML protocol-generalization S2 — Kaggle preregistration candidate
+# BatteryML protocol-generalization S2.1 — Kaggle preregistration candidate (Execution Repair)
 
 Prepared: 2026-09-16 (Europe/Belgrade)  
 Status: **FINAL CANDIDATE — RUN PROHIBITED pending Ivan/Operator ratification**
 
 ## Study class and prior knowledge
 
-S2 is a **resource-adapted preregistered re-execution**, not a continuation of
-S1 and not a fully blind confirmatory study.
+S2.1 is an **execution-repair instance** of S2, not a continuation of
+S1 and not a fully blind confirmatory study. S2 was terminated following a pre-scientific
+environment admission mismatch in child processes; S2.1 implements the exact governing
+scientific design with an isolated pip freeze and verified module provenance.
 
 S1 remains locked as `EXECUTION_BLOCKED_RESOURCE — model gate incomplete`.
 Before this S2 freeze, the following S1 results were known from the partial S1 run:
@@ -24,8 +26,21 @@ Exposure status for the remaining model cells is unverified.
 - Primary83 XGBoost B: `exposure: unverified`;
 - All Sensitivity84 combinations (Variance A/B, Ridge A/B, XGBoost A/B): `exposure: unverified`.
 
-S1 values cannot be copied into, substituted for, or adjudicated as S2
-results. S2 must execute its entire matrix from the beginning.
+S1 values cannot be copied into, substituted for, or adjudicated as S2.1
+results. S2.1 must execute its entire matrix from the beginning.
+
+### S2 Attempt 001 execution failure and exposure status
+
+S2 Attempt 001 on Kaggle CPU host (`volmax1/batteryml-s2-attempt-001`) deterministically aborted
+during preflight environment admission inside child process `00-preprocess` prior to directory
+creation (`PROCESSED.mkdir`) or loading of any MATR raw batch data (`load_batch`). The failure occurred
+because `run_child` passed `PYTHONPATH=/kaggle/working/s2-site-packages`, causing child `pip freeze`
+to enumerate offline wheels (`addict`, `fire`) as 874 lines instead of 872 base packages.
+The Operator formally ratified the classification of Attempt 001 as `PRE-SCIENTIFIC_EXECUTION_FAILURE`.
+Raw files were hashed in binary read mode during preflight input verification (`verify_inputs()`), but never
+loaded into the BatteryML preprocessing pipeline (`load_batch` was never called). No additional scientific
+exposure occurred from S2 Attempt 001 beyond the previously known S1 exposed metrics. S2 is formally closed,
+and S2.1 executes the governing scientific design under the repaired driver.
 
 ### Cross-environment divergence disposition
 
@@ -154,12 +169,12 @@ after ratification. No neural model is part of S2.
 
 - Private Kaggle CPU kernel; internet disabled; GPU disabled.
 - Python exactly `3.12.13`.
-- Linux x86_64; at least `31 GiB` total RAM.
+- Linux x86_64; at least `31 GiB` total RAM (`mem_total_bytes >= 31 GiB`). Hardware admission evaluates `/proc/meminfo MemTotal` (observed: 31.35 GiB / 33,659,383,808 bytes). The container cgroup memory limit (`memory.max`) in Kaggle CPU containers is tracked (observed: 30.00 GiB / 32,212,254,720 bytes).
 - **CPU admission**: Exactly **4 logical CPU cores** required (`logical_cpus == 4`). Hosts with core counts different from 4 fail admission closed. This requirement freezes XGBoost threading semantics without altering upstream BatteryML code.
 - **Memory tracking**: Both `/proc/meminfo MemTotal` and cgroup memory limit (`memory.max` under cgroup v2, or `memory.limit_in_bytes` under cgroup v1) are recorded in the environment receipt.
 - Kaggle base `pip freeze` SHA-256 exactly
-  `e137b12924bbb4fbb83f45c8ccb3419ba4e5556d01d977a05a7ab4e175155c35` (872 lines).
-- Offline wheels: `addict-2.4.0-py3-none-any.whl` (`249bb56b...`) and `fire-0.7.1-py3-none-any.whl` (`e43fd8a5...`).
+  `e137b12924bbb4fbb83f45c8ccb3419ba4e5556d01d977a05a7ab4e175155c35` (872 lines). In both parent and child processes, `pip freeze` is executed with `PYTHONPATH` stripped to guarantee that the base platform package image is verified without pollution from working directories.
+- Offline wheels: `addict-2.4.0-py3-none-any.whl` (`249bb56b...`) and `fire-0.7.1-py3-none-any.whl` (`e43fd8a5...`). Provenance is verified by asserting that imported module file paths reside strictly within the dedicated `s2-site-packages` directory.
 - CUDA must be unavailable.
 - Frozen XGBoost resolved execution parameters are documented in `environment-resource-receipt.json`.
 
@@ -178,13 +193,14 @@ a frozen determinism verification protocol:
 Execution is governed by a strict attempt policy frozen in `attempt-policy-receipt.json`:
 - **Maximum 2 scientific attempts** are permitted.
 - Attempt 001 executes the full 12-run matrix from an empty workspace.
-- Attempt 002 is permitted **ONLY IF** Attempt 001 failed to complete all twelve runs due to an unexpected platform/resource failure (e.g. host OOM, platform timeout, or session disconnection).
+- Any unhandled failure in Attempt 001 records initial disposition `FAILED_PENDING_OPERATOR_CLASSIFICATION`; it never automatically transitions to `FAILED_PLATFORM_RETRY_ALLOWED`.
+- Attempt 002 is permitted **ONLY IF** Attempt 001 failed to complete all twelve runs and the Operator formally classifies the failure under [L3] as an unexpected platform/resource failure (e.g. host OOM, platform timeout, or session disconnection). Any deterministic code or pre-scientific failure remains non-retryable without a new execution-repair instance.
 - Attempt 002 must be a **full restart** of all twelve runs from the beginning with identical governing hashes and environment.
 - Partial results from different attempts are **never combined or spliced**.
 - The first complete attempt is governing.
 - If Attempt 002 also fails to complete all twelve runs, the terminal disposition is **`EXECUTION_BLOCKED_RESOURCE`**.
 - An immutable attempt ledger (`attempt-ledger.json`) records for each attempt:
-  - Kaggle kernel version / URL;
+  - Kaggle kernel slug, version, and URL (mandatory `--kernel-id` argument passed to `execute-all`);
   - Attempt number (1 or 2);
   - Start and end UTC timestamps;
   - Governing preregistration SHA-256 and driver SHA-256;
@@ -262,9 +278,9 @@ universal failure on unseen protocols, or invalidity of other BatteryML datasets
 The driver requires a receipt containing all of:
 
 - `status=RATIFIED`;
-- `instance=batteryml-protocol-generalization-s2-kaggle`;
+- `instance=batteryml-protocol-generalization-s2.1-kaggle`;
 - this final preregistration SHA-256;
-- the final S2 driver SHA-256;
+- the final S2.1 driver SHA-256;
 - operator name and ratification timestamp;
 - `operator_verbatim_statement` (verbatim text of operator ratification);
 - `operator_statement_location` (identifier of the message or session where uttered).
```
