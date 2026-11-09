import sys
from pathlib import Path
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from native_base_costs import read_table, map_nodes

TABLE = '''Delay normalization factor: 2.37623e-11
Cost Index Base Cost Ortho Cost Index Seg Index Inv. Length T. Linear T. Quadratic C. Load
0 SOURCE 2.37623e-11 -1 -1 nan 0 0 0
1 SINK 0 -1 -1 nan 0 0 0
2 OPIN 2.37623e-11 -1 -1 nan 0 0 0
3 IPIN 2.25742e-11 -1 -1 nan 0 0 0
4 CHANX L4 9.50492e-11 6 0 0.25 1e-10 0 0
5 CHANX L16 3.80197e-10 6 1 0.0625 1e-10 0 0
6 CHANY L4 9.50492e-11 4 0 0.25 1e-10 0 0
7 CHANY L16 3.80197e-10 4 1 0.0625 1e-10 0 0
'''


class NativeCosts(unittest.TestCase):
    def test_native_types_and_segments(self):
        with tempfile.TemporaryDirectory() as temp:
            p = Path(temp) / 'echo'
            p.write_text(TABLE)
            table, rows = read_table(p)
            self.assertEqual([r['base_cost_ps_q'] for r in rows], [24, 0, 24, 23, 95, 380, 95, 380])
            graph = Path(temp) / 'graph.xml'
            # Deliberately reorder the segment IDs between consecutive nodes.
            graph.write_text('<rr_graph><rr_nodes><node id="0" type="CHANX"><segment segment_id="1"/></node>'
                             '<node id="1" type="CHANY"><segment segment_id="0"/></node>'
                             '<node id="2" type="SINK"/></rr_nodes></rr_graph>')
            costs, _ = map_nodes(graph, table)
            self.assertEqual(costs, [380, 95, 0])
            graph.write_text(graph.read_text().replace('segment_id="1"', 'segment_id="9"'))
            with self.assertRaises(ValueError):
                map_nodes(graph, table)

    def test_invalid_tables_rejected(self):
        for text in [TABLE.replace('2.37623e-11', 'nan'), TABLE.replace('2.37623e-11', '-1e-9'),
                     TABLE.replace('2.37623e-11', '1e-6'), TABLE.replace('CHANX', 'CHANZ'),
                     TABLE + TABLE.splitlines()[2] + '\n', TABLE.replace('1 SINK 0 -1 -1 nan 0 0 0\n', '')]:
            with self.subTest(text=text), tempfile.TemporaryDirectory() as temp:
                p = Path(temp) / 'echo'
                p.write_text(text)
                with self.assertRaises(ValueError):
                    read_table(p)


if __name__ == '__main__':
    unittest.main()
