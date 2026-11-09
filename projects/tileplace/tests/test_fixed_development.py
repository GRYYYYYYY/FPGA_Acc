"""Reject a superficially successful development run with unusable native trials."""

import copy
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from run_fixed_development import validate
from tileplace_vpr import ContractError


class FixedDevelopmentTests(unittest.TestCase):
    def test_wrong_implementation_and_failed_rejected_oracle_are_not_valid_results(self):
        # Construct an internally consistent zero-acceptance search. Its final
        # layout is still legal when a trial fails, which must not mask failure.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            place = root / "final.place"
            place.write_text("a 0 0 0 0 #0\n")
            from tileplace_vpr import sha256
            base = {"status": "pass", "legal": True, "cpd_ns": 10, "wirelength": 100}
            report = {"status": "pass", "baseline": base, "final": base,
                      "closure_calls": 1, "accepted_transactions": 0,
                      "input_place": {"path": str(place)},
                      "output_place": {"path": str(place), "sha256": sha256(place)},
                      "provenance": {"implementation": {"sha256": "expected", "sources": []}, "inputs": []},
                      "trials": [{"trial": 1, "accepted": False, "incumbent_before": base,
                                  "closure": {"status": "pass", "legal": True}}]}
            path = root / "report.json"
            path.write_text(json.dumps(report))
            validate(path, "expected")
            with self.assertRaises(ContractError):
                validate(path, "other")
            broken = copy.deepcopy(report)
            broken["trials"][0]["closure"] = {"status": "fail", "legal": False}
            path.write_text(json.dumps(broken))
            with self.assertRaisesRegex(ContractError, "native oracle failure"):
                validate(path, "expected")


if __name__ == "__main__":
    unittest.main()
