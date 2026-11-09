import unittest,tempfile
from pathlib import Path
import xml.etree.ElementTree as ET
from test_streaming_rr_nodes import NodeTests
from test_bound_indexed_cost import BindingTests
from rr_graph import read_rr_graph
from cached_bound_rc import CachedBoundRC
from prepared_csr import write,read
from streaming_bound_csr import convert

class ConversionTests(unittest.TestCase):
    def test_complete_xml_conversion_exact(self):
        for multi,side in [(False,"NONE"),(True,"NONE")]+[(True,s) for s in __import__("prepared_csr").SIDES if s!="NONE"]:
            g,t,c,b=BindingTests().inputs(multi)
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'rr.xml';root=NodeTests().xml(g)
                for n in root.find('rr_nodes'):n.find('loc').set('side',side)
                ET.ElementTree(root).write(p)
                actualg=read_rr_graph(p);identity={**b,'graph_sha256':actualg.sha256}
                old=Path(d)/'old';new=Path(d)/'new'
                expected=write(CachedBoundRC(actualg,t,c,identity),old)
                actual=convert(p,t,c,identity,new)
                self.assertEqual(actual,expected)
                for name in expected['files']:self.assertEqual((old/(name+'.bin')).read_bytes(),(new/(name+'.bin')).read_bytes())
                read(new,actualg.sha256,expected['context_sha256'])
                fast=Path(d)/'fast';optimized=convert(p,t,c,identity,fast,class_cache=True)
                self.assertEqual(optimized,expected)
                for name in expected['files']:self.assertEqual((old/(name+'.bin')).read_bytes(),(fast/(name+'.bin')).read_bytes())
    def test_unknown_endpoint_and_binding_rejected(self):
        g,t,c,b=BindingTests().inputs()
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'rr.xml';root=NodeTests().xml(g);root.find('rr_edges')[0].set('sink_node','99999');ET.ElementTree(root).write(p)
            from pre_route_endpoints import sha
            identity={**b,'graph_sha256':sha(p)}
            with self.assertRaisesRegex(ValueError,'unknown edge endpoint'):convert(p,t,c,identity,Path(d)/'bad')
            self.assertFalse((Path(d)/'bad').exists())
            with self.assertRaisesRegex(ValueError,'binding identity mismatch'):convert(p,t,c,b,Path(d)/'bad2')
