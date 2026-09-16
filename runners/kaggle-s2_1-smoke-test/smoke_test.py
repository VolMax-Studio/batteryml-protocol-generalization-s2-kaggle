#!/usr/bin/env python3
"""Pre-ratification Kaggle CPU smoke test for S2.1 parent->child environment admission."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def main() -> None:
    print(f"[{utcnow()}] [SMOKE-TEST] Initializing S2.1 parent->child smoke test...")

    runner_path = Path(__file__).resolve()
    runner_sha = sha256_file(runner_path)
    print(f"[{utcnow()}] [SMOKE-TEST] Runner script: {runner_path} (SHA-256: {runner_sha})")

    driver_candidates = sorted(Path("/kaggle/input").rglob("s2_kaggle_driver.py"))
    if len(driver_candidates) != 1:
        raise RuntimeError(f"Expected 1 s2_kaggle_driver.py, found {driver_candidates!r}")
    driver = driver_candidates[0]
    control_root = driver.parent
    driver_sha = sha256_file(driver)
    print(f"[{utcnow()}] [SMOKE-TEST] Found mounted driver: {driver} (SHA-256: {driver_sha})")

    raw_candidates = sorted(Path("/kaggle/input").rglob("2017-05-12_batchdata_updated_struct_errorcorrect.mat"))
    if not raw_candidates:
        raise RuntimeError("Raw MATR dataset not found in /kaggle/input")
    raw_root = raw_candidates[0].parent

    os.environ["S2_INPUT_ROOT"] = str(control_root)
    os.environ["S2_RAW_ROOT"] = str(raw_root)
    os.environ["S2_WORKING_ROOT"] = "/kaggle/working"

    working = Path("/kaggle/working")
    for d in ["s2-artifact", "s2-site-packages"]:
        p = working / d
        if p.exists():
            raise RuntimeError(f"Pre-existing path found: {p}")

    cmd = [sys.executable, str(driver), "smoke-test-child"]
    print(f"[{utcnow()}] [SMOKE-TEST] Running: {' '.join(cmd)}")
    sys.stdout.flush()

    start = utcnow()
    completed = subprocess.run(cmd, text=True, capture_output=True)
    end = utcnow()

    print("=== STDOUT ===")
    print(completed.stdout)
    print("=== STDERR ===")
    print(completed.stderr)
    print(f"Exit code: {completed.returncode}")

    artifact_dir = working / "s2-artifact"
    parent_receipt_file = artifact_dir / "smoke-test-parent-receipt.json"
    child_receipt_file = artifact_dir / "smoke-test-child-receipt.json"

    report = {
        "start_utc": start,
        "end_utc": end,
        "exit_code": completed.returncode,
        "status": "PASS" if completed.returncode == 0 else "FAIL",
        "governing_driver_path": str(driver),
        "governing_driver_sha256": driver_sha,
        "runner_script_path": str(runner_path),
        "runner_script_sha256": runner_sha,
        "control_dataset_root": str(control_root),
        "control_dataset_slug": "volmax1/batteryml-protocol-generalization-s2-controls",
        "stdout": completed.stdout,
        "stderr": completed.stderr,
    }

    if parent_receipt_file.is_file():
        report["parent_receipt"] = json.loads(parent_receipt_file.read_text())
    if child_receipt_file.is_file():
        report["child_receipt"] = json.loads(child_receipt_file.read_text())

    (working / "SMOKE_TEST_REPORT.json").write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n"
    )
    print(f"[{utcnow()}] [SMOKE-TEST] Completed with status: {report['status']}")
    if completed.returncode != 0:
        sys.exit(completed.returncode)


if __name__ == "__main__":
    main()
