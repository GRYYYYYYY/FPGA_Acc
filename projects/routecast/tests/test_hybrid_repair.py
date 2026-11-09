from dataclasses import replace
import unittest
from test_pin_pools import graph
from connectivity_trial import construct
from hybrid_repair import repair
from rr_graph import RREdge


class RepairTests(unittest.TestCase):
    def setup_case(self):
        g=graph()
        # Root can enter track1; quotient picks a track2 exit that is physically incompatible.
        # A longer real route from track1 through track2 still exists.
        edges=tuple(e for e in g.edges if (e.source,e.sink) not in {(0,2),(1,3)})+(RREdge(1,2,0,()),)
        g=replace(g,edges=edges)
        ep={'graph_sha256':g.sha256,'connections':[{'connection_id':0,'net_id':7,'source':0,'sink':5},
                                                  {'connection_id':1,'net_id':7,'source':0,'sink':5}]}
        return g,ep,construct(g,ep,0)

    def test_failed_lift_repaired_and_duplicate_net_counted_once(self):
        g,ep,candidates=self.setup_case()
        self.assertEqual(candidates['lifted_connections'],0)
        result=repair(g,ep,candidates)
        self.assertEqual(result['completed'],2);self.assertEqual(result['methods'],{'regional':2})
        self.assertEqual(result['repair_traces'][0]['failed_unique_endpoints'],1)
        self.assertEqual(result['node_occupancy']['2'],1)

    def test_full_fallback_when_region_excludes_detour(self):
        g,ep,_=self.setup_case();nodes=dict(g.nodes)
        loc=dict(nodes[2].location);loc.update(xlow='10',xhigh='10')
        nodes[2]=replace(nodes[2],location=tuple(sorted(loc.items())))
        g=replace(g,nodes=nodes)
        # Endpoint-only candidates force the regional stage to attempt repair.
        candidates={'physical_graph_sha256':g.sha256,'work':{},'connections':[{**r,'physical_edge_ids':None} for r in ep['connections']]}
        result=repair(g,ep,candidates,margin=1)
        self.assertEqual(result['completed'],2);self.assertEqual(result['methods'],{'full':2})
        self.assertGreater(result['repair_work']['full_edge_visits'],0)

    def test_unreachable_cohort_is_preserved_and_reported(self):
        g,ep,_=self.setup_case();g=replace(g,edges=tuple(e for e in g.edges if e.source!=0))
        candidates={'physical_graph_sha256':g.sha256,'work':{},'connections':[{**r,'physical_edge_ids':None} for r in ep['connections']]}
        result=repair(g,ep,candidates)
        self.assertEqual(result['completed'],0);self.assertEqual(result['requested'],2)
        self.assertEqual(result['methods'],{'failed':2});self.assertEqual(result['node_occupancy'],{})

    def test_reject_incomplete_candidate_cohort(self):
        g,ep,candidates=self.setup_case();candidates={**candidates,'connections':candidates['connections'][:1]}
        with self.assertRaisesRegex(ValueError,'incomplete'):repair(g,ep,candidates)


if __name__=='__main__':unittest.main()
