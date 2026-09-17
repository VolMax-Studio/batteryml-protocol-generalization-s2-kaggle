#!/usr/bin/env python3
"""Generate the S2.1 post-run binding receipt from machine-readable evidence.

This is a non-scientific closure tool. It never fits a model and does not accept
scientific metrics on the command line. Metrics are copied from the frozen
adjudication and run receipts; all hashes and dataset-version matches are
recomputed from files.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import stat
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath
from typing import Any


INSTANCE = "batteryml-protocol-generalization-s2.1-kaggle"
KERNEL_REF = "volmax1/batteryml-s2-1-execution-run"
EXPECTED_UNIVERSES = ("primary83", "sensitivity84")
EXPECTED_SPLITS = ("a", "b")
EXPECTED_MODELS = ("variance", "ridge", "xgb")
VERSION_DIR = re.compile(r"^v([1-9][0-9]*)$")


def sha256_bytes(value: bytes) -> str:
    return hashlib.sha256(value).hexdigest()


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_object(path: Path) -> dict[str, Any]:
    value = json.loads(path.read_text())
    if not isinstance(value, dict):
        raise RuntimeError(f"Expected JSON object: {path}")
    return value


def canonical_zip_listing(archive: Path) -> tuple[bytes, int]:
    rows: list[tuple[str, str]] = []
    with zipfile.ZipFile(archive) as bundle:
        seen: set[str] = set()
        for info in bundle.infolist():
            if info.is_dir():
                continue
            relative = PurePosixPath(info.filename).as_posix()
            if relative.startswith("/") or ".." in PurePosixPath(relative).parts:
                raise RuntimeError(f"Inadmissible archive path in {archive}: {relative}")
            mode = (info.external_attr >> 16) & 0o170000
            if mode == stat.S_IFLNK:
                raise RuntimeError(f"Symlink is inadmissible in {archive}: {relative}")
            if relative in seen:
                raise RuntimeError(f"Duplicate archive path in {archive}: {relative}")
            seen.add(relative)
            rows.append((relative, sha256_bytes(bundle.read(info))))
    if not rows:
        raise RuntimeError(f"Archive contains no regular files: {archive}")
    rows.sort(key=lambda row: row[0])
    listing = "".join(f"{digest}  {relative}\n" for relative, digest in rows).encode()
    return listing, len(rows)


def enumerate_archives(root: Path) -> list[tuple[int, Path]]:
    candidates: list[tuple[int, Path]] = []
    for directory in sorted(root.iterdir()):
        match = VERSION_DIR.fullmatch(directory.name)
        if not directory.is_dir() or not match:
            continue
        archives = sorted(directory.glob("*.zip"))
        if len(archives) != 1:
            raise RuntimeError(f"Expected one zip in {directory}, found {len(archives)}")
        candidates.append((int(match.group(1)), archives[0]))
    if not candidates:
        raise RuntimeError(f"No explicit-version archives found under {root}")
    versions = [version for version, _ in candidates]
    if versions != list(range(min(versions), max(versions) + 1)):
        raise RuntimeError(f"Candidate dataset versions are not contiguous: {versions}")
    return candidates


def query_kernel() -> dict[str, Any]:
    try:
        from kaggle.api.kaggle_api_extended import KaggleApi
        from kagglesdk.kernels.types.kernels_api_service import ApiGetKernelRequest
    except ImportError as exc:
        raise RuntimeError("The authenticated Kaggle Python client is required") from exc

    api = KaggleApi()
    api.authenticate()
    status_response = api.kernels_status(KERNEL_REF)
    owner, slug = KERNEL_REF.split("/", 1)
    request = ApiGetKernelRequest()
    request.user_name = owner
    request.kernel_slug = slug
    with api.build_kaggle_client() as client:
        metadata_response = client.kernels.kernels_api_client.get_kernel(request)
    metadata = metadata_response.metadata
    status = str(status_response.status).rsplit(".", 1)[-1]
    observation = {
        "configured_ref": KERNEL_REF,
        "current_version_number": metadata.current_version_number,
        "dataset_data_sources": sorted(metadata.dataset_data_sources or []),
        "docker_image": metadata.docker_image,
        "enable_gpu": metadata.enable_gpu,
        "enable_internet": metadata.enable_internet,
        "kernel_id": metadata.id,
        "last_run_time": str(metadata.last_run_time),
        "status": status,
    }
    if observation["status"] != "COMPLETE":
        raise RuntimeError(f"Kaggle kernel is not COMPLETE: {observation['status']}")
    return observation


def collect_run_matrix(artifact: Path) -> list[dict[str, Any]]:
    runs: list[dict[str, Any]] = []
    for universe in EXPECTED_UNIVERSES:
        for split in EXPECTED_SPLITS:
            for model in EXPECTED_MODELS:
                root = artifact / "results" / universe / split / model
                prediction = root / "per-cell-predictions.csv"
                run_receipt_path = root / "run-receipt.json"
                parameter_path = root / "resolved-model-parameters.json"
                for path in (prediction, run_receipt_path, parameter_path):
                    if not path.is_file():
                        raise RuntimeError(f"Missing frozen run evidence: {path}")
                run_receipt = load_object(run_receipt_path)
                identity = (run_receipt.get("universe"), run_receipt.get("split"), run_receipt.get("model"))
                if identity != (universe, split, model):
                    raise RuntimeError(f"Run receipt identity mismatch: {run_receipt_path}")
                runs.append(
                    {
                        "mae": run_receipt["mae"],
                        "model": model,
                        "parameters_sha256": sha256_file(parameter_path),
                        "predictions_sha256": sha256_file(prediction),
                        "rmse": run_receipt["rmse"],
                        "run_receipt_sha256": sha256_file(run_receipt_path),
                        "seed": run_receipt["seed"],
                        "split": split,
                        "test_count": len(run_receipt["test_cell_ids"]),
                        "train_count": len(run_receipt["train_cell_ids"]),
                        "universe": universe,
                    }
                )
    if len(runs) != 12:
        raise RuntimeError(f"Expected 12 runs, found {len(runs)}")
    return runs


def parse_artifact_manifest(path: Path) -> dict[str, str]:
    entries: dict[str, str] = {}
    for line in path.read_text().splitlines():
        digest, separator, relative = line.partition("  ")
        if not separator or len(digest) != 64 or not relative:
            raise RuntimeError(f"Malformed artifact manifest line: {line!r}")
        entries[relative] = digest
    return entries


def write_checkpoint_manifest(artifact: Path, entries: dict[str, str]) -> Path:
    output = artifact / "checkpoint-files.sha256"
    rows = [f"{digest}  {relative}\n" for relative, digest in sorted(entries.items()) if relative.endswith(".ckpt")]
    if not rows:
        raise RuntimeError("Artifact manifest contains no checkpoint hashes")
    for row in rows:
        digest, _, relative = row.rstrip("\n").partition("  ")
        checkpoint = artifact / relative
        if not checkpoint.is_file() or sha256_file(checkpoint) != digest:
            raise RuntimeError(f"Checkpoint does not match frozen artifact manifest: {checkpoint}")
    output.write_text("".join(rows))
    return output


def write_public_manifest(output_root: Path) -> Path:
    output = output_root / "public-evidence-files.sha256"
    excluded = {
        output,
        output_root / "post-run-binding-receipt.json",
    }
    rows: list[str] = []
    for path in sorted(output_root.rglob("*"), key=lambda item: item.relative_to(output_root).as_posix()):
        if not path.is_file() or path in excluded:
            continue
        relative = path.relative_to(output_root).as_posix()
        if relative.startswith("s2-processed-matr/") or relative.endswith(".ckpt"):
            continue
        rows.append(f"{sha256_file(path)}  {relative}\n")
    output.write_text("".join(rows))
    return output


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--output-root", type=Path, required=True)
    parser.add_argument("--dataset-archives-root", type=Path, required=True)
    parser.add_argument("--receipt", type=Path)
    args = parser.parse_args()

    output_root = args.output_root.resolve()
    artifact = output_root / "s2-artifact"
    report_path = output_root / "EXECUTION_REPORT.json"
    listing_path = output_root / "control-dataset-files.sha256"
    adjudication_path = artifact / "adjudication.json"
    ledger_path = artifact / "attempt-ledger.json"
    closure_path = artifact / "execution-closure.json"
    completion_path = artifact / "completion-receipt.json"
    artifact_manifest_path = artifact / "artifact-files.sha256"
    receipt_path = (args.receipt or output_root / "post-run-binding-receipt.json").resolve()

    report = load_object(report_path)
    adjudication = load_object(adjudication_path)
    ledger = load_object(ledger_path)
    closure = load_object(closure_path)
    completion = load_object(completion_path)
    if closure.get("ratification", {}).get("instance") != INSTANCE:
        raise RuntimeError("Execution closure instance mismatch")
    if not report.get("scientific_run_executed") or report.get("exit_code") != 0:
        raise RuntimeError("Execution report does not describe a successful scientific run")

    runtime_listing = listing_path.read_bytes()
    runtime_listing_sha = sha256_bytes(runtime_listing)
    if runtime_listing_sha != report.get("control_dataset_listing_sha256"):
        raise RuntimeError("Runtime listing SHA-256 differs from EXECUTION_REPORT.json")

    versions: list[dict[str, Any]] = []
    matching_versions: list[int] = []
    for version, archive in enumerate_archives(args.dataset_archives_root.resolve()):
        listing, file_count = canonical_zip_listing(archive)
        matches = listing == runtime_listing
        versions.append(
            {
                "archive_sha256": sha256_file(archive),
                "file_count": file_count,
                "listing_bytes": len(listing),
                "listing_sha256": sha256_bytes(listing),
                "runtime_byte_match": matches,
                "version": version,
            }
        )
        if matches:
            matching_versions.append(version)
    if not matching_versions:
        raise RuntimeError("No explicit dataset version matches the runtime listing")

    artifact_entries = parse_artifact_manifest(artifact_manifest_path)
    checkpoint_manifest = write_checkpoint_manifest(artifact, artifact_entries)
    run_matrix = collect_run_matrix(artifact)
    public_manifest = write_public_manifest(output_root)
    kernel = query_kernel()

    configured_dataset = report.get("control_dataset_mount", {}).get("configured_slug")
    if configured_dataset not in kernel["dataset_data_sources"]:
        raise RuntimeError("Configured control dataset is absent from Kaggle kernel metadata")

    output_hashes = {
        "adjudication_sha256": sha256_file(adjudication_path),
        "artifact_manifest_sha256": sha256_file(artifact_manifest_path),
        "attempt_ledger_sha256": sha256_file(ledger_path),
        "checkpoint_manifest_sha256": sha256_file(checkpoint_manifest),
        "completion_receipt_sha256": sha256_file(completion_path),
        "control_dataset_files_listing_sha256": runtime_listing_sha,
        "execution_closure_sha256": sha256_file(closure_path),
        "execution_report_sha256": sha256_file(report_path),
        "public_evidence_manifest_sha256": sha256_file(public_manifest),
    }
    governing = {
        **report["governing"],
        "attempt_policy_sha256": closure["ratification"]["attempt_policy_sha256"],
        "ratification_receipt_sha256": report["ratification_receipt_sha256"],
        "runner_sha256": report["runner_sha256"],
    }
    receipt = {
        "adjudication_summary": {
            "adjudication": adjudication["adjudication"],
            "attempt": ledger["attempt_number"],
            "disposition": ledger["disposition"],
            "primary": adjudication["primary"],
            "relative_rmse_change": adjudication["relative_rmse_change"],
            "sensitivity": adjudication["sensitivity"],
            "trigger_exposure_classification": adjudication["trigger_exposure_classification"],
            "triggers": adjudication["triggers"],
        },
        "closure_step_scientific_run_executed": False,
        "control_dataset_binding": {
            "candidate_versions": versions,
            "configured_slug": configured_dataset,
            "matching_versions": matching_versions,
            "runtime_file_count": len(runtime_listing.splitlines()),
            "runtime_listing_bytes": len(runtime_listing),
            "runtime_listing_sha256": runtime_listing_sha,
        },
        "generated_at_utc": datetime.now(timezone.utc).isoformat(),
        "generator_sha256": sha256_file(Path(__file__).resolve()),
        "governing_hashes": governing,
        "kernel_binding": kernel,
        "output_file_hashes": output_hashes,
        "run_matrix": run_matrix,
        "run_matrix_count": len(run_matrix),
        "scientific_run_executed_in_bound_attempt": True,
        "status": "POST_RUN_BINDING_COMPLETE_GENERATED",
        "study_instance": INSTANCE,
    }
    receipt_path.write_text(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"receipt": str(receipt_path), "receipt_sha256": sha256_file(receipt_path), "matching_versions": matching_versions, "run_matrix_count": len(run_matrix)}, sort_keys=True))


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        raise
