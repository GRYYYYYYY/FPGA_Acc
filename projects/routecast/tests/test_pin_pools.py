from collections import defaultdict
from dataclasses import replace
from fractions import Fraction
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from connection_golden import Result
from pin_pools import build_pools, PinDemand
from rr_graph import RRGraph, RRNode, RREdge
from template_sketch import quotient, estimate


def graph(facets=False):
    loc=lambda ptc:tuple(sorted({'xlow':'0','xhigh':'0','ylow':'0','yhigh':'0','ptc':str(ptc)}.items()))
    nodes={0:RRNode(0,'SOURCE',1,'NONE',(),loc(0),(),None),
           1:RRNode(1,'CHANX',1,'INC_DIR',(),loc(0),(),0),
           2:RRNode(2,'CHANX',1,'INC_DIR',(),loc(1),(),0),
           3:RRNode(3,'IPIN',1,'NONE',(),loc(0),(),None),
           4:RRNode(4,'IPIN',1,'NONE',(),loc(1),(),None),
           5:RRNode(5,'SINK',2,'NONE',(),loc(0),(),None)}
    edges=[(0,1),(0,2),(1,3),(2,4),(3,5),(4,5)]
    if facets:
        nodes[6]=replace(nodes[3],id=6);edges.append((6,5))
    return RRGraph(nodes,tuple(RREdge(s,t,0,()) for s,t in edges),
                   {0:'<switch type="mux"><timing Tdel="0"/></switch>'},{0:'<segment/>'},{},'synthetic')


class PinPoolTests(unittest.TestCase):
    def test_capacity_facets_and_fractional_conservation(self):
        pools,owner=build_pools(graph(True));self.assertEqual(pools[5].capacity,2)
        self.assertEqual(len(pools[5].physical_pins),2);self.assertEqual(owner[6],5)
        demand=PinDemand(pools);self.assertEqual(demand.update(0,1,7,5),Result.COMMITTED)
        demand.update(1,1,7,5);self.assertEqual(demand.demand[5],1)
        self.assertEqual(sum(demand.physical_pin_expectation(5).values()),1)
        self.assertEqual(demand.pressure(5),Fraction(1,2))
        demand.update(0,2,remove=True);self.assertEqual(demand.demand[5],1)
        demand.update(1,2,remove=True);self.assertEqual(demand.demand[5],0)

    def test_invalid_capacity_and_update_atomicity(self):
        g=graph();nodes=dict(g.nodes);nodes[5]=replace(nodes[5],capacity=3)
        with self.assertRaises(ValueError):build_pools(replace(g,nodes=nodes))
        demand=PinDemand(build_pools(g)[0]);demand.update(0,1,2,5);before=(demand.states,demand.demand)
        self.assertEqual(demand.update(0,1,2,5),Result.STALE)
        self.assertEqual(demand.update(0,2,2,999),Result.INVALID)
        self.assertEqual((demand.states,demand.demand),before)

    def test_random_updates_against_independent_distinct_net_set(self):
        demand=PinDemand(build_pools(graph())[0]);rng=random.Random(7421);active={};epochs={}
        for _ in range(1000):
            cid=rng.randrange(30);epoch=epochs.get(cid,0)+1
            if rng.random()<.3:result=demand.update(cid,epoch,remove=True);active.pop(cid,None)
            else:
                net=rng.randrange(10);result=demand.update(cid,epoch,net,5);active[cid]=net
            self.assertEqual(result,Result.COMMITTED);epochs[cid]=epoch
            self.assertEqual(demand.demand[5],len(set(active.values())))
            self.assertEqual(demand.demand,demand.rebuild())

    def test_template_capacity_direction_and_segment_preservation(self):
        g=graph();pooled,mapping,members=quotient(g,True)
        self.assertEqual(mapping[1],mapping[2]);self.assertEqual(pooled.nodes[mapping[1]].capacity,2)
        self.assertEqual(mapping[3],mapping[4]);self.assertEqual(pooled.nodes[mapping[3]].capacity,2)
        self.assertEqual(pooled.nodes[mapping[1]].direction,'INC_DIR')
        changed=dict(g.nodes);changed[2]=replace(changed[2],direction='DEC_DIR')
        _,mapping,_=quotient(replace(g,nodes=changed),True);self.assertNotEqual(mapping[1],mapping[2])
        changed[2]=replace(changed[2],direction='INC_DIR',segment_id=1)
        _,mapping,_=quotient(replace(g,nodes=changed),True);self.assertNotEqual(mapping[1],mapping[2])

    def test_relaxed_class_capacity_does_not_prove_pin_reachability(self):
        g=graph();nodes=dict(g.nodes);nodes[6]=replace(nodes[0],id=6)
        # Two nets can reach only the same physical pin although the class has 2 pins.
        edges=tuple(e for e in g.edges if e.source!=0)+(RREdge(0,1,0,()),RREdge(6,1,0,()))
        limited=replace(g,nodes=nodes,edges=edges)
        demand=PinDemand(build_pools(limited)[0]);demand.update(0,1,1,5);demand.update(1,1,2,5)
        self.assertEqual(demand.pressure(5),1)
        # Shared reachable IPIN 3 has capacity 1; no conflict-free physical assignment.
        self.assertEqual([e.sink for e in limited.edges if e.source==1],[3])
        end={'graph_sha256':limited.sha256,'connections':[{'connection_id':0,'net_id':1,'source':0,'sink':5},
                                                       {'connection_id':1,'net_id':2,'source':6,'sink':5}]}
        self.assertEqual(estimate(limited,end,True)['prediction']['connections_completed'],2)

    def test_reject_boolean_physical_endpoint(self):
        g=graph();end={'graph_sha256':g.sha256,'connections':[{'connection_id':0,'net_id':1,'source':True,'sink':5}]}
        with self.assertRaises(ValueError):estimate(g,end,True)

    def test_pooled_prediction_and_expected_demand(self):
        g=graph();end={'graph_sha256':g.sha256,'connections':[{'connection_id':0,'net_id':7,'source':0,'sink':5}]}
        result=estimate(g,end,True)
        self.assertEqual(result['prediction']['connections_completed'],1)
        demand={int(n):Fraction(*v) for n,v in result['channel_expected_demand'].items()}
        self.assertEqual(demand[1],Fraction(1,2));self.assertEqual(demand[2],Fraction(1,2))
        self.assertEqual(sum(demand.values()),1)


if __name__=='__main__':unittest.main()
