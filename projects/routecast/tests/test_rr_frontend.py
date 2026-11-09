import random
from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph
from audit_native_route import audit
from rr_occupancy import Occupancy
from connection_golden import Result
FIXTURE=Path(__file__).parent/'fixtures/rr_semantics.xml'


class RRTests(unittest.TestCase):
    def test_repeated_sink_still_validates_incoming_arc(self):
        text=FIXTURE.with_suffix('.route').read_text().replace('Node: 60 SINK','Node: 50 SINK')
        with tempfile.TemporaryDirectory() as tmp:
            route=Path(tmp)/'repeated.route';route.write_text(text)
            result=audit(FIXTURE,route)
            self.assertEqual(len(result['connections']),2)
            self.assertEqual(result['connections'][0]['edge_ids'],result['connections'][1]['edge_ids'])
            prefix,suffix=text.rsplit('Node: 40 IPIN Switch: 5',1)
            route.write_text(prefix+'Node: 40 IPIN Switch: 99'+suffix)
            with self.assertRaises(ValueError):audit(FIXTURE,route)

    def test_native_branch_replay_and_switch_validation(self):
        route=FIXTURE.with_suffix('.route')
        result=audit(FIXTURE,route)
        self.assertEqual(len(result['connections']),2)
        self.assertEqual(result['shared_node_occurrences_saved'],4)
        self.assertEqual(result['occupied_nodes'],6)
        self.assertEqual(result['overflow_nodes'],{})
        with tempfile.TemporaryDirectory() as tmp:
            bad=Path(tmp)/'bad.route'
            bad.write_text(route.read_text().replace('Node: 20 OPIN Switch: 5','Node: 20 OPIN Switch: 99'))
            with self.assertRaises(ValueError): audit(FIXTURE,bad)

    def test_semantic_preservation_and_sparse_ids(self):
        g=read_rr_graph(FIXTURE)
        self.assertEqual(len(g.nodes),7); self.assertEqual(len(g.edges),6)
        self.assertEqual(g.nodes[30].direction,'INC_DIR')
        self.assertEqual(g.nodes[30].segment_id,9)
        self.assertEqual(dict(g.nodes[20].location)['side'],'RIGHT')
        self.assertEqual(dict(g.nodes[20].location)['ptc'],'3')
        self.assertIn('Tdel',g.switches[5])
        self.assertEqual(g.edges[0].source,10)
        with self.assertRaises(TypeError): g.nodes[10]=g.nodes[20]

    def test_reject_corrupted_records(self):
        text=FIXTURE.read_text()
        variants=[text.replace('sink_node="20"','sink_node="999"',1),
                  text.replace('switch_id="5"','switch_id="99"',1),
                  text.replace('segment_id="9"','segment_id="99"'),
                  text.replace('id="70"','id="10"'),
                  text.replace('capacity="1"','capacity="-1"',1),
                  text.replace('direction="INC_DIR"','direction="UNKNOWN"')]
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'bad.xml'
            for variant in variants:
                p.write_text(variant)
                with self.assertRaises(ValueError): read_rr_graph(p)

    def test_shared_trunk_remove_and_cross_net_overflow(self):
        ledger=Occupancy(read_rr_graph(FIXTURE))
        self.assertEqual(ledger.update(1,1,4,10,50,(0,1,2,3)),Result.COMMITTED)
        self.assertEqual(ledger.update(2,1,4,10,60,(0,1,2,4)),Result.COMMITTED)
        self.assertEqual(ledger.occupancy[30],1)
        self.assertEqual(ledger.update(1,2,remove=True),Result.COMMITTED)
        self.assertEqual(ledger.occupancy[30],1); self.assertEqual(ledger.occupancy[50],0)
        self.assertEqual(ledger.update(3,1,5,70,50,(5,1,2,3)),Result.COMMITTED)
        self.assertEqual(ledger.overflow()[30],1)
        self.assertEqual(ledger.occupancy,ledger.rebuild())

    def test_invalid_replacement_and_stale_are_atomic(self):
        ledger=Occupancy(read_rr_graph(FIXTURE)); ledger.update(1,1,4,10,50,(0,1,2,3))
        before=(ledger.states,ledger.occupancy)
        for args,result in [((1,2,4,10,60,(0,1,4)),Result.INVALID),
                            ((1,1,4,10,60,(0,1,2,4)),Result.STALE),
                            ((2,1,4,70,50,(5,1,2,3)),Result.INVALID)]:
            self.assertEqual(ledger.update(*args),result)
            self.assertEqual((ledger.states,ledger.occupancy),before)
        self.assertEqual(ledger.update(1,2,4,10,60,(0,1,2,4)),Result.COMMITTED)
        self.assertEqual(ledger.occupancy[50],0); self.assertEqual(ledger.occupancy[60],1)

    def test_random_updates_vs_independent_net_union(self):
        ledger=Occupancy(read_rr_graph(FIXTURE)); rng=random.Random(9136); expected={}; epochs={}
        for step in range(1000):
            cid=rng.randrange(30); epoch=epochs.get(cid,0)+1; net=cid%5
            if rng.random()<.25:
                result=ledger.update(cid,epoch,remove=True); expected.pop(cid,None)
            else:
                sink=rng.choice((50,60)); path=(0,1,2,3 if sink==50 else 4)
                result=ledger.update(cid,epoch,net,10,sink,path)
                expected[cid]=(net,{10,20,30,40,sink})
            self.assertEqual(result,Result.COMMITTED); epochs[cid]=epoch
            totals={nid:len({net for net,nodes in expected.values() if nid in nodes}) for nid in ledger.graph.nodes}
            self.assertEqual(ledger.occupancy,totals,f'step={step}')
            self.assertEqual(ledger.occupancy,ledger.rebuild())


if __name__=='__main__': unittest.main()
