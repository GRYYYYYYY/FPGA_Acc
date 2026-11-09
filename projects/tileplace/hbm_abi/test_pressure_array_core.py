import random,subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent

def payload(snapshot,queries):
 lines=[f"{len(snapshot['prefix_lines'])} {len(snapshot['prefix_entries'])} {len(queries)}"]
 for name in ['prefix_lines','prefix_entries']:lines.extend(' '.join(map(str,row)) for row in snapshot[name])
 lines.extend(' '.join(map(str,row)) for row in queries)
 return '\n'.join(lines)+'\n'
class ArrayCoreTest(unittest.TestCase):
 def test_reference_and_fault_status(self):
  with tempfile.TemporaryDirectory() as directory:
   binary=Path(directory)/'query'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'pressure_array_core.cpp'),str(ROOT/'pressure_array_tb.cpp'),'-o',str(binary)],check=True)
   rng=random.Random(30)
   for seed in range(12):
    reference=engine(seed);snapshot,_=pack(reference)
    queries=[tuple(rng.randrange(-30,31) for _ in range(4)) for _ in range(500)]
    queries.extend([(0,0,0,0),(-2147483648,0,2147483647,0)])
    expected=[]
    for x,y,bx,by in queries:
     h=reference._path_pressure((x,y),(bx,by),True);v=reference._path_pressure((x,y),(bx,by),False);expected.append((h,v,min(h,v),0))
    result=subprocess.run([str(binary)],input=payload(snapshot,queries),text=True,capture_output=True,check=True)
    self.assertEqual([tuple(map(int,row.split())) for row in result.stdout.splitlines()],expected)
   faults=[({'prefix_lines':[(0,0,1,2**64-1,1)],'prefix_entries':[(0,0,0)]},1),
           ({'prefix_lines':[(0,0,10,0,2)],'prefix_entries':[(0,0,10),(1,0,0)]},2),
           ({'prefix_lines':[(0,0,2**64-1,0,1)],'prefix_entries':[(0,0,0)]},3)]
   for snapshot,status in faults:
    result=subprocess.run([str(binary)],input=payload(snapshot,[(0,0,1,0)]),text=True,capture_output=True,check=True)
    self.assertEqual(tuple(map(int,result.stdout.split())),(0,0,0,status))
if __name__=='__main__':unittest.main()
