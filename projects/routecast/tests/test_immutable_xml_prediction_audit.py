import unittest,tempfile
from pathlib import Path
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit

class CachedXMLTests(unittest.TestCase):
    def test_readonly_payload_and_changed_graph_rejection(self):
        xml='<rr_graph><rr_nodes><node id="0" type="SOURCE" capacity="1"><loc xlow="0" xhigh="0" ylow="0" yhigh="0"/></node><node id="1" type="SINK" capacity="1"><loc xlow="0" xhigh="0" ylow="0" yhigh="0"/></node></rr_nodes><rr_edges><edge src_node="0" sink_node="1" switch_id="0"/></rr_edges></rr_graph>'
        with tempfile.TemporaryDirectory() as directory:
            p=Path(directory)/'graph.xml';p.write_text(xml);ctx=ImmutableXMLAudit(p,sha(p))
            for view in (ctx.caps,ctx.types,ctx.spans,ctx.graph.edges.source,ctx.graph.edges.destination,ctx.graph.edges.switch):
                with self.assertRaises(TypeError):view[0]=9
            with self.assertRaises(ValueError):ctx.verify({}, {'connections':[{'physical_edge_ids':[99]}]})
            p.write_text(xml+'\n')
            with self.assertRaisesRegex(ValueError,'changed before audit'):ctx.verify({}, {})
            with self.assertRaisesRegex(ValueError,'unexpected graph digest'):ImmutableXMLAudit(p,ctx.digest)
if __name__=='__main__':unittest.main()
