from pathlib import Path
import sys
import tempfile
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph
from routing_process_labels import build, native_table, node_occupancy
from evaluate_process_overflow import evaluate
FIXTURE=Path(__file__).parent/'fixtures'
TABLE='''
 1 0.0 0.0 0 99 2 3 4 (10.0%) 4 (5%)
 2 0.0 0.5 0 10 1 1 0 (0.0%) 4 (5%)
Total local nets with reserved CLB opins: 0
Completed routing consistency check successfully.
VPR succeeded
'''


class ProcessLabelTests(unittest.TestCase):
    def test_multinet_shared_node_overflow_and_trajectory(self):
        g=read_rr_graph(FIXTURE/'rr_semantics.xml');shared=(FIXTURE/'rr_semantics.route').read_text()
        competing='''\nNet 5 (other)
Node: 70 SOURCE Switch: 5
Node: 20 OPIN Switch: 5
Node: 30 CHANX Switch: 5
Node: 40 IPIN Switch: 5
Node: 50 SINK Switch: -1
'''
        with tempfile.TemporaryDirectory() as tmp:
            paths=[Path(tmp)/f'iteration_{i:03d}.route' for i in (1,2)]
            paths[0].write_text(shared+competing);paths[1].write_text(shared)
            result=build(g,paths,TABLE)
            self.assertEqual([r['overused_nodes'] for r in result['iterations']],[4,0])
            self.assertEqual(result['overflow_recurrence']['30'],1)
            self.assertEqual(result['iterations'][0]['node_occupancy']['30'],2)
            with self.assertRaisesRegex(ValueError,'overuse'):build(g,paths,TABLE.replace('3 4 (','3 3 ('))
            with self.assertRaisesRegex(ValueError,'missing iteration'):build(g,paths[:1],TABLE)

    def test_overflow_classification_and_complete_cohort_gate(self):
        g=read_rr_graph(FIXTURE/'rr_semantics.xml')
        prediction={'graph_sha256':g.sha256,'mode':'test','connections_completed':2,'connections_requested':2,
                    'node_occupancy':{'30':2}}
        labels={'graph_sha256':g.sha256,'iterations':[{'iteration':1,'node_overflow':{'30':1}}]}
        result=evaluate(g,prediction,labels)
        self.assertEqual(result['precision'],1)
        self.assertEqual(result['recall'],1)
        self.assertEqual(result['true_positive'],1)
        prediction['node_occupancy']={}
        result=evaluate(g,prediction,labels)
        self.assertIsNone(result['precision']);self.assertEqual(result['recall'],0)
        prediction['connections_completed']=1
        with self.assertRaisesRegex(ValueError,'complete cohort'):evaluate(g,prediction,labels)

    def test_native_evidence_required(self):
        g=read_rr_graph(FIXTURE/'rr_semantics.xml')
        with self.assertRaisesRegex(ValueError,'OPIN'):build(g,[],TABLE.replace('opins: 0','opins: 1'))
        with self.assertRaisesRegex(ValueError,'success'):build(g,[],TABLE.replace('VPR succeeded',''))
        with self.assertRaises(ValueError):native_table('no table here')

    def test_reject_global_node_and_type_mismatch(self):
        g=read_rr_graph(FIXTURE/'rr_semantics.xml')
        with self.assertRaises(ValueError):node_occupancy('Net 1 (clk): global net connecting:\nNode: 10 SOURCE',g)
        with self.assertRaises(ValueError):node_occupancy('Net 1 (x)\nNode: 10 SINK',g)
        with self.assertRaises(ValueError):node_occupancy('Node: 10 SOURCE',g)


if __name__=='__main__':unittest.main()
