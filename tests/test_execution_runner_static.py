from __future__ import annotations

import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


RUNNER_PATH = (
    Path(__file__).resolve().parents[1]
    / "runners"
    / "kaggle-s2-execution"
    / "execute.py"
)
SPEC = importlib.util.spec_from_file_location("s2_execution_runner", RUNNER_PATH)
assert SPEC is not None and SPEC.loader is not None
RUNNER = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(RUNNER)


class ExecutionRunnerStaticTests(unittest.TestCase):
    def valid_authorization(self) -> dict[str, object]:
        return {
            "schema_version": 1,
            "study_instance": RUNNER.INSTANCE,
            "governing": {
                "preregistration_sha256": RUNNER.EXPECTED_PREREG_SHA256,
                "driver_sha256": RUNNER.EXPECTED_DRIVER_SHA256,
                "split_manifest_sha256": RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256,
                "ratification_receipt_sha256": "a" * 64,
            },
            "kernel": {
                "slug": "volmax1/batteryml-s2-1-execution-run",
                "version": 2,
                "url": "https://www.kaggle.com/code/volmax1/batteryml-s2-1-execution-run",
                "measurement_source": "kaggle_api",
                "measured_at_utc": "2026-09-16T20:00:00+00:00",
            },
            "control_dataset": {
                "slug": RUNNER.CONTROL_DATASET_SLUG,
                "version": 8,
                "listing_sha256": "b" * 64,
                "measurement_source": "kaggle_api",
                "measured_at_utc": "2026-09-16T20:00:00+00:00",
            },
        }

    def test_authorization_accepts_complete_measured_identity(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / RUNNER.AUTHORIZATION_FILENAME
            path.write_text(json.dumps(self.valid_authorization()))
            self.assertEqual(RUNNER.validate_authorization(path)["kernel"]["version"], 2)

    def test_authorization_rejects_unmeasured_kernel_version(self) -> None:
        authorization = self.valid_authorization()
        authorization["kernel"]["version"] = None  # type: ignore[index]
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / RUNNER.AUTHORIZATION_FILENAME
            path.write_text(json.dumps(authorization))
            with self.assertRaisesRegex(RuntimeError, "kernel version"):
                RUNNER.validate_authorization(path)

    def test_listing_is_sorted_and_content_bound(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "z.txt").write_text("z\n")
            (root / "a.txt").write_text("a\n")
            listing, digest = RUNNER.deterministic_listing(root)
            self.assertEqual(
                [line.split("  ", 1)[1] for line in listing.splitlines()],
                ["a.txt", "z.txt"],
            )
            self.assertEqual(len(digest), 64)

    def test_control_mount_is_bound_to_receipt_version_and_listing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            driver = root / "s2_kaggle_driver.py"
            prereg = root / "PREREGISTRATION.md"
            manifest = root / "batteryml-protocol-generalization-split-manifest.csv"
            receipt = root / "ratification-receipt.txt"
            version_receipt = root / RUNNER.CONTROL_VERSION_FILENAME
            driver.write_text("driver\n")
            prereg.write_text("prereg\n")
            manifest.write_text("manifest\n")
            version = {
                "slug": RUNNER.CONTROL_DATASET_SLUG,
                "version": 8,
                "measurement_source": "kaggle_api",
                "measured_at_utc": "2026-09-16T20:00:00+00:00",
            }
            version_receipt.write_text(json.dumps(version, sort_keys=True) + "\n")

            old = (
                RUNNER.EXPECTED_DRIVER_SHA256,
                RUNNER.EXPECTED_PREREG_SHA256,
                RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256,
            )
            try:
                RUNNER.EXPECTED_DRIVER_SHA256 = RUNNER.sha256_file(driver)
                RUNNER.EXPECTED_PREREG_SHA256 = RUNNER.sha256_file(prereg)
                RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256 = RUNNER.sha256_file(manifest)
                receipt.write_text(
                    "status=RATIFIED\n"
                    f"instance={RUNNER.INSTANCE}\n"
                    f"prereg_sha256={RUNNER.EXPECTED_PREREG_SHA256}\n"
                    f"driver_sha256={RUNNER.EXPECTED_DRIVER_SHA256}\n"
                )
                listing, listing_sha = RUNNER.deterministic_listing(root)
                auth = self.valid_authorization()
                auth["governing"]["preregistration_sha256"] = RUNNER.EXPECTED_PREREG_SHA256  # type: ignore[index]
                auth["governing"]["driver_sha256"] = RUNNER.EXPECTED_DRIVER_SHA256  # type: ignore[index]
                auth["governing"]["split_manifest_sha256"] = RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256  # type: ignore[index]
                auth["governing"]["ratification_receipt_sha256"] = RUNNER.sha256_file(receipt)  # type: ignore[index]
                auth["control_dataset"]["listing_sha256"] = listing_sha  # type: ignore[index]
                observed_listing, mount = RUNNER.validate_control_mount(root, receipt, auth)
                self.assertEqual(observed_listing, listing)
                self.assertEqual(mount["version"], 8)
                self.assertEqual(mount["listing_sha256"], listing_sha)
            finally:
                (
                    RUNNER.EXPECTED_DRIVER_SHA256,
                    RUNNER.EXPECTED_PREREG_SHA256,
                    RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256,
                ) = old

    def test_runner_does_not_fabricate_kaggle_environment(self) -> None:
        source = RUNNER_PATH.read_text()
        self.assertNotIn('os.environ["KAGGLE_KERNEL_RUN_TYPE"]', source)
        self.assertNotIn('os.environ["KAGGLE_URL"]', source)
        self.assertNotIn("batteryml-s2-1-execution-run/1", source)


if __name__ == "__main__":
    unittest.main()
