from pathlib import Path
import sys,unittest
from dataclasses import replace
from fractions import Fraction as F
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph, RREdge
from buffered_rc_sketch import BufferedRCSketch
from path_rc import PathRC
class BufferedRCTests(unittest.TestCase):
 def graph(self):
  g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml')
  return replace(g,nodes={n:replace(v,timing=(('R','4'),('C','3'))) for n,v in g.nodes.items()})
 def test_search_and_exact_path_cost(self):
  g=self.graph();engine=BufferedRCSketch(g);rc=PathRC(g)
  result=engine.search(10,{50,60});self.assertEqual(result.paths,{50:(0,1,2,3),60:(0,1,2,4)})
  for path in result.paths.values():
   weights={eid:w for arcs in engine.outgoing.values() for eid,dst,w in arcs}
   self.assertEqual(sum(weights[eid] for eid in path),rc.path(10,path).delay*engine.scale)
 def test_rc_changes_path_selection_with_independent_enumeration(self):
  g=self.graph();g=replace(g,edges=g.edges+(RREdge(20,40,5,()),))
  engine=BufferedRCSketch(g);rc=PathRC(g);candidates=[]
  def walk(node,path,visited):
   if node==50:
    weights=[round(rc.path(g.edges[e].source,[e]).delay*engine.scale) for e in path]
    candidates.append((sum(weights),len(path),path));return
   for eid,e in enumerate(g.edges):
    if e.source==node and e.sink not in visited:walk(e.sink,path+(eid,),visited|{e.sink})
  walk(10,(),{10})
  self.assertEqual(engine.search(10,{50}).paths[50],min(candidates)[2])
  self.assertEqual(min(candidates)[2],(0,6,3))
 def test_nonbuffered_negative_and_scale_rejected(self):
  g=self.graph()
  for kind in ('pass_gate','short'):
   with self.assertRaises(ValueError):BufferedRCSketch(replace(g,switches={5:f'<switch id="5" type="{kind}"><timing/></switch>'}))
  nodes=dict(g.nodes);nodes[10]=replace(nodes[10],timing=(('R','100'),('C','0')))
  with self.assertRaises(ValueError):BufferedRCSketch(replace(g,nodes=nodes,switches={5:'<switch id="5" type="mux"><timing Cinternal="5"/></switch>'}))
  for scale in (0,True,1.5):
   with self.assertRaises(ValueError):BufferedRCSketch(g,scale)
 def test_rounding_bound_and_capacity_disabled(self):
  g=self.graph();engine=BufferedRCSketch(g,3);rc=PathRC(g)
  for arcs in engine.outgoing.values():
   for eid,dst,w in arcs:self.assertLessEqual(abs(F(w,3)-rc.path(g.edges[eid].source,[eid]).delay),F(1,6))
  nodes=dict(g.nodes);nodes[30]=replace(nodes[30],capacity=0)
  self.assertEqual(BufferedRCSketch(replace(g,nodes=nodes)).search(10,{50}).paths,{})
if __name__=='__main__':unittest.main()
