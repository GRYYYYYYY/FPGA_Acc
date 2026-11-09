import unittest,tempfile
from pathlib import Path
from prepared_csr import write as old_write,read
from streaming_csr_builder import write
from cached_bound_rc import CachedBoundRC
from test_bound_indexed_cost import BindingTests

class BuilderTests(unittest.TestCase):
    def test_all_payload_fields_and_context_exact(self):
        for multi in (False,True):
            g,t,c,b=BindingTests().inputs(multi);engine=CachedBoundRC(g,t,c,b)
            with tempfile.TemporaryDirectory() as d:
                a=Path(d)/'old';z=Path(d)/'new';previous=old_write(engine,a);_,f=read(a,g.sha256)
                nodes={name:data for name,data in f.items() if name not in ('row_offsets','edge_ids','dest_ranks','switch_ids','costs')}
                costs={eid:w for arcs in engine.outgoing.values() for eid,_,w in arcs}
                arcs=lambda:((i,e.source,e.sink,e.switch_id,costs[i]) for i,e in enumerate(g.edges))
                context={k:v for k,v in previous['context'].items() if k not in ('cost_payload_sha256','edge_mapping_sha256')}
                actual=write(nodes,arcs,z,context)
                self.assertEqual(previous,actual)
                for name in previous['files']:self.assertEqual((a/(name+'.bin')).read_bytes(),(z/(name+'.bin')).read_bytes())
                read(z,g.sha256,previous['context_sha256'])
    def test_changed_second_pass_rejected(self):
        g,t,c,b=BindingTests().inputs();engine=CachedBoundRC(g,t,c,b)
        with tempfile.TemporaryDirectory() as d:
            a=Path(d)/'old';m=old_write(engine,a);_,f=read(a,g.sha256)
            nodes={name:data for name,data in f.items() if name not in ('row_offsets','edge_ids','dest_ranks','switch_ids','costs')}
            calls=[0]
            def arcs():
                calls[0]+=1
                for i,e in enumerate(g.edges):yield i,e.source,e.sink,e.switch_id,calls[0]
            with self.assertRaisesRegex(ValueError,'changed between passes'):write(nodes,arcs,Path(d)/'new',m['context'])
