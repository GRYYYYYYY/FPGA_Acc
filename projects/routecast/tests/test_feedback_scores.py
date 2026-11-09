import unittest
import test_hybrid_repair as fixture
from hybrid_repair import repair
from feedback_scores import scores

class FeedbackScoreTests(unittest.TestCase):
    def test_shared_net_does_not_double_count_span_or_bbox(self):
        g,e,c=fixture.RepairTests().setup_case();pred=repair(g,e,c);a=scores(g,e,pred['node_occupancy'])
        single={**e,'connections':e['connections'][:1]};self.assertEqual(scores(g,single,pred['node_occupancy']),a)
        different={**e,'connections':[{**r,'net_id':r['connection_id']} for r in e['connections']]}
        b=scores(g,different,{k:2*v for k,v in pred['node_occupancy'].items()})
        self.assertEqual(b['channel_net_span_sum'],2*a['channel_net_span_sum'])
        self.assertEqual(b['net_bbox_hpwl'],2*a['net_bbox_hpwl'])
    def test_bad_resources_and_counts_rejected(self):
        g,e,c=fixture.RepairTests().setup_case()
        for occ in ({'99999':1},{'0':-1},{'0':True},{'0':.5}):
            with self.assertRaises(ValueError):scores(g,e,occ)

if __name__=='__main__':unittest.main()
