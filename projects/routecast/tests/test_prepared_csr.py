from pathlib import Path
import sys,tempfile,unittest
from dataclasses import replace
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from prepared_csr import write,read,arcs
from compact_indexed_sketch import CompactIndexedSketch
from rr_graph import read_rr_graph,RREdge
class TransportTests(unittest.TestCase):
 def test_sparse_ids_parallel_arcs_disabled_and_metadata(self):
  g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');nodes=dict(g.nodes);nodes[60]=replace(nodes[60],capacity=0);g=replace(g,nodes=nodes,edges=g.edges+(RREdge(20,30,5,()),RREdge(30,20,5,())));engine=CompactIndexedSketch(g,node_budget=len(g.nodes))
  with tempfile.TemporaryDirectory() as tmp:
   out=Path(tmp)/'csr';write(engine,out);m,f=read(out,g.sha256)
   for n in g.nodes:self.assertEqual(tuple(arcs(f,n)),engine.outgoing[n])
   self.assertEqual(f['node_ids'].tolist(),sorted(g.nodes));self.assertEqual(m['edges'],8);self.assertEqual(f['directions'][2],1);self.assertEqual(f['ptc'][1],3);self.assertEqual(f['capacities'][-2],0)
   with self.assertRaises(ValueError):read(out,'wronggraph')
   with self.assertRaisesRegex(ValueError,'context mismatch'):read(out,g.sha256,'wrongcontext')
   (out/'costs.bin').write_bytes(b'corrupt')
   with self.assertRaises(ValueError):read(out,g.sha256)
 def test_reject_incomplete_and_unsupported_costs(self):
  g=read_rr_graph(Path(__file__).parent/'fixtures/rr_semantics.xml');engine=CompactIndexedSketch(g,node_budget=len(g.nodes))
  with tempfile.TemporaryDirectory() as tmp:
   engine.outgoing[10]=()
   with self.assertRaises(ValueError):write(engine,Path(tmp)/'a')
if __name__=='__main__':unittest.main()
