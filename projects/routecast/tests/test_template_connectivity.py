from dataclasses import replace
import random
import unittest
from test_pin_pools import graph
from template_sketch import quotient
from template_connectivity import Lifter, refine, signatures
from semantic_sketch import Sketch
from rr_graph import RREdge


class ConnectivityTests(unittest.TestCase):
    def test_false_connectivity_detected_and_refined(self):
        g=graph();edges=tuple(e for e in g.edges if (e.source,e.sink) not in {(0,2),(1,3)})
        g=replace(g,edges=edges);pooled,mapping,_=quotient(g,True)
        path=Sketch(pooled,node_budget=len(pooled.nodes)).search(mapping[0],{mapping[5]}).paths[mapping[5]]
        lifted=Lifter(g,pooled,mapping).lift(0,5,path)
        self.assertIsNone(lifted.edge_ids);self.assertEqual(lifted.failed_at,2)
        refined,colors,_,_,is_stable=refine(g,pooled,mapping)
        self.assertTrue(is_stable)
        self.assertNotIn(colors[5],Sketch(refined,node_budget=len(refined.nodes)).search(colors[0],{colors[5]}).paths)

    def test_exact_switch_and_raw_edge_sequence(self):
        g=graph();pooled,mapping,_=quotient(g,True)
        path=Sketch(pooled,node_budget=len(pooled.nodes)).search(mapping[0],{mapping[5]}).paths[mapping[5]]
        lift=Lifter(g,pooled,mapping).lift(0,5,path)
        self.assertEqual(lift.edge_ids,(0,2,4))
        for raw,q in zip(lift.edge_ids,path):
            edge=g.edges[raw];qedge=pooled.edges[q]
            self.assertEqual((mapping[edge.source],mapping[edge.sink],edge.switch_id),(qedge.source,qedge.sink,qedge.switch_id))
        with self.assertRaises(ValueError):Lifter(g,pooled,mapping).lift(0,5,path[:-1])

    def test_switch_identity_cannot_be_substituted(self):
        g=graph();edges=tuple(replace(e,switch_id=7) if i in (1,3) else e for i,e in enumerate(g.edges))
        switches={**g.switches,7:g.switches[0]};g=replace(g,edges=edges,switches=switches)
        pooled,mapping,_=quotient(g,True)
        ids={(e.source,e.sink,e.switch_id):i for i,e in enumerate(pooled.edges)}
        start=ids[(mapping[0],mapping[2],7)];last=ids[(mapping[4],mapping[5],0)]
        wrong=(start,ids[(mapping[2],mapping[3],0)],last)
        right=(start,ids[(mapping[2],mapping[4],7)],last)
        lifter=Lifter(g,pooled,mapping)
        self.assertIsNone(lifter.lift(0,5,wrong).edge_ids)
        self.assertEqual(lifter.lift(0,5,right).edge_ids,(1,3,5))

    def test_lifter_matches_independent_enumeration(self):
        rng=random.Random(85104)
        for case in range(100):
            g=graph();edges=list(g.edges)
            edges.extend(RREdge(rng.choice((1,2)),rng.choice((1,2,3,4)),0,()) for _ in range(5))
            g=replace(g,edges=tuple(e for e in edges if rng.random()>.2))
            # Ensure each physical IPIN remains assigned to its SINK class.
            g=replace(g,edges=g.edges+(RREdge(3,5,0,()),RREdge(4,5,0,())))
            pooled,mapping,_=quotient(g,True)
            result=Sketch(pooled,node_budget=len(pooled.nodes)).search(mapping[0],{mapping[5]})
            if mapping[5] not in result.paths:continue
            path=result.paths[mapping[5]];answers=[]
            def enumerate_paths(node,step,prefix):
                if step==len(path):
                    if node==5:answers.append(tuple(prefix))
                    return
                qe=pooled.edges[path[step]]
                for eid,e in enumerate(g.edges):
                    if e.source==node and mapping[e.sink]==qe.sink and e.switch_id==qe.switch_id:
                        enumerate_paths(e.sink,step+1,prefix+[eid])
            enumerate_paths(0,0,[])
            lift=Lifter(g,pooled,mapping).lift(0,5,path)
            self.assertEqual(lift.edge_ids,min(answers) if answers else None,f'case={case}')
            refined,colors,_,_,fixed=refine(g,pooled,mapping)
            self.assertTrue(fixed)
            signatures_by_node=signatures(g,colors)
            for a in g.nodes:
                for b in g.nodes:
                    if colors[a]==colors[b]:self.assertEqual(signatures_by_node[a],signatures_by_node[b])
            result=Sketch(refined,node_budget=len(refined.nodes)).search(colors[0],{colors[5]})
            if colors[5] in result.paths:
                self.assertIsNotNone(Lifter(g,refined,colors).lift(0,5,result.paths[colors[5]]).edge_ids)


if __name__=='__main__':unittest.main()
