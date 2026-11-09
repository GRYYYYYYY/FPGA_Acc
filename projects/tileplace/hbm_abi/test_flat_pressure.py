import random,struct,subprocess,tempfile,unittest
from pathlib import Path
from snapshot_codec import encode
from test_snapshot_codec import fixture
from pack_snapshot import pack
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent
class FlatPressureTest(unittest.TestCase):
 def test_queries_and_malformed_snapshots(self):
  with tempfile.TemporaryDirectory() as directory:
   directory=Path(directory);binary=directory/'query'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'flat_pressure_query.cpp'),'-o',str(binary)],check=True)
   reference=engine(3);snapshot,_=pack(reference);blob=encode(snapshot);path=directory/'snapshot.bin';path.write_bytes(blob)
   rng=random.Random(30);queries=[tuple(rng.randrange(-20,20) for _ in range(4)) for _ in range(500)]
   expected=[]
   for x,y,bx,by in queries:
    h=reference._path_pressure((x,y),(bx,by),True);v=reference._path_pressure((x,y),(bx,by),False);expected.append((h,v,min(h,v)))
   result=subprocess.run([str(binary),str(path)],input='\n'.join(' '.join(map(str,q)) for q in queries)+'\n',text=True,capture_output=True,check=True)
   self.assertEqual([tuple(map(int,row.split())) for row in result.stdout.splitlines()],expected)
   overflow_count=bytearray(blob);struct.pack_into('<Q',overflow_count,24,2**64-1)
   for damaged in [blob[:-1],blob+b'\0',b'BAD!'+blob[4:],overflow_count]:
    path.write_bytes(damaged);result=subprocess.run([str(binary),str(path)],capture_output=True)
    self.assertNotEqual(result.returncode,0)
if __name__=='__main__':unittest.main()
