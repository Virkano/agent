import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.m11_security_scan import CHECKLIST, ROOT, checklist_summary, digest, scan_frontend, scan_image


class SecurityScanStructureTests(unittest.TestCase):
    def test_three_sync_has_all_phases_and_real_evidence(self):
        summary = checklist_summary()
        self.assertEqual(sum(summary["counts"].values()), 8)
        self.assertFalse(summary["all_done"])
        self.assertGreater(summary["counts"]["PENDING"], 0)

    def test_unselected_image_is_not_reported_clean(self):
        self.assertEqual(scan_image(ROOT / "output" / "m11-04", None)["state"], "NOT_RUN")

    def test_checklist_digest_is_stable(self):
        self.assertEqual(digest(CHECKLIST), digest(CHECKLIST))
        self.assertEqual(len(digest(CHECKLIST)), 64)

    def test_frontend_findings_are_not_marked_clean(self):
        audit = '{"metadata":{"vulnerabilities":{"high":2,"low":1,"total":3}}}'
        command = subprocess.CompletedProcess([], 1, audit, "")
        with tempfile.TemporaryDirectory(dir=ROOT / "output") as temporary, patch(
            "scripts.m11_security_scan.run_command", return_value=command
        ):
            result = scan_frontend(Path(temporary))
        self.assertEqual(result["state"], "FINDINGS")
        self.assertEqual(result["findings"], 3)

    def test_missing_image_scan_credentials_remain_an_error(self):
        inspect = subprocess.CompletedProcess([], 0, "sha256:example\n", "")
        scout = subprocess.CompletedProcess([], 1, "no credential found", "")
        with tempfile.TemporaryDirectory() as temporary, patch(
            "scripts.m11_security_scan.run_command", side_effect=[inspect, scout]
        ):
            result = scan_image(Path(temporary), "example:local")
        self.assertEqual(result["state"], "ERROR")
        self.assertEqual(result["reason"], "Docker Scout authentication unavailable")
        self.assertEqual(result["image_id"], "sha256:example")


if __name__ == "__main__":
    unittest.main()
