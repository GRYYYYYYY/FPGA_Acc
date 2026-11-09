from copy import deepcopy
from collections import Counter
import unittest
import test_hybrid_repair as fixture
from hybrid_repair import repair
from physical_prediction_audit import audit

class AuditTests(unittest.TestCase):
    def test_shared_net_and_complete_cohort(self):
        g,e,c=fixture.RepairTests().setup_case();r=repair(g,e,c);report=audit(g,e,r,c)
        self.assertEqual(report['completed'],2)
        self.assertEqual(report['connection_node_touches'],2*report['net_node_touches'])
    def test_zero_failure_method_schema(self):
        g,e,c=fixture.RepairTests().setup_case();r=repair(g,e,c)
        r['methods']=dict(Counter(row['method'] for row in r['connections']))
        self.assertNotIn('failed',r['methods'])
        self.assertEqual(audit(g,e,r,c)['completed'],2)
        bad=deepcopy(r);bad['methods']['failed']=0
        with self.assertRaisesRegex(ValueError,'method counters inconsistent'):audit(g,e,bad,c)
    def test_independent_corruption_rejection(self):
        g,e,c=fixture.RepairTests().setup_case();r=repair(g,e,c)
        for corrupt in ('cohort','arc','occupancy','counter'):
            bad=deepcopy(r)
            if corrupt=='cohort':bad['connections'].pop()
            if corrupt=='arc':bad['connections'][0]['physical_edge_ids']=[-1]
            if corrupt=='occupancy':bad['node_occupancy']['0']=2
            if corrupt=='counter':bad['completed']=1
            with self.subTest(corrupt=corrupt),self.assertRaises(ValueError):audit(g,e,bad,c)

if __name__=='__main__':unittest.main()
