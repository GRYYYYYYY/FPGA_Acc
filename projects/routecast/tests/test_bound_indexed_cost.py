from pathlib import Path
import sys,unittest
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from bound_indexed_cost import BoundIndexedCost,BoundNormalizedRCBase,digest,parse_bound_table
from native_indexed_cost import NativeBaseSketch
from normalized_rc_base import NormalizedRCBaseSketch
from rr_graph import RREdge
from path_rc import PathRC,State
from fractions import Fraction
import test_normalized_rc_base as fixture

MULTI=fixture.TEXT.replace('4 CHANX test 4 5 0 0.25 0 0 0\n5 CHANY test 4 4 0 0.25 0 0 0\n','4 CHANX test 4 6 0 0.25 0 0 0\n5 CHANX long 16 7 1 0.0625 0 0 0\n6 CHANY test 4 4 0 0.25 0 0 0\n7 CHANY long 16 5 1 0.0625 0 0 0\n')
class BindingTests(unittest.TestCase):
 def inputs(self,multi=False):
  g=fixture.NormalizedBlendTests().graph();mapping={10:0,20:2,30:4,40:3,50:1,60:1,70:0}
  if multi:
   nodes=dict(g.nodes);nodes[80]=replace(nodes[30],id=80,type='CHANY',segment_id=1);nodes[90]=replace(nodes[30],id=90,segment_id=1);g=replace(g,nodes=nodes,edges=g.edges+(RREdge(20,90,5,()),RREdge(90,80,5,()),RREdge(80,40,5,())),segments={**g.segments,1:'<segment id="1" name="long"/>'});mapping.update({80:7,90:5})
  text=MULTI if multi else fixture.TEXT
  csv='node_id,cost_index,segment_index\n'+''.join(f'{n},{i},{g.nodes[n].segment_id if g.nodes[n].type in {"CHANX","CHANY"} else -1}\n' for n,i in mapping.items())
  return g,text,csv,{'graph_sha256':g.sha256,'table_sha256':digest(text),'bindings_sha256':digest(csv)}
 def test_single_segment_exact_old_models(self):
  g,t,c,b=self.inputs();self.assertEqual(BoundIndexedCost(g,t,c,b,100).outgoing,NativeBaseSketch(g,t,g.sha256,100).outgoing);self.assertEqual(BoundNormalizedRCBase(g,t,c,b,100).outgoing,NormalizedRCBaseSketch(g,t,g.sha256,100).outgoing)
 def test_multi_segment_native_bindings(self):
  g,t,c,b=self.inputs(True);m=BoundIndexedCost(g,t,c,b,100);self.assertEqual(m.node_costs[30],400);self.assertEqual(m.node_costs[80],1600);self.assertEqual(m.indices[90],5);self.assertEqual(m.indices[80],7);parse_bound_table(t.replace('16 7 1','16 6 1').replace('16 5 1','16 4 1'))
  # Index 5 is CHANX here; old type-only indexing would silently use the wrong row.
  normalized=BoundNormalizedRCBase(g,t,c,b,100);self.assertEqual(normalized.indices,m.indices)
  weights={eid:w for arcs in normalized.outgoing.values() for eid,dst,w in arcs};rc=PathRC(g)
  for eid in (6,7):self.assertEqual(weights[eid],round((rc.step(State(Fraction(0),Fraction(0)),eid).delay+16)*50))
 def test_missing_duplicate_wrong_type_segment_hash(self):
  g,t,c,b=self.inputs(True)
  for bad in (c.replace('80,7,1\n',''),c+'80,7,1\n',c.replace('80,7,1','80,5,1'),c.replace('80,7,1','80,7,0')):
   with self.assertRaises(ValueError):BoundIndexedCost(g,t,bad,{**b,'bindings_sha256':digest(bad)})
  with self.assertRaises(ValueError):BoundIndexedCost(g,t,c,{**b,'table_sha256':'bad'})
  with self.assertRaises(ValueError):parse_bound_table(t.replace('16 7 1','16 5 1'))
if __name__=='__main__':unittest.main()
