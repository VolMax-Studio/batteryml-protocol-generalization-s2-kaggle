#!/usr/bin/env python3
"""Fail-closed runner for BatteryML S2.1 Attempt 001 on Kaggle CPU."""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


INSTANCE = "batteryml-protocol-generalization-s2.1-kaggle"
KERNEL_SLUG = "volmax1/batteryml-s2-1-execution-run"
KERNEL_URL = f"https://www.kaggle.com/code/{KERNEL_SLUG}"
CONTROL_DATASET_SLUG = "volmax1/batteryml-protocol-generalization-s2-controls"
EXPECTED_PREREG_SHA256 = "6b027e7426a51caae616b4721bddbe4b62f368e4d17ae659de0399c7b215d92f"
EXPECTED_DRIVER_SHA256 = "c943e1d52478bbec578ec1d06dcbc84b627f33f3e73e3edd18a38c43dbfc65b9"
EXPECTED_SPLIT_MANIFEST_SHA256 = "96695e534718733469ba108ee3c1372e29351710235d5b47020f6bd9ae2ce722"
KERNEL_ID_PENDING = (
    f"{KERNEL_SLUG}/POST_RUN_API_BINDING_PENDING ({KERNEL_URL})"
)


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def read_json(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object in {path}")
    return value


def read_key_value_receipt(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    return values


def deterministic_listing(root: Path) -> tuple[str, str]:
    """Return canonical SHA-256 listing text and its SHA-256."""
    rows: list[str] = []
    for path in sorted(root.rglob("*"), key=lambda item: item.relative_to(root).as_posix()):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            raise RuntimeError(f"Symlink is not admissible in control dataset: {relative}")
        if path.is_file():
            rows.append(f"{sha256_file(path)}  {relative}\n")
    if not rows:
        raise RuntimeError("Control dataset contains no regular files")
    text = "".join(rows)
    return text, hashlib.sha256(text.encode("utf-8")).hexdigest()


def validate_control_mount(
    control_root: Path,
    receipt_path: Path,
) -> tuple[str, dict[str, Any]]:
    driver = control_root / "s2_kaggle_driver.py"
    prereg = control_root / "PREREGISTRATION.md"
    split_manifest = control_root / "batteryml-protocol-generalization-split-manifest.csv"
    expected_files = {
        driver: EXPECTED_DRIVER_SHA256,
        prereg: EXPECTED_PREREG_SHA256,
        split_manifest: EXPECTED_SPLIT_MANIFEST_SHA256,
    }
    for path, expected in expected_files.items():
        if not path.is_file() or sha256_file(path) != expected:
            raise RuntimeError(f"Frozen input SHA-256 mismatch: {path}")

    receipt = read_key_value_receipt(receipt_path)
    required_receipt = {
        "status": "RATIFIED",
        "instance": INSTANCE,
        "prereg_sha256": EXPECTED_PREREG_SHA256,
        "driver_sha256": EXPECTED_DRIVER_SHA256,
    }
    for key, expected in required_receipt.items():
        if receipt.get(key) != expected:
            raise RuntimeError(f"Ratification receipt {key} mismatch")
    for key in (
        "operator",
        "ratified_at",
        "operator_verbatim_statement",
        "operator_statement_location",
    ):
        if not receipt.get(key, "").strip():
            raise RuntimeError(f"Ratification receipt lacks {key}")

    listing_text, listing_sha = deterministic_listing(control_root)
    mount_receipt = {
        "configured_slug": CONTROL_DATASET_SLUG,
        "mount_path": str(control_root),
        "version": None,
        "version_binding_status": "POST_RUN_API_BINDING_PENDING",
        "listing_sha256": listing_sha,
        "file_count": len(listing_text.splitlines()),
    }
    return listing_text, mount_receipt


def write_report(path: Path, report: dict[str, Any]) -> None:
    path.write_text(json.dumps(report, indent=2, sort_keys=True) + "\n")


def main() -> None:
    print(f"[{utcnow()}] [S2-EXECUTE] Initializing fail-closed S2.1 runner...")
    input_root = Path("/kaggle/input")
    working = Path("/kaggle/working")
    report_path = working / "EXECUTION_REPORT.json"

    driver_candidates = sorted(input_root.rglob("s2_kaggle_driver.py"))
    if len(driver_candidates) != 1:
        raise RuntimeError(f"Expected exactly one s2_kaggle_driver.py, found {len(driver_candidates)}")
    driver = driver_candidates[0]
    control_root = driver.parent

    receipt_candidates = sorted(input_root.rglob("ratification-receipt.txt"))
    if len(receipt_candidates) != 1:
        raise RuntimeError(
            f"Expected exactly one ratification-receipt.txt, found {len(receipt_candidates)}"
        )
    receipt_path = receipt_candidates[0]
    if receipt_path.parent != control_root:
        raise RuntimeError("Unique ratification receipt is not at the mounted control dataset root")

    raw_candidates = sorted(
        input_root.rglob("2017-05-12_batchdata_updated_struct_errorcorrect.mat")
    )
    if len(raw_candidates) != 1:
        raise RuntimeError(f"Expected exactly one MATR batch1 file, found {len(raw_candidates)}")
    raw_root = raw_candidates[0].parent

    listing_text, control_mount = validate_control_mount(control_root, receipt_path)
    listing_path = working / "control-dataset-files.sha256"
    listing_path.write_text(listing_text)

    for forbidden in ("s2-artifact", "s2-processed-matr", "s2-site-packages"):
        path = working / forbidden
        if path.exists():
            raise RuntimeError(f"Pre-existing namespace path found: {path}")

    cmd = [
        sys.executable,
        str(driver),
        "execute-all",
        "--ratification-receipt",
        str(receipt_path),
        "--attempt",
        "1",
        "--kernel-id",
        KERNEL_ID_PENDING,
    ]
    report: dict[str, Any] = {
        "runner_preflight_utc": utcnow(),
        "status": "PREFLIGHT_PASS_API_BINDING_PENDING",
        "scientific_run_executed": False,
        "driver_process_started": False,
        "post_run_api_binding_required": True,
        "kernel_binding": {
            "configured_slug": KERNEL_SLUG,
            "configured_url": KERNEL_URL,
            "version": None,
            "status": "POST_RUN_API_BINDING_PENDING",
        },
        "control_dataset_mount": control_mount,
        "control_dataset_listing": listing_text,
        "control_dataset_listing_sha256": control_mount["listing_sha256"],
        "control_dataset_listing_path": str(listing_path),
        "ratification_receipt_path": str(receipt_path),
        "ratification_receipt_sha256": sha256_file(receipt_path),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "governing": {
            "preregistration_sha256": EXPECTED_PREREG_SHA256,
            "driver_sha256": EXPECTED_DRIVER_SHA256,
            "split_manifest_sha256": EXPECTED_SPLIT_MANIFEST_SHA256,
        },
        "command": cmd,
    }
    write_report(report_path, report)

    print(f"[{utcnow()}] [S2-EXECUTE] Preflight PASS; spawning frozen driver.")
    sys.stdout.flush()
    report["driver_process_started"] = True
    report["runner_start_utc"] = utcnow()
    write_report(report_path, report)

    process = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
        env={
            **dict(os.environ),
            "S2_INPUT_ROOT": str(control_root),
            "S2_RAW_ROOT": str(raw_root),
            "S2_WORKING_ROOT": str(working),
        },
    )
    assert process.stdout is not None
    for line in iter(process.stdout.readline, ""):
        print(line, end="", flush=True)
    process.stdout.close()
    returncode = process.wait()

    report["runner_end_utc"] = utcnow()
    report["exit_code"] = returncode
    report["status"] = (
        "SCIENTIFIC_EXECUTION_COMPLETE_API_BINDING_PENDING"
        if returncode == 0
        else "DRIVER_FAILED_API_BINDING_PENDING"
    )
    artifact_dir = working / "s2-artifact"
    if artifact_dir.is_dir():
        for name in ("completion-receipt.json", "adjudication.json", "attempt-ledger.json"):
            path = artifact_dir / name
            if path.is_file():
                report[name.removesuffix(".json").replace("-", "_")] = read_json(path)
        manifest_path = artifact_dir / "artifact-files.sha256"
        if manifest_path.is_file():
            report["artifact_manifest_content"] = manifest_path.read_text()
    if returncode == 0 and (artifact_dir / "completion-receipt.json").is_file():
        report["scientific_run_executed"] = True
    write_report(report_path, report)
    print(f"[{utcnow()}] [S2-EXECUTE] Driver return code: {returncode}")
    if returncode != 0:
        raise SystemExit(returncode)


if __name__ == "__main__":
    main()
