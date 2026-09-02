#!/usr/bin/env python3
from __future__ import annotations

import importlib.util
import sys
import tempfile
import unittest
from pathlib import Path


TOOLS = Path(__file__).parents[1] / "tools"
sys.path.insert(0, str(TOOLS))
MODULE_PATH = TOOLS / "run_vpr_placement_baseline.py"
SPEC = importlib.util.spec_from_file_location("run_vpr_placement_baseline", MODULE_PATH)
assert SPEC and SPEC.loader
baseline = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(baseline)


class VprPlacementBaselineTests(unittest.TestCase):
    def test_parse_vpr_metrics_includes_stage_times(self) -> None:
        log = """
## Initial Placement took 0.01 seconds (max_rss 10 MiB)
## Analytic Placement took 0.50 seconds (max_rss 10 MiB)
## Placement Quench took 0.02 seconds (max_rss 10 MiB)
# Placement took 1.25 seconds (max_rss 10 MiB)
Successfully routed after 7 routing iterations.
# Routing took 2.75 seconds (max_rss 20 MiB)
Total wirelength: 1234, average net length: 2.0
Final critical path delay (least slack): 4.25 ns, Fmax: 235 MHz
Flow timing analysis took 0.125 seconds (0.1 STA, 0.025 slack).
The entire flow of VPR took 5.00 seconds (max_rss 64.5 MiB)
"""
        metrics = baseline.parse_vpr_metrics(log)
        self.assertEqual(metrics["routing_iterations"], 7)
        self.assertEqual(metrics["wirelength"], 1234)
        self.assertEqual(metrics["cpd_ns"], 4.25)
        self.assertEqual(metrics["max_rss_mib"], 64.5)
        self.assertEqual(metrics["stage_times_s"]["analytic_placement"], 0.5)
        self.assertEqual(metrics["stage_times_s"]["placement_quench"], 0.02)

    def test_work_directory_must_be_empty(self) -> None:
        with tempfile.TemporaryDirectory() as temporary:
            work = Path(temporary) / "work"
            work.mkdir()
            (work / "stale.log").write_text("stale")
            with self.assertRaisesRegex(baseline.ContractError, "not empty"):
                baseline.require_empty_work(work)


if __name__ == "__main__":
    unittest.main()
