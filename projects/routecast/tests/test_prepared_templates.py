from copy import deepcopy
import unittest
import test_hybrid_repair as fixture
from connectivity_trial import construct
from prepared_templates import PreparedTemplates
from indexed_sketch import IndexedSketch
from compact_indexed_sketch import CompactIndexedSketch

class PreparedTests(unittest.TestCase):
    def test_all_refinements_equal_fresh_and_repeat_has_no_state_leak(self):
        g,e,_=fixture.RepairTests().setup_case()
        for rounds in (0,1,2,None):
            with self.subTest(rounds=rounds):
                prepared=PreparedTemplates(g,rounds);expected=construct(g,e,rounds)
                first=prepared.predict(e);self.assertEqual(first,expected)
                compact=PreparedTemplates(g,rounds,search_type=CompactIndexedSketch)
                self.assertEqual(compact.predict(e),expected)
                indexed=PreparedTemplates(g,rounds,search_type=IndexedSketch)
                self.assertEqual(indexed.predict(e),expected)
                self.assertEqual(indexed.predict(e),expected)
                witnesses=len(prepared.lifter.witness)
                empty=prepared.predict({**e,'connections':[]});self.assertEqual(empty['node_occupancy'],{})
                first['connections'].clear();first['node_occupancy'].clear()
                self.assertEqual(prepared.predict(e),expected)
                self.assertEqual(len(prepared.lifter.witness),witnesses)
    def test_changed_cohort_fresh_equivalence_and_graph_identity(self):
        g,e,_=fixture.RepairTests().setup_case();prepared=PreparedTemplates(g,2)
        changed={**e,'connections':[{**r,'net_id':r['connection_id']} for r in e['connections']]}
        self.assertEqual(prepared.predict(changed),construct(g,changed,2))
        with self.assertRaisesRegex(ValueError,'identity'):prepared.predict({**e,'graph_sha256':'changed'})

if __name__=='__main__':unittest.main()
