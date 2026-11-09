import struct,unittest
from snapshot_codec import FORMATS,HEADER,encode,decode

def fixture():
 s={name:[] for name in FORMATS};s['generation']=17
 s['blocks']=[(9,2,-1,3,1,0,0,0,0,0,0,0,0,0)]
 s['positions']=[(-1,3,1,0)];s['units']=[(0,1,0,0,0,0)];s['unit_members']=[(9,)]
 s['prefix_lines']=[(0,-2,99,0,2)];s['prefix_entries']=[(-3,0,0),(8,0,50)]
 return s
class CodecTest(unittest.TestCase):
 def test_round_trip(self):
  s=fixture();raw=encode(s);self.assertEqual(raw[:4],b'TPLC');self.assertEqual(decode(raw),s)
 def test_reject_corruption(self):
  raw=encode(fixture())
  for broken in [raw[:-1],raw+b'\0',raw[:8],b'BAD!'+raw[4:]]:
   with self.assertRaises(ValueError):decode(broken)
  broken=bytearray(raw);struct.pack_into('<Q',broken,24,2**64-1)
  with self.assertRaises(ValueError):decode(broken)
 def test_reject_cross_references_and_prefix(self):
  for field,row in [('unit_members',(99,)),('prefix_entries',(-3,1,0))]:
   s=fixture();s[field][0]=row
   with self.assertRaises(ValueError):encode(s)
if __name__=='__main__':unittest.main()
