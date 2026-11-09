import tempfile,unittest
from pathlib import Path
from fractions import Fraction
from buffered_rc_node_classes import read,arc_delay

XML='''<rr_graph><switches><switch id="0" type="buffer"><timing R="0.5" Tdel="1" Cinternal="0"/></switch></switches><rr_nodes><node id="0"><timing R="2" C="3"/></node><node id="1"><timing R="2" C="3"/></node></rr_nodes><rr_edges><edge src_node="0" sink_node="1" switch_id="0"/></rr_edges></rr_graph>'''

class ClassesTests(unittest.TestCase):
    def load(self,text):
        with tempfile.TemporaryDirectory() as tmp:
            p=Path(tmp)/'graph.xml';p.write_text(text);return read(p)
    def test_exact_interning(self):
        ids,classes,switches,digest=self.load(XML)
        self.assertEqual(list(ids),[0,0]);self.assertEqual(len(classes),1)
        self.assertEqual(arc_delay(classes,switches,0,0),Fraction(11,2))
        self.assertEqual(len(digest),64)
    def test_reject_electrical_and_identity_errors(self):
        variants=[XML.replace('id="1"','id="2"'),XML.replace('R="2" C="3"','C="3"'),
                  XML.replace('R="2"','R="NaN"'),XML.replace('type="buffer"','type="pass_gate"'),
                  XML.replace('Cinternal="0"','Cinternal="1"'),XML.replace('R="0.5"','R="-1"'),
                  XML.replace('<switches>','<switches><switch id="0" type="buffer"><timing/></switch>')]
        for text in variants:
            with self.subTest(text=text),self.assertRaises(ValueError):self.load(text)
