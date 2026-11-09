import tempfile
from pathlib import Path
import unittest
from blif_constants import constants

class ConstantsTests(unittest.TestCase):
    def evaluate(self,text):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/'test.blif';p.write_text(text);return constants(p)
    def test_constants_and_buffer_chain(self):
        self.assertEqual(self.evaluate('.names z\n.names o\n1\n.names z alias\n1 1\n.names alias o out\n11 1\n'),{'z':0,'o':1,'alias':0,'out':0})
    def test_unknown_input_and_latch_not_assumed_constant(self):
        self.assertEqual(self.evaluate('.names x y\n1 1\n.latch y q\n.names q r\n1 1\n'),{})
    def test_zero_cover_and_continuation(self):
        self.assertEqual(self.evaluate('.names o\n1\n.names o \\\n inv\n0 1\n'),{'o':1,'inv':0})
    def test_mixed_polarity_rejected(self):
        with self.assertRaises(ValueError):self.evaluate('.names o\n1\n.names o x\n0 0\n1 1\n')

if __name__=='__main__':unittest.main()
