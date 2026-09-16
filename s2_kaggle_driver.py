#!/usr/bin/env python3
"""Fail-closed driver for BatteryML protocol-generalization S2 on Kaggle."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import math
import os
import platform
import shutil
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

import numpy as np


INSTANCE = "batteryml-protocol-generalization-s2.1-kaggle"
INPUT = Path(os.environ.get(
    "S2_INPUT_ROOT",
    "/kaggle/input/datasets/volmax1/batteryml-protocol-generalization-s2-controls",
))
RAW = Path(os.environ.get(
    "S2_RAW_ROOT",
    "/kaggle/input/datasets/rickandjoe/mit-battery-degradation-dataset",
))
WORKING = Path(os.environ.get("S2_WORKING_ROOT", "/kaggle/working"))
REPO = INPUT / "BatteryML"
SPLIT_MANIFEST = INPUT / "batteryml-protocol-generalization-split-manifest.csv"
SOURCE_MANIFEST = INPUT / "batteryml-source-files.sha256"
PREREGISTRATION = INPUT / "PREREGISTRATION.md"
WHEELS = INPUT / "offline-wheels"
PROCESSED = WORKING / "s2-processed-matr"
SITE = WORKING / "s2-site-packages"
ARTIFACT = WORKING / "s2-artifact"
DRIVER = Path(__file__).resolve()

EXPECTED_REPO_SHA = "2861ae3b8c79938c7fc8e6fe9986b799ca71c7dd"
EXPECTED_SOURCE_MANIFEST_SHA = "5e239025955a160586a666b3cd50deb03c0e60e8ccf316fbb111156f197a516e"
EXPECTED_SPLIT_SHA = "96695e534718733469ba108ee3c1372e29351710235d5b47020f6bd9ae2ce722"
EXPECTED_BASE_FREEZE_SHA = "e137b12924bbb4fbb83f45c8ccb3419ba4e5556d01d977a05a7ab4e175155c35"
MIN_RAM_BYTES = 31 * 1024**3
EXACT_CPUS = 4

S1_EXPOSED_METRICS = {
    ("primary83", "variance", "a"): 136.12962341308594,
    ("primary83", "variance", "b"): 133.47593688964844,
    ("primary83", "ridge", "a"): 115.7891820959575,
}
CROSS_ENVIRONMENT_REL_TOLERANCE = 0.010
MAX_SCIENTIFIC_ATTEMPTS = 2

EXPECTED_FILES = {
    RAW / "2017-05-12_batchdata_updated_struct_errorcorrect.mat": "9d928ab978f0e3c70b31cb833a749fedd35094d01af76475d69b40aa3497f5ba",
    RAW / "2017-06-30_batchdata_updated_struct_errorcorrect.mat": "63ab200d09ecb237fee5ef3a5c5db76e3212e3206a0bd92f769e1427fed338b8",
    SPLIT_MANIFEST: EXPECTED_SPLIT_SHA,
    SOURCE_MANIFEST: EXPECTED_SOURCE_MANIFEST_SHA,
    REPO / "configs/baselines/sklearn/variance_model/matr_1.yaml": "ab0849c3a021273629c1a6e90c09aa29eb425fdfb17aef2376888524f6984b5b",
    REPO / "configs/baselines/sklearn/ridge/matr_1.yaml": "ad554e8c459a85278ce125a20c179dd3ed65046d5abeab455a3738d3ca793a54",
    REPO / "configs/baselines/sklearn/xgb/matr_1.yaml": "ce3e35629429b988426d0a0b9da867e7c4411a949715dad61597b5684483a0f7",
    WHEELS / "addict-2.4.0-py3-none-any.whl": "249bb56bbfd3cdc2a004ea0ff4c2b6ddc84d53bc2194761636eb314d5cfa5dfc",
    WHEELS / "fire-0.7.1-py3-none-any.whl": "e43fd8a5033a9001e7e2973bab96070694b9f12f2e0ecf96d4683971b5ab1882",
}
MODELS = {
    "variance": REPO / "configs/baselines/sklearn/variance_model/matr_1.yaml",
    "ridge": REPO / "configs/baselines/sklearn/ridge/matr_1.yaml",
    "xgb": REPO / "configs/baselines/sklearn/xgb/matr_1.yaml",
}
EXPECTED_VERSIONS = {
    "python": "3.12.13",
    "numpy": "2.0.2",
    "pandas": "2.3.3",
    "torch": "2.10.0+cpu",
    "sklearn": "1.6.1",
    "xgboost": "3.2.0",
    "numba": "0.60.0",
    "scipy": "1.16.3",
    "h5py": "3.16.0",
}


def utcnow() -> str:
    return datetime.now(timezone.utc).isoformat()


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def mem_total_bytes() -> int:
    for line in Path("/proc/meminfo").read_text().splitlines():
        if line.startswith("MemTotal:"):
            return int(line.split()[1]) * 1024
    raise RuntimeError("MemTotal missing from /proc/meminfo")


def cgroup_memory_limit_bytes() -> int | None:
    for candidate in (
        Path("/sys/fs/cgroup/memory.max"),
        Path("/sys/fs/cgroup/memory/memory.limit_in_bytes"),
    ):
        if candidate.is_file():
            try:
                text = candidate.read_text().strip()
                if text != "max" and text.isdigit():
                    return int(text)
                elif text == "max":
                    return None
            except Exception:
                pass
    return None


def pip_freeze_sha() -> tuple[int, str]:
    sanitized_env = {k: v for k, v in os.environ.items() if k != "PYTHONPATH"}
    text = subprocess.check_output(
        [sys.executable, "-m", "pip", "freeze"], text=True, env=sanitized_env
    )
    if not text.endswith("\n"):
        text += "\n"
    return len(text.splitlines()), hashlib.sha256(text.encode()).hexdigest()


def verify_environment() -> dict[str, object]:
    import h5py
    import numba
    import pandas
    import scipy
    import sklearn
    import torch
    import xgboost

    observed = {
        "python": platform.python_version(),
        "numpy": np.__version__,
        "pandas": pandas.__version__,
        "torch": torch.__version__,
        "sklearn": sklearn.__version__,
        "xgboost": xgboost.__version__,
        "numba": numba.__version__,
        "scipy": scipy.__version__,
        "h5py": h5py.__version__,
    }
    if observed != EXPECTED_VERSIONS:
        raise RuntimeError(f"environment mismatch: {observed!r}")
    if torch.cuda.is_available():
        raise RuntimeError("CPU-only environment required; CUDA is available")
    memory = mem_total_bytes()
    cpus = os.cpu_count() or 0
    if memory < MIN_RAM_BYTES:
        raise RuntimeError(f"RAM below frozen minimum: {memory}")
    if cpus != EXACT_CPUS:
        raise RuntimeError(
            f"exact CPU logical cores required: {EXACT_CPUS}, observed: {cpus}"
        )
    cgroup_limit = cgroup_memory_limit_bytes()
    xgb_params = (
        xgboost.XGBRegressor().get_params(deep=True)
        if hasattr(xgboost, "XGBRegressor")
        else {}
    )
    freeze_lines, freeze_sha = pip_freeze_sha()
    if (freeze_lines, freeze_sha) != (872, EXPECTED_BASE_FREEZE_SHA):
        raise RuntimeError(
            f"base pip freeze mismatch: lines={freeze_lines}, sha256={freeze_sha}"
        )
    return {
        "versions": observed,
        "cuda_available": False,
        "ram_total_bytes": memory,
        "cgroup_memory_limit_bytes": cgroup_limit,
        "logical_cpus": cpus,
        "exact_cpu_admission_pass": True,
        "xgboost_resolved_parameters": xgb_params,
        "base_pip_freeze_lines": freeze_lines,
        "base_pip_freeze_sha256": freeze_sha,
    }


def verify_source_snapshot() -> dict[str, object]:
    expected: list[tuple[str, str]] = []
    for line in SOURCE_MANIFEST.read_text().splitlines():
        digest, name = line.split("  ", 1)
        expected.append((name, digest))
    actual_names = sorted(
        str(path.relative_to(REPO)) for path in REPO.rglob("*") if path.is_file()
    )
    expected_names = [name for name, _ in expected]
    if actual_names != expected_names:
        raise RuntimeError("BatteryML source snapshot membership mismatch")
    for name, digest in expected:
        actual = sha256(REPO / name)
        if actual != digest:
            raise RuntimeError(f"BatteryML source mismatch: {name}: {actual}")
    return {
        "commit": EXPECTED_REPO_SHA,
        "tracked_file_count": len(expected),
        "source_manifest_sha256": sha256(SOURCE_MANIFEST),
    }


def verify_inputs() -> dict[str, object]:
    hashes: dict[str, str] = {}
    for path, expected in EXPECTED_FILES.items():
        if not path.is_file():
            raise FileNotFoundError(path)
        actual = sha256(path)
        if actual != expected:
            raise RuntimeError(f"SHA-256 mismatch for {path}: {actual}")
        try:
            label = str(path.relative_to(INPUT))
        except ValueError:
            label = f"public-raw/{path.name}"
        hashes[label] = actual
    return {"hashes": hashes, "source": verify_source_snapshot()}


def read_receipt(path: Path) -> dict[str, str]:
    if not path.is_file():
        raise RuntimeError("ratification receipt is missing")
    values: dict[str, str] = {}
    for line in path.read_text().splitlines():
        if "=" in line:
            key, value = line.split("=", 1)
            values[key.strip()] = value.strip()
    required = {
        "status", "instance", "prereg_sha256", "driver_sha256",
        "operator", "ratified_at", "operator_verbatim_statement",
        "operator_statement_location",
    }
    if not required.issubset(values):
        raise RuntimeError("ratification receipt fields are incomplete")
    if values["status"] != "RATIFIED" or values["instance"] != INSTANCE:
        raise RuntimeError("ratification receipt does not authorize S2")
    if not values.get("operator_verbatim_statement", "").strip():
        raise RuntimeError("ratification receipt missing operator verbatim statement")
    if not values.get("operator_statement_location", "").strip():
        raise RuntimeError("ratification receipt missing operator statement location")
    if sha256(PREREGISTRATION) != values["prereg_sha256"]:
        raise RuntimeError("preregistration hash mismatch")
    if sha256(DRIVER) != values["driver_sha256"]:
        raise RuntimeError("driver hash mismatch")
    return values


def manifest_ids(universe: str, split: str) -> tuple[list[str], list[str]]:
    with SPLIT_MANIFEST.open(newline="") as handle:
        rows = [row for row in csv.DictReader(handle) if row["universe"] == universe]
    side_key, position_key = f"{split}_split", f"{split}_position"
    train = sorted(
        (row for row in rows if row[side_key] == "train"),
        key=lambda row: int(row[position_key]),
    )
    test = sorted(
        (row for row in rows if row[side_key] == "test"),
        key=lambda row: int(row[position_key]),
    )
    expected = (41, 42) if universe == "primary83" else (41, 43)
    if (len(train), len(test)) != expected:
        raise RuntimeError("split-manifest count mismatch")
    if split == "b":
        train_groups = {row["protocol_sha256"] for row in train}
        test_groups = {row["protocol_sha256"] for row in test}
        if train_groups & test_groups:
            raise RuntimeError("protocol overlap in frozen B split")
    return [row["cell_id"] for row in train], [row["cell_id"] for row in test]


def protocol_hashes(universe: str) -> dict[str, str]:
    with SPLIT_MANIFEST.open(newline="") as handle:
        return {
            row["cell_id"]: row["protocol_sha256"]
            for row in csv.DictReader(handle)
            if row["universe"] == universe
        }


def install_extras() -> dict[str, str]:
    if SITE.exists():
        raise RuntimeError(f"refusing existing site target: {SITE}")
    subprocess.run(
        [
            sys.executable, "-m", "pip", "install", "--no-index",
            "--no-deps", "--target", str(SITE),
            str(WHEELS / "addict-2.4.0-py3-none-any.whl"),
            str(WHEELS / "fire-0.7.1-py3-none-any.whl"),
        ],
        check=True,
    )
    sys.path.insert(0, str(SITE))
    import addict
    import fire
    versions = {
        "addict": str(getattr(addict, "__version__", "2.4.0")),
        "fire": str(getattr(fire, "__version__", "0.7.1")),
    }
    if versions != {"addict": "2.4.0", "fire": "0.7.1"}:
        raise RuntimeError(f"offline-extra mismatch: {versions!r}")
    return versions


def activate_extras() -> None:
    if not SITE.is_dir():
        raise RuntimeError("offline extras target is missing")
    sys.path.insert(0, str(SITE))
    import addict
    import fire
    if str(getattr(addict, "__version__", "2.4.0")) != "2.4.0":
        raise RuntimeError("addict version mismatch")
    if str(getattr(fire, "__version__", "0.7.1")) != "0.7.1":
        raise RuntimeError("fire version mismatch")
    site_resolved = SITE.resolve()
    for mod, name in ((addict, "addict"), (fire, "fire")):
        mod_file = getattr(mod, "__file__", None)
        if not mod_file:
            raise RuntimeError(f"{name} missing __file__ attribute")
        mod_path = Path(mod_file).resolve()
        if not mod_path.is_relative_to(site_resolved):
            raise RuntimeError(
                f"{name} provenance violation: loaded from {mod_path}, expected within {site_resolved}"
            )


def processed_rows() -> list[tuple[str, str]]:
    files = sorted(PROCESSED.glob("MATR_*.pkl"))
    if len(files) != 89:
        raise RuntimeError(f"expected 89 processed cells, found {len(files)}")
    return [(path.name, sha256(path)) for path in files]


def verify_processed() -> str:
    manifest = PROCESSED / "processed-files.sha256"
    expected = []
    for line in manifest.read_text().splitlines():
        digest, name = line.split("  ", 1)
        expected.append((name, digest))
    if processed_rows() != expected:
        raise RuntimeError("processed-file manifest mismatch")
    return sha256(manifest)


def command_verify(_: argparse.Namespace) -> None:
    receipt = {
        "timestamp_utc": utcnow(),
        "status": "PASS",
        "scientific_run_executed": False,
        "environment": verify_environment(),
        "inputs": verify_inputs(),
        "manifest_counts": {
            f"{universe}_{split}": [len(x) for x in manifest_ids(universe, split)]
            for universe in ("primary83", "sensitivity84")
            for split in ("a", "b")
        },
    }
    print(json.dumps(receipt, indent=2, sort_keys=True))


def command_preprocess(args: argparse.Namespace) -> None:
    ratification = read_receipt(args.ratification_receipt)
    environment = verify_environment()
    inputs = verify_inputs()
    activate_extras()
    if PROCESSED.exists():
        raise RuntimeError(f"refusing existing preprocessing directory: {PROCESSED}")
    PROCESSED.mkdir(parents=True, exist_ok=False)
    sys.path.insert(0, str(REPO))
    from batteryml.preprocess.base import BasePreprocessor
    from batteryml.preprocess.preprocess_MATR import clean_batches, load_batch

    preprocessor = BasePreprocessor(output_dir=str(PROCESSED), silent=True)
    batches = [
        load_batch(RAW / "2017-05-12_batchdata_updated_struct_errorcorrect.mat", 1),
        load_batch(RAW / "2017-06-30_batchdata_updated_struct_errorcorrect.mat", 2),
    ]
    clean_batches(batches, preprocessor.dump_single_file, True)
    rows = processed_rows()
    manifest = PROCESSED / "processed-files.sha256"
    manifest.write_text("".join(f"{digest}  {name}\n" for name, digest in rows))
    receipt = {
        "timestamp_utc": utcnow(),
        "ratification": ratification,
        "environment": environment,
        "inputs": inputs,
        "processed_file_count": len(rows),
        "processed_manifest_sha256": sha256(manifest),
    }
    (PROCESSED / "preprocess-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


def clean_cell_id(value: str) -> str:
    return value.removeprefix("MATR_")


def command_run(args: argparse.Namespace) -> None:
    ratification = read_receipt(args.ratification_receipt)
    environment = verify_environment()
    inputs = verify_inputs()
    activate_extras()
    processed_sha = verify_processed()
    train_ids, test_ids = manifest_ids(args.universe, args.split)
    groups = protocol_hashes(args.universe)
    output = ARTIFACT / "results" / args.universe / args.split / args.model
    if output.exists():
        raise RuntimeError(f"refusing existing run namespace: {output}")
    output.mkdir(parents=True, exist_ok=False)

    os.chdir(REPO)
    sys.path.insert(0, str(REPO))
    from batteryml.builders import MODELS as MODEL_REGISTRY
    from batteryml.pipeline import load_config, set_seed
    from batteryml.task import Task
    from batteryml.train_test_split.MATR_split import MATRTrainTestSplitter

    splitter = MATRTrainTestSplitter(str(PROCESSED), train_ids, test_ids)
    path_train = [path.stem.split("_", 1)[1] for path in splitter.train_cells]
    path_test = [path.stem.split("_", 1)[1] for path in splitter.test_cells]
    if path_train != train_ids or path_test != test_ids:
        raise RuntimeError("splitter membership/order mismatch")

    config = load_config(str(MODELS[args.model]), str(output))
    task = Task(
        train_test_splitter=splitter,
        feature_extractor=config["feature"],
        label_annotator=config["label"],
        feature_transformation=config["feature_transformation"],
        label_transformation=config["label_transformation"],
    )
    dataset = task.build().to("cpu")
    loaded_train = [clean_cell_id(cell.cell_id) for cell in task.train_cells]
    loaded_test = [clean_cell_id(cell.cell_id) for cell in task.test_cells]
    if loaded_train != train_ids or loaded_test != test_ids:
        raise RuntimeError("loaded membership/order mismatch before fit")
    if len(dataset.train_data) != len(train_ids) or len(dataset.test_data) != len(test_ids):
        raise RuntimeError("label filtering changed frozen membership")

    set_seed(0)
    model = MODEL_REGISTRY.build(config["model"])
    model.workspace = output
    resolved = model.model.get_params(deep=True) if hasattr(model, "model") else {}
    (output / "resolved-model-parameters.json").write_text(
        json.dumps(resolved, indent=2, sort_keys=True, default=str) + "\n"
    )
    model.fit(dataset, timestamp="frozen")
    prediction = model.predict(dataset)
    target = dataset.test_data.label
    if dataset.label_transformation is not None:
        target = dataset.label_transformation.inverse_transform(target)
        prediction = dataset.label_transformation.inverse_transform(prediction)
    target_values = target.detach().cpu().numpy().reshape(-1)
    prediction_values = prediction.detach().cpu().numpy().reshape(-1)
    rmse = float(np.sqrt(np.mean((target_values - prediction_values) ** 2)))
    mae = float(np.mean(np.abs(target_values - prediction_values)))

    with (output / "per-cell-predictions.csv").open("w", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "universe", "split", "model", "cell_id",
                "protocol_sha256", "target", "prediction",
            ],
        )
        writer.writeheader()
        for cell, observed, predicted in zip(test_ids, target_values, prediction_values):
            writer.writerow({
                "universe": args.universe,
                "split": args.split,
                "model": args.model,
                "cell_id": cell,
                "protocol_sha256": groups[cell],
                "target": repr(float(observed)),
                "prediction": repr(float(predicted)),
            })

    receipt = {
        "timestamp_utc": utcnow(),
        "ratification": ratification,
        "environment": environment,
        "inputs": inputs,
        "processed_manifest_sha256": processed_sha,
        "universe": args.universe,
        "split": args.split,
        "model": args.model,
        "seed": 0,
        "train_cell_ids": loaded_train,
        "test_cell_ids": loaded_test,
        "rmse": rmse,
        "mae": mae,
    }
    (output / "run-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


def run_child(arguments: list[str], label: str, receipt: Path) -> None:
    logs = ARTIFACT / "execution-logs"
    logs.mkdir(parents=True, exist_ok=True)
    command = [sys.executable, str(DRIVER), *arguments]
    start = utcnow()
    environment = os.environ.copy()
    environment["PYTHONPATH"] = str(SITE)
    environment["PYTHONDONTWRITEBYTECODE"] = "1"
    completed = subprocess.run(command, text=True, capture_output=True, env=environment)
    end = utcnow()
    (logs / f"{label}.command.txt").write_text(" ".join(command) + "\n")
    (logs / f"{label}.stdout.log").write_text(completed.stdout)
    (logs / f"{label}.stderr.log").write_text(completed.stderr)
    (logs / f"{label}.execution.json").write_text(json.dumps({
        "start_utc": start,
        "end_utc": end,
        "exit_code": completed.returncode,
        "command": command,
    }, indent=2, sort_keys=True) + "\n")
    if completed.returncode != 0:
        raise RuntimeError(f"child failed: {label}: exit {completed.returncode}")
    if not receipt.is_file():
        raise RuntimeError(f"child receipt missing: {receipt}")


def adjudicate() -> dict[str, object]:
    primary: dict[str, dict[str, dict[str, float]]] = {}
    sensitivity: dict[str, dict[str, dict[str, float]]] = {}
    for universe, target in (("primary83", primary), ("sensitivity84", sensitivity)):
        for model in ("variance", "ridge", "xgb"):
            target[model] = {}
            for split in ("a", "b"):
                path = ARTIFACT / "results" / universe / split / model / "run-receipt.json"
                data = json.loads(path.read_text())
                target[model][split] = {"rmse": data["rmse"], "mae": data["mae"]}

    divergences = {}
    diverged = False
    for (u, m, s), s1_val in S1_EXPOSED_METRICS.items():
        s2_val = primary[m][s]["rmse"]
        rel_diff = abs(s2_val - s1_val) / s1_val
        within_tol = (rel_diff <= CROSS_ENVIRONMENT_REL_TOLERANCE)
        divergences[f"{u}_{m}_{s}"] = {
            "s1_rmse": s1_val,
            "s2_rmse": s2_val,
            "relative_diff": rel_diff,
            "within_tolerance": within_tol,
        }
        if not within_tol:
            diverged = True

    if diverged:
        return {
            "timestamp_utc": utcnow(),
            "status": "DEFERRED_ENVIRONMENT_DIVERGENCE",
            "adjudication": "DEFERRED_ENVIRONMENT_DIVERGENCE",
            "primary": primary,
            "sensitivity": sensitivity,
            "s1_divergences": divergences,
            "cross_environment_relative_tolerance": CROSS_ENVIRONMENT_REL_TOLERANCE,
            "message": (
                "One or more exposed S1 metrics deviated by >1.0% relative in S2; "
                "scientific gate triggers not adjudicated."
            ),
            "automatic_neural_continuation": False,
        }

    relative = {
        model: (scores["b"]["rmse"] - scores["a"]["rmse"]) / scores["a"]["rmse"]
        for model, scores in primary.items()
    }
    order_a = sorted(primary, key=lambda model: primary[model]["a"]["rmse"])
    order_b = sorted(primary, key=lambda model: primary[model]["b"]["rmse"])
    triggers = {
        "any_relative_rmse_change_ge_10_percent": any(value >= 0.10 for value in relative.values()),
        "rmse_model_order_changed": order_a != order_b,
        "all_three_strictly_worse_under_b": all(
            scores["b"]["rmse"] > scores["a"]["rmse"] for scores in primary.values()
        ),
    }
    trigger_exposure_classification = {
        "any_relative_rmse_change_ge_10_percent": "partially_exposed_decision_weight_on_unverified_models",
        "rmse_model_order_changed": "partially_exposed_decision_weight_on_unverified_models",
        "all_three_strictly_worse_under_b": "pre_exposed_no_independent_confirmatory_weight",
    }
    signal = any(triggers.values())
    return {
        "timestamp_utc": utcnow(),
        "status": "ADJUDICATED",
        "primary": primary,
        "sensitivity": sensitivity,
        "relative_rmse_change": relative,
        "rmse_order_a_best_to_worst": order_a,
        "rmse_order_b_best_to_worst": order_b,
        "s1_divergences": divergences,
        "cross_environment_relative_tolerance": CROSS_ENVIRONMENT_REL_TOLERANCE,
        "triggers": triggers,
        "trigger_exposure_classification": trigger_exposure_classification,
        "trigger_3_status": "pre-exposed / no independent confirmatory weight (Variance B < Variance A in S1)",
        "adjudication": "SIGNAL_POSITIVE_MODEL_GATE" if signal else "STOP_NO_MATERIAL_SIGNAL",
        "automatic_neural_continuation": False,
    }


def artifact_manifest() -> str:
    path = ARTIFACT / "artifact-files.sha256"
    files = sorted(item for item in ARTIFACT.rglob("*") if item.is_file() and item != path)
    path.write_text("".join(
        f"{sha256(item)}  {item.relative_to(ARTIFACT)}\n" for item in files
    ))
    return sha256(path)


def command_execute_all(args: argparse.Namespace) -> None:
    attempt = getattr(args, "attempt", 1)
    if attempt not in (1, 2):
        raise ValueError(f"attempt must be 1 or 2, got {attempt}")
    kernel_id = getattr(args, "kernel_id", "").strip()
    if not kernel_id:
        raise ValueError("--kernel-id (slug, version, and URL) is required for execute-all")
    ratification = read_receipt(args.ratification_receipt)
    environment = verify_environment()
    inputs = verify_inputs()
    if ARTIFACT.exists() or PROCESSED.exists() or SITE.exists():
        raise RuntimeError("refusing pre-existing S2 execution namespace")
    ARTIFACT.mkdir(parents=True, exist_ok=False)

    start_time = utcnow()
    ledger_entry: dict[str, object] = {
        "attempt_number": attempt,
        "kaggle_kernel_run_id_or_url": kernel_id,
        "start_utc": start_time,
        "end_utc": None,
        "governing_prereg_sha256": sha256(PREREGISTRATION),
        "governing_driver_sha256": sha256(DRIVER),
        "exit_code": None,
        "disposition": None,
        "generated_receipts": [],
    }
    (ARTIFACT / "attempt-ledger.json").write_text(
        json.dumps(ledger_entry, indent=2, sort_keys=True) + "\n"
    )

    extras = install_extras()
    closure = {
        "timestamp_utc": utcnow(),
        "attempt": attempt,
        "ratification": ratification,
        "environment": environment,
        "inputs": inputs,
        "offline_extras": extras,
        "driver_sha256": sha256(DRIVER),
        "preregistration_sha256": sha256(PREREGISTRATION),
    }
    (ARTIFACT / "execution-closure.json").write_text(
        json.dumps(closure, indent=2, sort_keys=True) + "\n"
    )

    receipt_arg = str(args.ratification_receipt)
    try:
        run_child(
            ["preprocess-one", "--ratification-receipt", receipt_arg],
            "00-preprocess",
            PROCESSED / "preprocess-receipt.json",
        )
        counter = 1
        for universe in ("primary83", "sensitivity84"):
            for model in ("variance", "ridge", "xgb"):
                for split in ("a", "b"):
                    label = f"{counter:02d}-{universe}-{model}-{split}"
                    receipt = ARTIFACT / "results" / universe / split / model / "run-receipt.json"
                    run_child([
                        "run-one", "--ratification-receipt", receipt_arg,
                        "--universe", universe, "--split", split, "--model", model,
                    ], label, receipt)
                    counter += 1

        decision = adjudicate()
        (ARTIFACT / "adjudication.json").write_text(
            json.dumps(decision, indent=2, sort_keys=True) + "\n"
        )
        manifest_sha = artifact_manifest()
        summary = {
            "timestamp_utc": utcnow(),
            "attempt": attempt,
            "status": "COMPLETE",
            "instance": INSTANCE,
            "adjudication": decision["adjudication"],
            "artifact_manifest_sha256": manifest_sha,
        }
        (ARTIFACT / "completion-receipt.json").write_text(
            json.dumps(summary, indent=2, sort_keys=True) + "\n"
        )
        ledger_entry["end_utc"] = utcnow()
        ledger_entry["exit_code"] = 0
        ledger_entry["disposition"] = "GOVERNING_COMPLETE"
        ledger_entry["generated_receipts"] = [
            "execution-closure.json",
            "adjudication.json",
            "completion-receipt.json",
            "artifact-files.sha256",
        ]
        (ARTIFACT / "attempt-ledger.json").write_text(
            json.dumps(ledger_entry, indent=2, sort_keys=True) + "\n"
        )
        print(json.dumps(summary, indent=2, sort_keys=True))
    except Exception as exc:
        ledger_entry["end_utc"] = utcnow()
        ledger_entry["exit_code"] = 1
        ledger_entry["disposition"] = (
            "FAILED_PENDING_OPERATOR_CLASSIFICATION"
            if attempt == 1
            else "EXECUTION_BLOCKED_RESOURCE"
        )
        (ARTIFACT / "attempt-ledger.json").write_text(
            json.dumps(ledger_entry, indent=2, sort_keys=True) + "\n"
        )
        raise exc


def command_verify_determinism(_: argparse.Namespace) -> None:
    """Verify byte-identical recreation on a synthetic fixture without touching raw data."""
    sys.path.insert(0, str(REPO))
    from batteryml.data.battery_data import BatteryData, CycleData
    from batteryml.builders import MODELS as MODEL_BUILDERS
    from batteryml.train_test_split.base import BaseTrainTestSplitter
    from batteryml.task import Task
    from batteryml.pipeline import set_seed

    def run_pass(output_dir: Path) -> dict[str, dict[str, object]]:
        tmp_data = output_dir / "data"
        tmp_data.mkdir(parents=True, exist_ok=True)
        train_paths, test_paths = [], []
        cells_spec = [
            ("synth_1", 800.0, 0.01, True),
            ("synth_2", 900.0, 0.02, True),
            ("synth_3", 750.0, -0.01, False),
            ("synth_4", 850.0, -0.02, False),
        ]
        for cid, life, noise, is_tr in cells_spec:
            cycles = []
            for c in range(105):
                q = np.linspace(1.1 - 0.001 * c + noise, 0.1, 1000)
                cd = CycleData(
                    cycle_number=c,
                    Qdlin=q.tolist(),
                    discharge_capacity_in_Ah=[float(q[0])],
                )
                cycles.append(cd)
            b = BatteryData(
                cell_id=cid,
                cycle_data=cycles,
                nominal_capacity_in_Ah=1.1,
                max_cycle=life,
            )
            p = tmp_data / f"{cid}.pkl"
            b.dump(p)
            if is_tr:
                train_paths.append(p)
            else:
                test_paths.append(p)

        class Splitter(BaseTrainTestSplitter):
            def __init__(self):
                super().__init__(str(tmp_data))
                self.train_cells = train_paths
                self.test_cells = test_paths

            def split(self):
                return self.train_cells, self.test_cells

        splitter = Splitter()
        model_configs = [
            (
                "variance",
                "LinearRegressionRULPredictor",
                {
                    "name": "VarianceModelFeatureExtractor",
                    "interp_dims": 1000,
                    "critical_cycles": [2, 9, 99],
                    "use_precalculated_qdlin": True,
                },
            ),
            (
                "ridge",
                "RidgeRULPredictor",
                {
                    "name": "VoltageCapacityMatrixFeatureExtractor",
                    "diff_base": 8,
                    "max_cycle_index": 98,
                    "cycles_to_keep": 98,
                    "use_precalculated_qdlin": True,
                },
            ),
            (
                "xgb",
                "XGBoostRULPredictor",
                {
                    "name": "VoltageCapacityMatrixFeatureExtractor",
                    "diff_base": 8,
                    "max_cycle_index": 98,
                    "cycles_to_keep": 98,
                    "use_precalculated_qdlin": True,
                },
            ),
        ]
        results = {}
        for short_name, mname, f_conf in model_configs:
            task = Task(
                train_test_splitter=splitter,
                feature_extractor=f_conf,
                label_annotator={"name": "RULLabelAnnotator"},
                feature_transformation={"name": "ZScoreDataTransformation"},
                label_transformation={
                    "name": "SequentialDataTransformation",
                    "transformations": [
                        {"name": "LogScaleDataTransformation"},
                        {"name": "ZScoreDataTransformation"},
                    ],
                },
            )
            dataset = task.build().to("cpu")
            set_seed(0)
            model = MODEL_BUILDERS.build({"name": mname})
            m_workspace = output_dir / short_name
            m_workspace.mkdir(parents=True, exist_ok=True)
            model.workspace = m_workspace
            model.fit(dataset, timestamp="frozen")
            pred = model.predict(dataset)
            target = dataset.test_data.label
            if dataset.label_transformation is not None:
                pred = dataset.label_transformation.inverse_transform(pred)
                target = dataset.label_transformation.inverse_transform(target)
            target_vals = target.detach().cpu().numpy().reshape(-1)
            pred_vals = pred.detach().cpu().numpy().reshape(-1)
            rmse = float(np.sqrt(np.mean((target_vals - pred_vals) ** 2)))
            mae = float(np.mean(np.abs(target_vals - pred_vals)))

            preds_path = output_dir / f"{short_name}_predictions.csv"
            with open(preds_path, "w", newline="") as h:
                w = csv.writer(h)
                w.writerow(["cell_id", "target", "prediction"])
                for cid, obs, pr in zip(["synth_3", "synth_4"], target_vals, pred_vals):
                    w.writerow([cid, repr(float(obs)), repr(float(pr))])

            metrics_path = output_dir / f"{short_name}_metrics.json"
            with open(metrics_path, "w") as h:
                json.dump({"rmse": rmse, "mae": mae}, h, indent=2, sort_keys=True)

            results[short_name] = {
                "predictions_sha256": hashlib.sha256(preds_path.read_bytes()).hexdigest(),
                "metrics_sha256": hashlib.sha256(metrics_path.read_bytes()).hexdigest(),
                "metrics": {"rmse": rmse, "mae": mae},
            }
        return results

    base_tmp = Path(tempfile.mkdtemp())
    try:
        res1 = run_pass(base_tmp / "pass1")
        res2 = run_pass(base_tmp / "pass2")
        match = (res1 == res2)
        receipt = {
            "timestamp_utc": utcnow(),
            "status": "PASS" if match else "FAIL",
            "rule": "rename_rerun_byte_identical",
            "scope": {
                "fixture_type": "synthetic_non_matr_cells",
                "models_verified": ["variance", "ridge", "xgb"],
                "comparison": ["per-cell-predictions.csv", "metrics.json"],
                "timestamps_excluded": True,
                "host_metadata_excluded": True,
            },
            "pass1_hashes": {
                k: {
                    "predictions_sha256": v["predictions_sha256"],
                    "metrics_sha256": v["metrics_sha256"],
                }
                for k, v in res1.items()
            },
            "pass2_hashes": {
                k: {
                    "predictions_sha256": v["predictions_sha256"],
                    "metrics_sha256": v["metrics_sha256"],
                }
                for k, v in res2.items()
            },
            "byte_identical_match": match,
            "canonical_metrics": {k: v["metrics"] for k, v in res1.items()},
        }
        print(json.dumps(receipt, indent=2, sort_keys=True))
    finally:
        shutil.rmtree(base_tmp)


def command_smoke_test_child(args: argparse.Namespace) -> None:
    """Parent smoke test verifying parent->child invocation passes environment admission under PYTHONPATH=SITE."""
    environment = verify_environment()
    inputs = verify_inputs()
    if ARTIFACT.exists() or SITE.exists():
        raise RuntimeError("refusing pre-existing smoke test namespace")
    ARTIFACT.mkdir(parents=True, exist_ok=False)
    extras = install_extras()
    receipt_path = ARTIFACT / "smoke-test-child-receipt.json"
    run_child(
        ["smoke-test-child-worker"],
        "smoke-test-child",
        receipt_path,
    )
    result = {
        "timestamp_utc": utcnow(),
        "status": "PASS",
        "scope": "parent_to_child_environment_admission",
        "governing_driver_sha256": sha256(DRIVER),
        "parent_environment": environment,
        "parent_inputs": inputs,
        "offline_extras": extras,
        "child_receipt": json.loads(receipt_path.read_text()),
    }
    (ARTIFACT / "smoke-test-parent-receipt.json").write_text(
        json.dumps(result, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(result, indent=2, sort_keys=True))


def command_smoke_test_child_worker(_: argparse.Namespace) -> None:
    """Child worker for smoke test: verifies environment and activates extras under child PYTHONPATH."""
    environment = verify_environment()
    activate_extras()
    receipt = {
        "timestamp_utc": utcnow(),
        "status": "PASS",
        "child_pid": os.getpid(),
        "pythonpath": os.environ.get("PYTHONPATH", ""),
        "environment": environment,
    }
    (ARTIFACT / "smoke-test-child-receipt.json").write_text(
        json.dumps(receipt, indent=2, sort_keys=True) + "\n"
    )
    print(json.dumps(receipt, indent=2, sort_keys=True))


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="command", required=True)
    verify = subparsers.add_parser("verify")
    verify.set_defaults(func=command_verify)
    preprocess = subparsers.add_parser("preprocess-one")
    preprocess.add_argument("--ratification-receipt", type=Path, required=True)
    preprocess.set_defaults(func=command_preprocess)
    run = subparsers.add_parser("run-one")
    run.add_argument("--ratification-receipt", type=Path, required=True)
    run.add_argument("--universe", choices=["primary83", "sensitivity84"], required=True)
    run.add_argument("--split", choices=["a", "b"], required=True)
    run.add_argument("--model", choices=sorted(MODELS), required=True)
    run.set_defaults(func=command_run)
    execute = subparsers.add_parser("execute-all")
    execute.add_argument("--ratification-receipt", type=Path, required=True)
    execute.add_argument("--attempt", type=int, choices=[1, 2], default=1)
    execute.add_argument(
        "--kernel-id",
        type=str,
        required=True,
        help="Explicit Kaggle kernel slug, version, and URL (e.g. volmax1/batteryml-s2-1-execution/1)",
    )
    execute.set_defaults(func=command_execute_all)
    det = subparsers.add_parser("verify-determinism")
    det.set_defaults(func=command_verify_determinism)
    smoke = subparsers.add_parser("smoke-test-child")
    smoke.set_defaults(func=command_smoke_test_child)
    worker = subparsers.add_parser("smoke-test-child-worker")
    worker.set_defaults(func=command_smoke_test_child_worker)
    return parser.parse_args()


if __name__ == "__main__":
    parsed = parse_args()
    parsed.func(parsed)

