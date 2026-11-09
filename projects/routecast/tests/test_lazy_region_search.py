from dataclasses import replace
import random
import json
import unittest
from test_pin_pools import graph
import test_hybrid_repair as repair_fixture
from hybrid_repair import RegionalSearch, repair
from lazy_region_search import LazyRegionalSearch
from rr_graph import RREdge


class LazyTests(unittest.TestCase):
    def test_region_result_matches_eager_on_random_geometry(self):
        rng=random.Random(91004)
        for case in range(100):
            g=graph();nodes=dict(g.nodes)
            for nid in (1,2,3,4):
                loc=dict(nodes[nid].location);x=rng.randrange(5);y=rng.randrange(5)
                loc.update(xlow=str(x),xhigh=str(x+rng.randrange(3)),ylow=str(y),yhigh=str(y))
                nodes[nid]=replace(nodes[nid],location=tuple(sorted(loc.items())))
            edges=g.edges+tuple(RREdge(rng.randrange(5),rng.randrange(1,6),0,()) for _ in range(4))
            g=replace(g,nodes=nodes,edges=edges);margin=rng.randrange(3)
            eager,ew=RegionalSearch(g,margin).search(0,{5})
            lazy,lw=LazyRegionalSearch(g,margin).search(0,{5})
            self.assertEqual(eager,lazy,f'case={case}')
            self.assertEqual(ew['box'],lw['box'])
            self.assertLessEqual(lw['adjacency_filter_probes'],ew['adjacency_filter_probes'])
            self.assertLessEqual(lw['region_node_tests'],ew['region_node_tests'])

    def test_whole_repair_matches_eager(self):
        g,ep,candidates=repair_fixture.RepairTests().setup_case()
        eager=repair(g,ep,candidates);lazy=repair(g,ep,candidates,search_type=LazyRegionalSearch)
        self.assertEqual(eager['connections'],lazy['connections'])
        self.assertEqual(eager['node_occupancy'],lazy['node_occupancy'])
        self.assertEqual(eager['methods'],lazy['methods'])
        archived=json.loads(json.dumps(eager))
        self.assertEqual(json.loads(json.dumps(lazy))['connections'],archived['connections'])

    def test_archived_and_fresh_candidate_repair_serialization_matches(self):
        g,ep,candidate=repair_fixture.RepairTests().setup_case()
        # Completed quotient paths are tuples in memory and lists in archives.
        from connectivity_trial import construct
        candidate=construct(g,ep,None)
        archived=json.loads(json.dumps(candidate))
        live=repair(g,ep,candidate,search_type=LazyRegionalSearch)
        loaded=repair(g,ep,archived,search_type=LazyRegionalSearch)
        self.assertEqual(json.loads(json.dumps(live))['connections'],loaded['connections'])


if __name__=='__main__':unittest.main()
