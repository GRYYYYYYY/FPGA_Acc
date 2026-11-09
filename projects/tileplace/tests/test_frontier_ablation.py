import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from audit_frontier_ablation import compare_arms, audit_process
from tileplace_vpr import ContractError


class FrontierPairTests(unittest.TestCase):
    def test_failed_process_and_nonfinite_runtime_are_rejected(self):
        audit_process({"returncode": 0, "process_wall_s": 1})
        for receipt in ({"returncode": 1, "process_wall_s": 1},
                        {"returncode": 0, "process_wall_s": float("nan")},
                        {"returncode": 0, "process_wall_s": -1}):
            with self.assertRaises(ContractError):
                audit_process(receipt)

    def test_pair_requires_equal_inputs_budget_and_opposite_arms(self):
        enabled = {"baseline": {"cpd_ns": 10, "wirelength": 100}, "config": {"weight": 2},
                   "final": {"cpd_ns": 9, "wirelength": 101},
                   "provenance": {"inputs": [{"sha256": "same"}],
                                  "initial_route_feedback_sha256": "route",
                                  "initial_timing_feedback_sha256": "timing",
                                  "settings": {"use_no_goods": True, "max_closures": 24}}}
        disabled = copy.deepcopy(enabled)
        disabled["provenance"]["settings"]["use_no_goods"] = False
        disabled["final"]["cpd_ns"] = 10
        self.assertEqual(compare_arms(enabled, disabled)["cpd_enabled_over_disabled"], .9)
        # The audit verifies evidence, rather than requiring a favorable outcome.
        equal = copy.deepcopy(disabled)
        equal["final"] = copy.deepcopy(enabled["final"])
        self.assertEqual(compare_arms(enabled, equal)["cpd_enabled_over_disabled"], 1)
        better_control = copy.deepcopy(disabled)
        better_control["final"]["cpd_ns"] = 8
        self.assertGreater(compare_arms(enabled, better_control)["cpd_enabled_over_disabled"], 1)
        for section, key, value in (("settings", "use_no_goods", True),
                                    ("settings", "max_closures", 48)):
            broken = copy.deepcopy(disabled)
            broken["provenance"][section][key] = value
            with self.assertRaises(ContractError):
                compare_arms(enabled, broken)
        broken = copy.deepcopy(disabled)
        broken["provenance"]["inputs"] = [{"sha256": "different"}]
        with self.assertRaises(ContractError):
            compare_arms(enabled, broken)


if __name__ == "__main__":
    unittest.main()
