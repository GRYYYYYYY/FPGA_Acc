import struct,subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from snapshot_codec import FORMATS,RECORDS,encode
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent
class PlacementTest(unittest.TestCase):
 def test_constraints_and_atomic_rejection(self):
  with tempfile.TemporaryDirectory() as directory:
   directory=Path(directory);binary=directory/'query';p=directory/'snapshot.bin'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'flat_placement_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    e=engine(seed);s,_=pack(e);blob=encode(s);p.write_bytes(blob)
    occupied={loc:id for id,loc in e.positions.items()}
    candidate=next(t for unit in e.units for t in e._transactions_for_unit(unit,occupied))
    changes=candidate.trial
    data='1 0 999 999 0 0\n0\n'+str(len(changes))+' '+ ' '.join(str(v) for id,loc in sorted(changes.items()) for v in (id,*loc))+'\n'
    result=subprocess.run([str(binary),str(p)],input=data,text=True,capture_output=True,check=True)
    lines=result.stdout.splitlines();self.assertEqual(int(lines[0]),len(e.positions));self.assertEqual(lines[1],'REJECT')
    n=len(e.positions);self.assertEqual(lines[n+2],'OK');self.assertEqual(lines[2:n+2],lines[n+3:2*n+3])
    self.assertEqual(lines[2*n+3],'OK')
    expected=dict(e.positions);expected.update(changes)
    self.assertEqual({int(row.split()[0]):tuple(map(int,row.split()[1:])) for row in lines[2*n+4:]},expected)
    self.assertEqual({int(row.split()[0]):tuple(map(int,row.split()[1:])) for row in lines[2:n+2]},e.positions)
   broken=bytearray(blob);struct.pack_into('<I',broken,224+60,999)
   p.write_bytes(broken);self.assertNotEqual(subprocess.run([str(binary),str(p)],capture_output=True).returncode,0)
if __name__=='__main__':unittest.main()
