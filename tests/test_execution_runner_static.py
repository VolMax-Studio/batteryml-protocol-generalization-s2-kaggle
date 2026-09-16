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

    def test_listing_rejects_symlinks(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "file.txt").write_text("content\n")
            (root / "link.txt").symlink_to(root / "file.txt")
            with self.assertRaisesRegex(RuntimeError, "Symlink"):
                RUNNER.deterministic_listing(root)

    def test_control_mount_binds_governing_files_and_receipt(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            driver = root / "s2_kaggle_driver.py"
            prereg = root / "PREREGISTRATION.md"
            manifest = root / "batteryml-protocol-generalization-split-manifest.csv"
            receipt = root / "ratification-receipt.txt"
            driver.write_text("driver\n")
            prereg.write_text("prereg\n")
            manifest.write_text("manifest\n")

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
                    "operator=Ivan Nestorov\n"
                    "ratified_at=2026-09-16T22:00:00+02:00\n"
                    "operator_verbatim_statement=Ratified for test.\n"
                    "operator_statement_location=test-fixture\n"
                )
                expected_listing, expected_sha = RUNNER.deterministic_listing(root)
                observed_listing, mount = RUNNER.validate_control_mount(root, receipt)
                self.assertEqual(observed_listing, expected_listing)
                self.assertEqual(mount["version"], None)
                self.assertEqual(
                    mount["version_binding_status"],
                    "POST_RUN_API_BINDING_PENDING",
                )
                self.assertEqual(mount["listing_sha256"], expected_sha)
            finally:
                (
                    RUNNER.EXPECTED_DRIVER_SHA256,
                    RUNNER.EXPECTED_PREREG_SHA256,
                    RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256,
                ) = old

    def test_control_mount_rejects_incomplete_ratification(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for name in (
                "s2_kaggle_driver.py",
                "PREREGISTRATION.md",
                "batteryml-protocol-generalization-split-manifest.csv",
            ):
                (root / name).write_text(name + "\n")
            receipt = root / "ratification-receipt.txt"
            receipt.write_text("status=RATIFIED\n")
            old = (
                RUNNER.EXPECTED_DRIVER_SHA256,
                RUNNER.EXPECTED_PREREG_SHA256,
                RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256,
            )
            try:
                RUNNER.EXPECTED_DRIVER_SHA256 = RUNNER.sha256_file(root / "s2_kaggle_driver.py")
                RUNNER.EXPECTED_PREREG_SHA256 = RUNNER.sha256_file(root / "PREREGISTRATION.md")
                RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256 = RUNNER.sha256_file(
                    root / "batteryml-protocol-generalization-split-manifest.csv"
                )
                with self.assertRaisesRegex(RuntimeError, "receipt instance"):
                    RUNNER.validate_control_mount(root, receipt)
            finally:
                (
                    RUNNER.EXPECTED_DRIVER_SHA256,
                    RUNNER.EXPECTED_PREREG_SHA256,
                    RUNNER.EXPECTED_SPLIT_MANIFEST_SHA256,
                ) = old

    def test_runner_has_no_precreated_sidecar_dependency_or_fake_identity(self) -> None:
        source = RUNNER_PATH.read_text()
        self.assertNotIn("execution-authorization.json", source)
        self.assertNotIn("control-dataset-version.json", source)
        self.assertNotIn("Path(__file__).resolve().with_name", source)
        self.assertNotIn('os.environ["KAGGLE_KERNEL_RUN_TYPE"]', source)
        self.assertNotIn('os.environ["KAGGLE_URL"]', source)
        self.assertNotIn("batteryml-s2-1-execution-run/1", source)
        self.assertIn("POST_RUN_API_BINDING_PENDING", RUNNER.KERNEL_ID_PENDING)

    def test_post_run_binding_feasibility_receipt_is_non_scientific(self) -> None:
        path = Path(__file__).resolve().parents[1] / "post-run-binding-feasibility-receipt.json"
        receipt = json.loads(path.read_text())
        self.assertEqual(receipt["status"], "PASS_CONTENT_BINDING_FEASIBLE")
        self.assertFalse(receipt["scientific_run_executed"])
        self.assertEqual(receipt["explicit_version_download"]["exit_code"], 0)
        self.assertEqual(receipt["explicit_version_download"]["canonical_listing_file_count"], 223)
        self.assertEqual(len(receipt["explicit_version_download"]["canonical_listing_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
