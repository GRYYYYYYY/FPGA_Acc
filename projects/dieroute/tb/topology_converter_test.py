#!/usr/bin/env python3
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "tools"))
from export_vpr_topology import export

GRAPH = '''<rr_graph><rr_nodes>
<node id="0" type="SOURCE" capacity="1"><loc layer="0"/></node>
<node id="1" type="SINK" capacity="1"><loc layer="1"/></node>
<node id="2" type="CHANX" capacity="1"><loc layer="0"/></node>
</rr_nodes><rr_edges>
<edge src_node="0" sink_node="1" switch_id="0"/>
<edge src_node="2" sink_node="1" switch_id="0"/>
</rr_edges></rr_graph>'''.replace('<loc ', '<loc xlow="0" ylow="0" xhigh="1" yhigh="1" ')


class TopologyTest(unittest.TestCase):
    def test_shared_destination_is_not_two_slls(self):
        with tempfile.TemporaryDirectory() as d:
            graph, prefix = Path(d) / "rr.xml", Path(d) / "input"
            graph.write_text(GRAPH)
            report = export(graph, prefix)
            self.assertEqual(report["die_count"], 2)
            self.assertEqual(report["crossings"][0]["rr_edge_count"], 2)
            self.assertIn("NOT SLL capacity", report["capacity_semantics"])
            self.assertEqual(Path(str(prefix) + ".node_die").read_bytes(), struct.pack("<HHH", 0, 1, 0))
            self.assertEqual(json.loads(Path(str(prefix) + ".topology.json").read_text()), report)
            with self.assertRaises(FileExistsError):
                export(graph, prefix)

    def test_fail_closed(self):
        for bad in (GRAPH.replace('layer="1"', ''), GRAPH.replace('id="1"', 'id="4"'),
                    GRAPH.replace('sink_node="1"', 'sink_node="8"'),
                    GRAPH.replace('layer="1"', 'layer="0"'), GRAPH.replace('capacity="1"', 'capacity="0"')):
            with self.subTest(bad=bad), tempfile.TemporaryDirectory() as d:
                graph = Path(d) / "rr.xml"
                graph.write_text(bad)
                with self.assertRaises(ValueError):
                    export(graph, Path(d) / "input")
                self.assertFalse((Path(d) / "input.topology.json").exists())


if __name__ == "__main__":
    unittest.main()
