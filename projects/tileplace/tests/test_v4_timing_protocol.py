"""Timing repetitions must preserve intermediate decisions, not just final QoR."""

import copy
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[1] / "tools"))
from run_v4_timing_protocol import signature, feedback_signature


class TimingProtocolTests(unittest.TestCase):
    def test_feedback_comparison_ignores_route_header_paths_only(self):
        report = {"provenance": {"initial_route_feedback_sha256": "route",
                                 "initial_timing_feedback_sha256": "timing",
                                 "feedback_refreshes": [{"candidate_route_sha256": "path1",
                                     "timing_report_sha256": "raw1", "route_feedback_sha256": "edges1",
                                     "timing_feedback_sha256": "weights1", "parser": {"mode": "generic"}}]}}
        moved = copy.deepcopy(report)
        moved["provenance"]["feedback_refreshes"][0]["candidate_route_sha256"] = "path2"
        moved["provenance"]["feedback_refreshes"][0]["timing_report_sha256"] = "raw2"
        self.assertEqual(feedback_signature(report), feedback_signature(moved))
        moved["provenance"]["feedback_refreshes"][0]["timing_feedback_sha256"] = "weights2"
        self.assertNotEqual(feedback_signature(report), feedback_signature(moved))

    def test_signature_ignores_paths_but_detects_intermediate_changes(self):
        report = {
            "output_place": {"sha256": "final", "path": "/run1/final.place"},
            "config": {"timing_weight": 2}, "stop_reason": "epoch_limit",
            "closure_calls": 1, "accepted_transactions": 0,
            "final": {"legal": True, "cpd_ns": 10, "wirelength": 100, "report_path": "/run1/closure"},
            "trials": [{"accepted": False, "reason": "timing_first_acceptance_not_met",
                        "transaction_ids": ["move1"], "transaction_count": 1,
                        "candidate_place": {"sha256": "candidate", "path": "/run1/candidate"},
                        "closure": {"cpd_ns": 11, "wirelength": 101}}],
        }
        relocated = copy.deepcopy(report)
        relocated["output_place"]["path"] = "/run2/final.place"
        relocated["final"]["report_path"] = "/run2/closure"
        relocated["trials"][0]["candidate_place"]["path"] = "/run2/candidate"
        self.assertEqual(signature(report), signature(relocated))
        for field, value in (("accepted", True), ("reason", "different"), ("transaction_ids", ["move2"])):
            altered = copy.deepcopy(relocated)
            altered["trials"][0][field] = value
            self.assertNotEqual(signature(report), signature(altered))
        relocated["trials"][0]["candidate_place"]["sha256"] = "different"
        self.assertNotEqual(signature(report), signature(relocated))


if __name__ == "__main__":
    unittest.main()
