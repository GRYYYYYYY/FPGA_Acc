from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
from stream_metric_domain import metric_domain
from rr_graph import read_rr_graph
from pin_template_trial import spatial
class DomainTests(unittest.TestCase):
 def test_exact_old_spatial_and_resource_domain_multisegment(self):
  original=(Path(__file__).parent/'fixtures/rr_semantics.xml').read_text();text=original.replace('</segments>','<segment id="10" name="L3"/></segments>').replace('</rr_nodes>','<node id="80" type="CHANY" direction="INC_DIR" capacity="2"><loc xlow="1" xhigh="1" ylow="0" yhigh="2" ptc="0"/><segment segment_id="10"/></node></rr_nodes>')
  with tempfile.TemporaryDirectory() as tmp:
   path=Path(tmp)/'g.xml';path.write_text(text);g=read_rr_graph(path);pv={'30':3,'80':1};tv={'30':1,'80':2};p,t,sp,st,caps,counts=metric_domain(path,pv,tv)
   self.assertEqual(sp,spatial(g,pv));self.assertEqual(st,spatial(g,tv));self.assertEqual(p,{'30':3.0,'80':0.5});self.assertEqual(t,{'30':1.0,'80':1.0});self.assertEqual(caps['80'],2);self.assertEqual(sum(counts.values()),len(g.nodes))
 def test_reject_noninteger_and_unknown_occupancy(self):
  path=Path(__file__).parent/'fixtures/rr_semantics.xml'
  for bad in ({'30':-1},{'30':True},{'30':0.5}):
   with self.assertRaises(ValueError):metric_domain(path,bad,{})
  with self.assertRaises(AssertionError):metric_domain(path,{'999':1},{})
if __name__=='__main__':unittest.main()
