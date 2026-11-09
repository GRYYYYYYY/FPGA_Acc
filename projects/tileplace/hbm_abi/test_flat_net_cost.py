import struct,subprocess,tempfile,unittest
from pathlib import Path
from snapshot_codec import FORMATS,RECORDS,encode
from pack_snapshot import pack
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent
class FlatNetTest(unittest.TestCase):
 def test_costs_and_invalid_references(self):
  with tempfile.TemporaryDirectory() as directory:
   directory=Path(directory);binary=directory/'query';snapshot_path=directory/'snapshot.bin'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'flat_net_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    reference=engine(seed);snapshot,_=pack(reference);blob=encode(snapshot);snapshot_path.write_bytes(blob)
    result=subprocess.run([str(binary),str(snapshot_path)],text=True,capture_output=True,check=True)
    actual={row[0]:tuple(row[1:]) for line in result.stdout.splitlines() for row in [list(map(int,line.split()))]}
    self.assertEqual(actual,{id:reference._net_cost(id,reference.positions) for id in reference.net_members})
   offsets={};cursor=224
   for name in FORMATS:offsets[name]=cursor;cursor+=len(snapshot[name])*RECORDS[name].size
   for offset,value,fmt in [(offsets['net_members'],99999,'I'),(offsets['connections'],99999,'I'),
                             (offsets['nets']+24,2**64-1,'Q'),(offsets['nets']+4,1,'I')]:
    malformed=bytearray(blob);struct.pack_into('<'+fmt,malformed,offset,value);snapshot_path.write_bytes(malformed)
    result=subprocess.run([str(binary),str(snapshot_path)],capture_output=True)
    self.assertNotEqual(result.returncode,0)
if __name__=='__main__':unittest.main()
