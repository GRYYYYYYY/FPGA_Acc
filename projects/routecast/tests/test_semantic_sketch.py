from pathlib import Path
import sys
import random
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph, RRGraph, RRNode, RREdge
from connection_golden import Edge
from test_connection_golden import exhaustive_path
from semantic_sketch import Sketch
from indexed_sketch import IndexedSketch
from compact_indexed_sketch import CompactIndexedSketch
from prepare_sketch_inputs import prepare
from prediction_metrics import compare, ranks, spearman
from run_sketch import predict
from evaluate_sketch import evaluate
FIXTURE=Path(__file__).parent/'fixtures/rr_semantics.xml'


class SketchTests(unittest.TestCase):
    def test_same_coordinate_edges_and_shared_paths(self):
        g=read_rr_graph(FIXTURE)
        for mode in ('rr_hop','rr_length_switch'):
            result=Sketch(g,mode,20).search(10,{50,60})
            self.assertEqual(result.paths,{50:(0,1,2,3),60:(0,1,2,4)})
            self.assertFalse(result.budget_exhausted)
            self.assertEqual(Sketch(g,mode,20).search(10,{50,60}),result)

    def test_budget_and_invalid_endpoints(self):
        g=read_rr_graph(FIXTURE); result=Sketch(g,'rr_hop',2).search(10,{50})
        self.assertEqual(result.paths,{})
        self.assertTrue(result.budget_exhausted)
        with self.assertRaises(ValueError): Sketch(g).search(20,{50})
        with self.assertRaises(ValueError): Sketch(g).search(10,{20})

    def test_label_stripping_and_predictor_rejection(self):
        g=read_rr_graph(FIXTURE)
        labels={'graph_sha256':g.sha256,'connections':[{'connection_id':0,'net_id':4,'source':10,'sink':50,'edge_ids':[0,1,2,3]}]}
        inputs=prepare(labels)
        self.assertNotIn('edge_ids',inputs['connections'][0])
        prediction=predict(g,inputs,'rr_hop',20)
        result=evaluate(g,prediction,labels,inputs)
        self.assertEqual(result['resource_utilization']['mae'],0)
        inputs['connections'][0]['edge_ids']=[0,1,2,3]
        with self.assertRaises(ValueError): predict(g,inputs,'rr_hop',20)

    def test_failure_stays_in_evaluation(self):
        g=read_rr_graph(FIXTURE)
        labels={'graph_sha256':g.sha256,'connections':[{'connection_id':0,'net_id':4,'source':10,'sink':50,'edge_ids':[0,1,2,3]}]}
        inputs=prepare(labels); prediction=predict(g,inputs,'rr_hop',1)
        result=evaluate(g,prediction,labels,inputs)
        self.assertEqual(result['connections_completed'],0)
        self.assertEqual(result['resource_utilization']['mae'],1)
        self.assertIsNone(result['resource_utilization']['spearman'])

    def test_random_search_vs_independent_exhaustive_paths(self):
        rng=random.Random(69104)
        for case in range(50):
            count=rng.randrange(2,7)
            nodes={}
            for nid in range(count):
                kind='SOURCE' if nid==0 else 'SINK' if nid==count-1 else 'CHANX'
                loc=(('xlow','0'),('ylow','0'),('xhigh',str(nid%3)),('yhigh','0'),('ptc','0'))
                nodes[nid]=RRNode(nid,kind,1,'NONE',(),loc,(),0 if kind=='CHANX' else None)
            edges=tuple(RREdge(rng.randrange(count),rng.randrange(count),5,()) for _ in range(12))
            graph=RRGraph(nodes,edges,{5:'<switch type="mux"><timing Tdel="1e-10"/></switch>'},{0:'<segment/>'},{},'test')
            for mode in ('rr_hop','rr_length_switch'):
                oracle_edges=[]
                for edge in edges:
                    length=(edge.sink%3+1) if nodes[edge.sink].type=='CHANX' else 0
                    cost=1 if mode=='rr_hop' else 1+256*length+100
                    oracle_edges.append(Edge(edge.source,edge.sink,cost))
                expected=exhaustive_path(count,oracle_edges,0,count-1,count-1)
                result=Sketch(graph,mode,count+1).search(0,{count-1})
                self.assertEqual(result.paths.get(count-1),expected,f'case={case}, mode={mode}')
                for budget in (1,2,count+1):
                    self.assertEqual(CompactIndexedSketch(graph,mode,budget).search(0,{count-1}),
                                     Sketch(graph,mode,budget).search(0,{count-1}))
                    self.assertEqual(IndexedSketch(graph,mode,budget).search(0,{count-1}),
                                     Sketch(graph,mode,budget).search(0,{count-1}))

    def test_indexed_multi_sink_and_disabled_capacity(self):
        from dataclasses import replace
        g=read_rr_graph(FIXTURE)
        for mode in ('rr_hop','rr_length_switch'):
            for budget in range(1,9):
                for sinks in (set(),{50},{50,60}):
                    self.assertEqual(CompactIndexedSketch(g,mode,budget).search(10,sinks),Sketch(g,mode,budget).search(10,sinks))
                    self.assertEqual(IndexedSketch(g,mode,budget).search(10,sinks),Sketch(g,mode,budget).search(10,sinks))
            nodes=dict(g.nodes);nodes[40]=replace(nodes[40],capacity=0)
            disabled=replace(g,nodes=nodes)
            self.assertEqual(CompactIndexedSketch(disabled,mode,20).search(10,{50,60}),Sketch(disabled,mode,20).search(10,{50,60}))
            self.assertEqual(IndexedSketch(disabled,mode,20).search(10,{50,60}),Sketch(disabled,mode,20).search(10,{50,60}))

    def test_metrics_ties_and_undefined(self):
        self.assertEqual(ranks([1,1,3]),[.5,.5,2])
        self.assertAlmostEqual(spearman([1,2,3],[3,2,1]),-1)
        self.assertIsNone(spearman([0,0],[0,1]))
        result=compare({1:2,2:1,3:0},{1:0,2:1,3:2},1)
        self.assertEqual(result['precision_at_k'],0)
        self.assertAlmostEqual(result['spearman'],-1)


if __name__=='__main__': unittest.main()
