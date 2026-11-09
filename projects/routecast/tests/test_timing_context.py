import unittest
from timing_context import route_pairs,observed_context

class TimingContextTests(unittest.TestCase):
    def report(self,n=4):return '# Unit scale: 1e-09 seconds\n#Path 1\nPath Type : setup\n| (OPIN:2 x) 0 0\n| (IPIN:'+str(n)+' x) 0 0\nslack (VIOLATED) -1.5\n'
    def test_equivalent_endpoints_share_group_without_fabricated_ids(self):
        route='Net 7 (x)\nNode: 1 SOURCE\nNode: 2 OPIN\nNode: 3 CHANX\nNode: 4 IPIN\nNode: 5 SINK\nNode: 3 CHANX\nNode: 6 IPIN\nNode: 5 SINK\n'
        pairs=route_pairs(route);result=observed_context(self.report(),pairs)
        self.assertEqual(result['observed_endpoint_groups'],[(7,1,5)])
        self.assertEqual(pairs[(2,6)],{(7,1,5)})
        self.assertEqual(result['paths'][0]['slack_ns'],-1.5)
    def test_unknown_or_ambiguous_pair_rejected(self):
        for pairs in ({},{(2,4):{(7,1,5),(8,9,5)}}):
            with self.assertRaises(ValueError):observed_context(self.report(),pairs)
    def test_incomplete_segment_units_or_slack_rejected(self):
        for report in (self.report().replace('1e-09','1e-12'),self.report().replace('| (IPIN:4 x) 0 0\n',''),self.report().replace('slack (VIOLATED) -1.5\n','')):
            with self.assertRaises(ValueError):observed_context(report,{(2,4):{(7,1,5)}})

if __name__=='__main__':unittest.main()
