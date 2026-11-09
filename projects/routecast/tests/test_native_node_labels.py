import tempfile,unittest
from pathlib import Path
from test_pin_pools import graph
from native_node_labels import node_labels

class NativeLabelTests(unittest.TestCase):
    def parse(self,text,identity='a'*64):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.route';p.write_text(text);return node_labels(graph(),p,identity)
    def test_repeated_branch_node_counted_once_per_net(self):
        text='Placement_File: test.place Placement_ID: SHA256:'+'a'*64+'\nNet 1 (x)\nNode: 0 SOURCE\nNode: 0 SOURCE\nNet 2 (y)\nNode: 0 SOURCE\nNet 3 (z): global net connecting:\n'
        self.assertEqual(self.parse(text),{'0':2})
    def test_identity_and_malformed_node_rejected(self):
        header='Placement_File: test.place Placement_ID: SHA256:'+'a'*64+'\n'
        for text in ('Net 1 (x)\n',header+'Net 1 (x)\nNode: nonsense\n',header+'Net 1 (x)\nNode: 0 SINK\n'):
            with self.assertRaises(ValueError):self.parse(text)
        with self.assertRaises(ValueError):self.parse(header,'b'*64)

if __name__=='__main__':unittest.main()
