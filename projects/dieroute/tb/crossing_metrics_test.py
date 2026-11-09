#!/usr/bin/env python3
from pathlib import Path
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from audit_rr_experiments import native_crossings


class CrossingMetricsTest(unittest.TestCase):
    def test_branch_anchor_is_not_connected_to_previous_sink(self):
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / "route"
            p.write_text('''Net 0 (net)
Node: 0 SOURCE (0,0,0) Switch: 0
Node: 1 CHANX (0,0,1) Switch: 1
Node: 2 SINK (0,0,1) Switch: -1
Node: 0 SOURCE (0,0,0) Switch: 0
Node: 1 CHANX (0,0,1) Switch: 1
Node: 3 SINK (0,0,1) Switch: -1
Net 1 (other)
Node: 4 SOURCE (0,0,0) Switch: 0
Node: 1 CHANX (0,0,1) Switch: 1
Node: 3 SINK (0,0,1) Switch: -1
''')
            self.assertEqual(native_crossings(p, [0, 1, 1, 1, 0]),
                             {"net_crossing_edges": 2, "net_crossing_destinations": 2})


if __name__ == "__main__":
    unittest.main()
