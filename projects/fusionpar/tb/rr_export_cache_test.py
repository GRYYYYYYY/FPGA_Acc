"""Check full metadata round-trip and fail-closed native switch identities."""
import copy
from pathlib import Path
import struct
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path[:0] = [str(ROOT/'tools'), str(ROOT.parent/'persistroute/tools')]
import rr_export_cache as cache
import write_vpr_route as writer


class CacheTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.graph = self.root/'rr.xml'
        self.graph.write_text('''<rr_graph xmlns="urn:rr">
<block_types><block_type id="0"><pin_class><pin ptc="0">clb.I[0]</pin></pin_class></block_type></block_types>
<grid><grid_loc x="1" y="2" layer="1" block_type_id="0"/></grid>
<rr_nodes>
<node id="0" type="SOURCE"><loc xlow="1" ylow="2" xhigh="1" yhigh="2" layer="1" ptc="0"/></node>
<node id="1" type="CHANX"><loc xlow="2" ylow="2" xhigh="4" yhigh="2" layer="1" ptc="8"/></node>
<node id="2" type="SINK"><loc xlow="1" ylow="2" xhigh="1" yhigh="2" layer="1" ptc="0"/></node>
<node id="3" type="IPIN"><loc xlow="5" ylow="2" xhigh="5" yhigh="2" layer="1" ptc="9"/></node>
</rr_nodes><rr_edges>
<edge src_node="0" sink_node="1" switch_id="9"/>
<edge src_node="0" sink_node="1" switch_id="3"/>
<edge src_node="1" sink_node="2" switch_id="7"/>
<edge src_node="1" sink_node="2" switch_id="7"/>
</rr_edges></rr_graph>''')
        self.nodes = self.root/'graph.nodes'
        self.edges = self.root/'graph.edges'
        self.nodes.write_bytes(b''.join(struct.pack('<IHH', *r) for r in ((0,1,0),(1,1,1),(2,0,0),(2,0,0))))
        self.edges.write_bytes(b''.join(struct.pack('<IHH', *r) for r in ((1,1,1),(2,1,1))))
        # URI characters exercise proper read-only SQLite path quoting.
        self.db = self.root/'metadata #1?.sqlite'
        self.meta = cache.build(self.graph, self.nodes, self.edges, self.db, writer)

    def test_complete_round_trip(self):
        scope = cache.csr_scope(self.nodes, self.edges)
        self.assertEqual(cache.load(self.db, self.meta, *scope, writer.Node),
                         writer.load_rr_graph(self.graph, *scope))
        self.assertEqual(self.meta['node_count'], 4)
        self.assertEqual(self.meta['edge_pair_count'], 2)
        self.assertEqual(self.meta['ambiguous_pair_count'], 1)

    def test_sparse_lookup_preserves_pin_and_layer(self):
        nodes, edges, bad = cache.load(self.db, self.meta, {1,2,3}, {(1,2)}, writer.Node)
        self.assertEqual(nodes[2].logical_pin, 'clb.I[0]')
        self.assertEqual(nodes[2].layer, 1)
        self.assertIsNone(nodes[3].logical_pin)
        self.assertEqual(edges, {(1,2):7})
        self.assertFalse(bad)  # unused ambiguous pair must not reject this route

    def test_ambiguous_pair_keeps_first_and_all_switches(self):
        _, edges, bad = cache.load(self.db, self.meta, {0,1}, {(0,1)}, writer.Node)
        self.assertEqual(edges, {(0,1):9})
        self.assertEqual(bad, {(0,1):{9,3}})

    def test_missing_node_and_edge_fail(self):
        with self.assertRaisesRegex(ValueError, 'missing used nodes'):
            cache.load(self.db, self.meta, {99}, set(), writer.Node)
        with self.assertRaisesRegex(ValueError, 'missing used edges'):
            cache.load(self.db, self.meta, {0,2}, {(0,2)}, writer.Node)

    def test_identity_and_schema_fail(self):
        changed = copy.deepcopy(self.meta)
        changed['bindings']['rr_graph']['sha256'] = '0'*64
        with self.assertRaisesRegex(ValueError, 'identity/coverage'):
            cache.load(self.db, changed, set(), set(), writer.Node)
        changed['schema'] = 'wrong'
        with self.assertRaisesRegex(ValueError, 'schema'):
            cache.load(self.db, changed, set(), set(), writer.Node)

    def test_overwrite_and_incomplete_csr_fail(self):
        with self.assertRaisesRegex(ValueError, 'already exists'):
            cache.build(self.graph, self.nodes, self.edges, self.db, writer)
        self.nodes.write_bytes(struct.pack('<IHH', 1, 1, 0))
        with self.assertRaisesRegex(ValueError, 'contiguous CSR'):
            cache.csr_scope(self.nodes, self.edges)


if __name__ == '__main__':
    unittest.main()
