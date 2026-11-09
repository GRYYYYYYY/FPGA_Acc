import sys,itertools,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from bank_mandatory_cover_v1 import minimum_cover,components
class Contract(unittest.TestCase):
 def test_all_four_vertex_graphs_against_subset_enumeration(self):
  universe=list(itertools.combinations(range(4),2))
  for mask in range(64):
   es=[e for i,e in enumerate(universe) if mask>>i&1];valid=[]
   for n in range(5):
    for c in itertools.combinations(range(4),n):
     if all(set(c)&set(e) for e in es):valid.append(c)
   expected=min(valid,key=lambda c:(len(c),c));r=minimum_cover(es);self.assertEqual(tuple(r['cover']),expected)
 def test_overlaps_cliques_and_disjoint_additivity(self):
  es={(0,1),(1,2),(0,2),(4,5)};parts=components(es)
  self.assertEqual(sum(minimum_cover(e)['minimum_departures'] for n,e in parts),3)
  self.assertEqual(minimum_cover([(0,1),(0,2),(0,3)])['minimum_departures'],1)
 def test_budget_and_invalid_domains(self):
  with self.assertRaises(RuntimeError):minimum_cover([(0,1)],max_states=0)
  with self.assertRaises(ValueError):minimum_cover([(0,0)])
if __name__=='__main__':unittest.main()
