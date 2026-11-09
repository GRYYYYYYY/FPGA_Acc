import unittest,tempfile
from pathlib import Path
from fractions import Fraction as F
from test_integer_rc_budget_boundaries import IntegerBudgetBoundaries
from prepared_integer_rc_context import prepare,PreparedIntegerRC
from pre_route_endpoints import sha
class PreparedTests(unittest.TestCase):
 def test_exact_readonly_and_changed_payload_receipt_or_inputs_reject(self):
  rc,integer,costs=IntegerBudgetBoundaries().graph([(0,3,1,F(1,7))])
  with tempfile.TemporaryDirectory() as directory:
   root=Path(directory);original=root/'original';original.write_bytes(b'input');out=root/'lattice';digest=prepare(out,rc,{str(original):sha(original)});prepared=PreparedIntegerRC(rc,out,digest)
   self.assertEqual(list(prepared.increments),integer.increments);self.assertEqual(prepared.initial(0),integer.initial(0));self.assertEqual(prepared.path(0,3,[0]),integer.path(0,3,[0]))
   with self.assertRaises(TypeError):prepared.increments[0]=0
   with self.assertRaises(ValueError):PreparedIntegerRC(rc,out,'0'*64)
   original.write_bytes(b'changed')
   with self.assertRaises(ValueError):PreparedIntegerRC(rc,out,digest)
   original.write_bytes(b'input');data=(out/'increments.bin').read_bytes();(out/'increments.bin').write_bytes(bytes([data[0]^1])+data[1:])
   with self.assertRaises(ValueError):PreparedIntegerRC(rc,out,digest)
if __name__=='__main__':unittest.main()
