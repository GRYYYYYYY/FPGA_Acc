import csv
import json
from pathlib import Path
import struct
import sys
import tempfile
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'tools'))
from pack_native_slr_graph import pack


class NativeSlrConverterTest(unittest.TestCase):
    def fixture(self, root, mutation=None):
        graph = root / 'graph'; graph.mkdir()
        tables = {
            'nodes': [['id','tile','wire','owner_die','membership_mask','intent','xlow','ylow','xhigh','yhigh'],
                      [0,'A','source',0,1,'LOCAL',0,0,0,0],
                      [1,'A','bridge',0,3,'NODE_LAGUNA_DATA',0,0,0,1],
                      [2,'B','sink',1,2,'LOCAL',0,1,0,1]],
            'wires': [['node_id','tile','wire','die'],[0,'A','source',0],[1,'A','bridge',0],
                      [1,'B','bridge',1],[2,'B','sink',1]],
            'pips': [['id','src','dst','tile','start_wire','end_wire','bidirectional','die'],
                     [0,0,1,'A','source','bridge','false',0],
                     [1,1,2,'B','bridge','sink','false',1]],
        }
        if mutation: mutation(tables)
        for name, rows in tables.items():
            with (graph / (name + '.csv')).open('w', newline='') as stream:
                csv.writer(stream).writerows(rows)
        return graph

    def test_no_node_duplication_and_edge_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp); graph=self.fixture(root); prefix=root/'packed'
            pack(graph,prefix,[(7,0,2)])
            self.assertEqual((root/'packed.resources').stat().st_size,3*16)
            self.assertEqual(struct.unpack('<3H',(root/'packed.node_membership').read_bytes()),(1,3,2))
            self.assertEqual(struct.unpack('<2H',(root/'packed.edge_die').read_bytes()),(0,1))
            catalog=json.loads((root/'packed.edge_catalog.json').read_text())
            self.assertEqual([(e['src'],e['dst'],e['pip_id']) for e in catalog],[(0,1,0),(1,2,1)])
            with self.assertRaises(FileExistsError):pack(graph,prefix,[(7,0,2)])

    def test_reject_inconsistent_native_evidence_before_writing(self):
        mutations=[lambda t:t['nodes'][2].__setitem__(4,1),
                   lambda t:t['pips'][2].__setitem__(3,'A'),
                   lambda t:t['wires'].append([2,'A','bridge',0]),
                   lambda t:t['pips'].append([2,1,2,'B','bridge','sink','false',1]),
                   lambda t:t['pips'][1].__setitem__(6,'maybe')]
        for mutation in mutations:
            with self.subTest(mutation=mutation), tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); graph=self.fixture(root,mutation)
                with self.assertRaises(ValueError):pack(graph,root/'packed',[(7,0,2)])
                self.assertFalse(list(root.glob('packed.*')))

    def test_reject_ambiguous_or_shared_source_terminal(self):
        for con in [[(7,1,2)],[(7,0,2),(8,0,2)]]:
            with tempfile.TemporaryDirectory() as tmp:
                root=Path(tmp); graph=self.fixture(root)
                with self.assertRaises(ValueError):pack(graph,root/'packed',con)

    def test_explicit_parallel_and_reverse_keys(self):
        def mutation(t):
            t['wires'].extend([[0,'A','source2',0],[1,'A','bridge2',0]])
            t['pips'].append([2,0,1,'A','source2','bridge2','false',0])
            t['pips'][2][6]='true'
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);graph=self.fixture(root,mutation)
            with self.assertRaises(ValueError):pack(graph,root/'legacy',[(7,0,2)])
            pack(graph,root/'packed',[(7,0,2)],edge_identity=True)
            self.assertEqual(struct.unpack('<4I',(root/'packed.edge_ref').read_bytes()),(0,4,2,3))
            catalog=json.loads((root/'packed.edge_catalog.json').read_text())
            self.assertEqual([(e['src'],e['dst']) for e in catalog],[(0,1),(0,1),(1,2),(2,1)])

    def test_explicit_mode_rejects_duplicate_pip_identity(self):
        with tempfile.TemporaryDirectory() as tmp:
            root=Path(tmp);graph=self.fixture(root,lambda t:t['pips'].append([2,1,2,'B','bridge','sink','false',1]))
            with self.assertRaises(ValueError):pack(graph,root/'packed',[(7,0,2)],edge_identity=True)
            self.assertFalse(list(root.glob('packed.*')))


if __name__ == '__main__':unittest.main()
