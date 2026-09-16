#!/usr/bin/env python3
"""Non-scientific probe of the Kaggle-mounted S2.1 control dataset tree."""

from __future__ import annotations

import hashlib
import json
import os
from datetime import datetime, timezone
from pathlib import Path


CONTROL_DATASET_SLUG = "volmax1/batteryml-protocol-generalization-s2-controls"
EXPECTED_DRIVER_SHA256 = "c943e1d52478bbec578ec1d06dcbc84b627f33f3e73e3edd18a38c43dbfc65b9"
EXPECTED_DOWNLOADED_V7_LISTING_SHA256 = (
    "1fd46b85d24f3b0b64083fda9593ccf36db4fb1ae2b0bbf0966d5633ac5acc3e"
)
GOVERNING_RUNNER_SHA256 = (
    "fd74df3b17b2ea082041ca50d35b0c8a6015df7f8c87f4f502f4a472340d939a"
)


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


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


def main() -> None:
    input_root = Path(os.environ.get("PROBE_INPUT_ROOT", "/kaggle/input"))
    output_root = Path(os.environ.get("PROBE_OUTPUT_ROOT", "/kaggle/working"))
    output_root.mkdir(parents=True, exist_ok=True)

    drivers = sorted(input_root.rglob("s2_kaggle_driver.py"))
    if len(drivers) != 1:
        raise RuntimeError(f"Expected exactly one s2_kaggle_driver.py, found {len(drivers)}")
    driver = drivers[0]
    if sha256_file(driver) != EXPECTED_DRIVER_SHA256:
        raise RuntimeError("Mounted driver SHA-256 differs from the frozen scientific driver")
    control_root = driver.parent

    listing_text, listing_sha = deterministic_listing(control_root)
    listing_path = output_root / "mounted-control-dataset-files.sha256"
    listing_path.write_text(listing_text)

    receipt = {
        "control_dataset_configured_slug": CONTROL_DATASET_SLUG,
        "control_dataset_mount_path": str(control_root),
        "driver_sha256": sha256_file(driver),
        "expected_downloaded_v7_listing_sha256": EXPECTED_DOWNLOADED_V7_LISTING_SHA256,
        "file_count": len(listing_text.splitlines()),
        "governing_runner_sha256": GOVERNING_RUNNER_SHA256,
        "listing_bytes": len(listing_text.encode("utf-8")),
        "mounted_listing_path": str(listing_path),
        "mounted_listing_sha256": listing_sha,
        "models_executed": [],
        "probe_completed_at_utc": datetime.now(timezone.utc).isoformat(),
        "raw_matr_data_accessed": False,
        "scientific_driver_executed": False,
        "scientific_run_executed": False,
        "status": (
            "PASS_MOUNT_LISTING_MATCHES_DOWNLOADED_V7"
            if listing_sha == EXPECTED_DOWNLOADED_V7_LISTING_SHA256
            else "FAIL_MOUNT_LISTING_MISMATCH"
        ),
    }
    receipt_path = output_root / "MOUNT_LISTING_PROBE.json"
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps(receipt, indent=2, sort_keys=True))

    if listing_sha != EXPECTED_DOWNLOADED_V7_LISTING_SHA256:
        raise RuntimeError("Kaggle mount listing does not match explicit v7 download listing")


if __name__ == "__main__":
    main()
