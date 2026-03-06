import json
import unittest
from pathlib import Path

from tools.k8s_policy_check import check_dir


class TestPolicyChecker(unittest.TestCase):
    def test_checker_passes_on_repo_manifests(self) -> None:
        findings = check_dir(Path("k8s/manifests"))
        fails = [f for f in findings if f.status == "fail"]
        self.assertEqual(fails, [])

    def test_checker_emits_json_findings(self) -> None:
        raw = Path("k8s/manifests/20-deployment.json").read_text(encoding="utf-8")
        self.assertIsInstance(json.loads(raw), dict)


if __name__ == "__main__":
    unittest.main()
