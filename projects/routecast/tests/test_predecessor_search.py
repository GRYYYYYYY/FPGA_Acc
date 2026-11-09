import sys,unittest,random
from pathlib import Path
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph,RREdge
from compact_indexed_sketch import CompactIndexedSketch
from predecessor_search import PredecessorSearch
class Tests(unittest.TestCase):
 def test_random_cycles_ties_disabled_and_large_costs(self):
  rng=random.Random(731);g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml')
  for case in range(150):
   nodes=dict(g.nodes)
   if case%9==0:nodes[60]=replace(nodes[60],capacity=0)
   edges=g.edges+tuple(RREdge(rng.choice(list(nodes)),rng.choice(list(nodes)),5,()) for _ in range(25))
   graph=replace(g,nodes=nodes,edges=edges);base=CompactIndexedSketch(graph,node_budget=len(nodes))
   base.outgoing={n:tuple((e,d,None if w is None else rng.choice((0,0,1,2,(1<<64)-2))) for e,d,w in arcs) for n,arcs in base.outgoing.items()}
   other=PredecessorSearch(base);sinks=[n for n in nodes if nodes[n].type=='SINK']
   for source in [n for n in nodes if nodes[n].type=='SOURCE']:
    for targets in [[s] for s in sinks]+[sinks,[]]:
     self.assertEqual(other.search(source,targets),base.search(source,targets))
 def test_budget_rejected(self):
  g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml')
  with self.assertRaises(ValueError):PredecessorSearch(CompactIndexedSketch(g,node_budget=1))
if __name__=='__main__':unittest.main()
