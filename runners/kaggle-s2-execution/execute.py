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
CONTROL_DATASET_SLUG = "volmax1/batteryml-protocol-generalization-s2-controls"
EXPECTED_PREREG_SHA256 = "e573ff930e51c445e66724a37ec681873c6ea2fe7bf89d9962b817fdb5847e09"
EXPECTED_DRIVER_SHA256 = "c943e1d52478bbec578ec1d06dcbc84b627f33f3e73e3edd18a38c43dbfc65b9"
EXPECTED_SPLIT_MANIFEST_SHA256 = "96695e534718733469ba108ee3c1372e29351710235d5b47020f6bd9ae2ce722"
AUTHORIZATION_FILENAME = "execution-authorization.json"
CONTROL_VERSION_FILENAME = "control-dataset-version.json"


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


def validate_authorization(path: Path) -> dict[str, Any]:
    """Validate the immutable, post-ratification dispatch measurement receipt."""
    auth = read_json(path)
    if auth.get("schema_version") != 1 or auth.get("study_instance") != INSTANCE:
        raise RuntimeError("Execution authorization schema or study instance mismatch")

    governing = auth.get("governing")
    if not isinstance(governing, dict):
        raise RuntimeError("Execution authorization lacks governing hashes")
    expected_governing = {
        "preregistration_sha256": EXPECTED_PREREG_SHA256,
        "driver_sha256": EXPECTED_DRIVER_SHA256,
        "split_manifest_sha256": EXPECTED_SPLIT_MANIFEST_SHA256,
    }
    for key, expected in expected_governing.items():
        if governing.get(key) != expected:
            raise RuntimeError(f"Execution authorization {key} mismatch")
    receipt_sha = governing.get("ratification_receipt_sha256")
    if not isinstance(receipt_sha, str) or len(receipt_sha) != 64:
        raise RuntimeError("Execution authorization lacks frozen ratification receipt SHA-256")

    kernel = auth.get("kernel")
    if not isinstance(kernel, dict):
        raise RuntimeError("Execution authorization lacks measured kernel identity")
    slug = kernel.get("slug")
    version = kernel.get("version")
    url = kernel.get("url")
    if not isinstance(slug, str) or slug.count("/") != 1:
        raise RuntimeError("Measured kernel slug is invalid")
    if not isinstance(version, int) or isinstance(version, bool) or version < 1:
        raise RuntimeError("Measured kernel version is invalid")
    if url != f"https://www.kaggle.com/code/{slug}":
        raise RuntimeError("Measured kernel URL does not match measured slug")
    if kernel.get("measurement_source") != "kaggle_api":
        raise RuntimeError("Kernel identity was not measured through the Kaggle API")
    if not isinstance(kernel.get("measured_at_utc"), str) or not kernel["measured_at_utc"].strip():
        raise RuntimeError("Kernel identity lacks a measurement timestamp")

    control = auth.get("control_dataset")
    if not isinstance(control, dict):
        raise RuntimeError("Execution authorization lacks measured control dataset identity")
    if control.get("slug") != CONTROL_DATASET_SLUG:
        raise RuntimeError("Control dataset slug mismatch")
    if not isinstance(control.get("version"), int) or isinstance(control.get("version"), bool) or control["version"] < 1:
        raise RuntimeError("Measured control dataset version is invalid")
    listing_sha = control.get("listing_sha256")
    if not isinstance(listing_sha, str) or len(listing_sha) != 64:
        raise RuntimeError("Execution authorization lacks control dataset listing SHA-256")
    if control.get("measurement_source") != "kaggle_api":
        raise RuntimeError("Control dataset version was not measured through the Kaggle API")
    if not isinstance(control.get("measured_at_utc"), str) or not control["measured_at_utc"].strip():
        raise RuntimeError("Control dataset version lacks a measurement timestamp")
    return auth


