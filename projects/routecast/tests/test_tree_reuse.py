from pathlib import Path
import sys,unittest,random
from dataclasses import replace
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from rr_graph import read_rr_graph,RREdge
from tree_reuse import TreeReuse

class TreeTests(unittest.TestCase):
 def graph(self):return read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml')
 def test_tree_and_failed_branch_preservation(self):
  g=self.graph();m=TreeReuse(g,[10]*len(g.edges),[1]*len(g.edges));r=m.route(10,{60,50});self.assertEqual(r.paths,{50:(0,1,2,3),60:(0,1,2,4)});self.assertEqual(len(r.parents),5)
  g=replace(g,edges=g.edges[:-2]+g.edges[-1:]);r=TreeReuse(g,[10]*len(g.edges),[1]*len(g.edges)).route(10,{50,60});self.assertEqual(r.failures,(60,));self.assertEqual(r.paths,{50:(0,1,2,3)})
 def test_exhaustive_incremental_branch_oracle(self):
  rng=random.Random(20261004);g=self.graph();g=replace(g,edges=g.edges+(RREdge(20,40,5,()),RREdge(30,60,5,()),RREdge(40,30,5,())))
  for _ in range(100):
   weights=[rng.randrange(9) for e in g.edges];timing=[Fraction(rng.randrange(9),3) for e in g.edges];tree={10:()};arrivals={10:Fraction(0)};expected={}
   for target in (50,60):
    choices=[]
    def walk(node,path,score,visited):
     if node==target:choices.append((score,len(path),path));return
     for eid,e in enumerate(g.edges):
      if e.source==node and e.sink not in tree and e.sink not in visited:walk(e.sink,path+(eid,),score+weights[eid],visited|{e.sink})
    for node,prefix in list(tree.items()):walk(node,prefix,round(arrivals[node]),set(tree))
    selected=min(choices)[2];expected[target]=selected;node=10;prefix=();arrival=Fraction(0)
    for eid in selected:node=g.edges[eid].sink;prefix+=(eid,);arrival+=timing[eid];tree[node]=prefix;arrivals[node]=arrival
   self.assertEqual(TreeReuse(g,weights,timing).route(10,{60,50}).paths,expected)
 def test_existing_prefix_timing_is_not_free(self):
  g=self.graph();g=replace(g,edges=g.edges+(RREdge(30,60,5,()),));weights=[10]*7;weights[4]=1;weights[6]=5
  r=TreeReuse(g,weights,[10]*7).route(10,{50,60})
  self.assertEqual(r.paths[60],(0,1,6))
 def test_validation_and_capacity(self):
  g=self.graph()
  for bad in ([1]*5,[-1]*6,[True]*6):
   with self.assertRaises(ValueError):TreeReuse(g,bad,[0]*6)
  with self.assertRaises(ValueError):TreeReuse(g,[1]*6,[-1]*6)
  nodes=dict(g.nodes);nodes[30]=replace(nodes[30],capacity=0);r=TreeReuse(replace(g,nodes=nodes),[1]*6,[0]*6).route(10,{50,60});self.assertEqual(r.failures,(50,60));self.assertEqual(r.parents,{})
if __name__=='__main__':unittest.main()
