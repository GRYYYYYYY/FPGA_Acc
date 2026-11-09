import tempfile,unittest
from pathlib import Path
import xml.etree.ElementTree as ET
from test_bound_indexed_cost import BindingTests
from cached_bound_rc import CachedBoundRC
from prepared_csr import write,read as read_csr
from rr_graph import read_rr_graph
from streaming_rr_nodes import read
from path_rc import number

class NodeTests(unittest.TestCase):
    def xml(self,g):
        root=ET.Element('rr_graph')
        for tag,records in (('switches',g.switches),('segments',g.segments)):
            section=ET.SubElement(root,tag)
            for key in sorted(records):section.append(ET.fromstring(records[key]))
        section=ET.SubElement(root,'rr_nodes')
        for key,n in sorted(g.nodes.items()):
            node=ET.SubElement(section,'node',id=str(key),type=n.type,capacity=str(n.capacity),direction=n.direction)
            ET.SubElement(node,'loc',dict(n.location));ET.SubElement(node,'timing',dict(n.timing))
            if n.segment_id is not None:ET.SubElement(node,'segment',segment_id=str(n.segment_id))
        section=ET.SubElement(root,'rr_edges')
        for e in g.edges:ET.SubElement(section,'edge',src_node=str(e.source),sink_node=str(e.sink),switch_id=str(e.switch_id))
        return root
    def test_xml_fields_exact_old_reader(self):
        for multi in (False,True):
            g,t,c,b=BindingTests().inputs(multi)
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'rr.xml';ET.ElementTree(self.xml(g)).write(p)
                old=read_rr_graph(p);b={**b,'graph_sha256':old.sha256}
                dest=Path(d)/'csr';write(CachedBoundRC(old,t,c,b),dest);_,expected=read_csr(dest,old.sha256)
                fields,r,cap,switches,segments,sha=read(p)
                for name,data in fields.items():self.assertEqual(data,expected[name])
                self.assertEqual(sha,old.sha256);self.assertEqual(switches,dict(old.switches));self.assertEqual(segments,dict(old.segments))
                for rank,n in enumerate(old.nodes.values()):
                    timing=dict(n.timing);self.assertEqual(r[rank],number(timing.get('R','0')));self.assertEqual(cap[rank],number(timing.get('C','0')))
    def test_invalid_inventory_rejected(self):
        g,*_=BindingTests().inputs()
        for mutation in ('duplicate','negative_rc','missing_segment'):
            root=self.xml(g);nodes=root.find('rr_nodes')
            if mutation=='duplicate':nodes[1].set('id',nodes[0].get('id'))
            elif mutation=='negative_rc':nodes[0].find('timing').set('R','-1')
            else:
                n=next(n for n in nodes if n.get('type') in ('CHANX','CHANY'));n.remove(n.find('segment'))
            with tempfile.TemporaryDirectory() as d:
                p=Path(d)/'rr.xml';ET.ElementTree(root).write(p)
                with self.assertRaises(ValueError):read(p)