def validate_control_mount(
    control_root: Path,
    receipt_path: Path,
    auth: dict[str, Any],
) -> tuple[str, dict[str, Any]]:
    driver = control_root / "s2_kaggle_driver.py"
    prereg = control_root / "PREREGISTRATION.md"
    split_manifest = control_root / "batteryml-protocol-generalization-split-manifest.csv"
    expected_files = {
        driver: EXPECTED_DRIVER_SHA256,
        prereg: EXPECTED_PREREG_SHA256,
        split_manifest: EXPECTED_SPLIT_MANIFEST_SHA256,
        receipt_path: auth["governing"]["ratification_receipt_sha256"],
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

    version_path = control_root / CONTROL_VERSION_FILENAME
    if not version_path.is_file():
        raise RuntimeError(f"Missing mounted dataset version receipt: {version_path}")
    version_receipt = read_json(version_path)
    control = auth["control_dataset"]
    required_version_fields = {
        "slug": control["slug"],
        "version": control["version"],
        "measurement_source": control["measurement_source"],
        "measured_at_utc": control["measured_at_utc"],
    }
    for key, expected in required_version_fields.items():
        if version_receipt.get(key) != expected:
            raise RuntimeError(f"Mounted control dataset version receipt {key} mismatch")

    listing_text, listing_sha = deterministic_listing(control_root)
    if listing_sha != control["listing_sha256"]:
        raise RuntimeError("Mounted control dataset listing SHA-256 mismatch")

    mount_receipt = {
        "slug": control["slug"],
        "version": control["version"],
        "version_receipt_path": str(version_path),
        "version_receipt_sha256": sha256_file(version_path),
        "mount_path": str(control_root),
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

    authorization_path = Path(__file__).resolve().with_name(AUTHORIZATION_FILENAME)
    if not authorization_path.is_file():
        raise RuntimeError(
            "Missing post-ratification execution-authorization.json; kernel identity is unmeasured"
        )
    auth = validate_authorization(authorization_path)

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

    listing_text, control_mount = validate_control_mount(control_root, receipt_path, auth)
    listing_path = working / "control-dataset-files.sha256"
    listing_path.write_text(listing_text)

    for forbidden in ("s2-artifact", "s2-processed-matr", "s2-site-packages"):
        path = working / forbidden
        if path.exists():
            raise RuntimeError(f"Pre-existing namespace path found: {path}")

    kernel = auth["kernel"]
    kernel_id = f"{kernel['slug']}/{kernel['version']} ({kernel['url']})"
    cmd = [
        sys.executable,
        str(driver),
        "execute-all",
        "--ratification-receipt",
        str(receipt_path),
        "--attempt",
        "1",
        "--kernel-id",
        kernel_id,
    ]
    report: dict[str, Any] = {
        "runner_preflight_utc": utcnow(),
        "status": "PREFLIGHT_PASS",
        "scientific_run_executed": False,
        "driver_process_started": False,
        "kernel": kernel,
        "control_dataset_mount": control_mount,
        "control_dataset_listing": listing_text,
        "control_dataset_listing_path": str(listing_path),
        "execution_authorization_path": str(authorization_path),
        "execution_authorization_sha256": sha256_file(authorization_path),
        "ratification_receipt_path": str(receipt_path),
        "ratification_receipt_sha256": sha256_file(receipt_path),
        "runner_sha256": sha256_file(Path(__file__).resolve()),
        "governing": auth["governing"],
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
    report["status"] = "PASS" if returncode == 0 else "FAIL"
    artifact_dir = working / "s2-artifact"
    if returncode == 0 and artifact_dir.is_dir():
        for name in ("completion-receipt.json", "adjudication.json", "attempt-ledger.json"):
            path = artifact_dir / name
            if path.is_file():
                report[name.removesuffix(".json").replace("-", "_")] = read_json(path)
        manifest_path = artifact_dir / "artifact-files.sha256"
        if manifest_path.is_file():
            report["artifact_manifest_content"] = manifest_path.read_text()
        report["scientific_run_executed"] = True
    write_report(report_path, report)
    print(f"[{utcnow()}] [S2-EXECUTE] Driver return code: {returncode}")
    if returncode != 0:
        raise SystemExit(returncode)


if __name__ == "__main__":
    main()
