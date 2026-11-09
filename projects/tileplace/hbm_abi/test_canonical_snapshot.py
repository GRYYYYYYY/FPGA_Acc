import copy,subprocess,tempfile,unittest
from pathlib import Path
from snapshot_codec import encode
from pack_snapshot import pack
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent
class CanonicalTest(unittest.TestCase):
 def test_canonical_ownership_and_duplicates(self):
  with tempfile.TemporaryDirectory() as directory:
   directory=Path(directory);binary=directory/'query';path=directory/'snapshot.bin'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'canonical_snapshot_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    snapshot,_=pack(engine(seed));path.write_bytes(encode(snapshot))
    self.assertEqual(subprocess.run([str(binary),str(path)],capture_output=True).returncode,0)
   snapshot,_=pack(engine(0));bad=[]
   s=copy.deepcopy(snapshot);s['focus'].append(s['focus'][0]);bad.append(s)
   s=copy.deepcopy(snapshot);s['routed_edges'].append(s['routed_edges'][0]);bad.append(s)
   s=copy.deepcopy(snapshot);s['net_members'].append((0,));bad.append(s)
   s=copy.deepcopy(snapshot);s['prefix_entries'].append((999,0,0));bad.append(s)
   s=copy.deepcopy(snapshot);s['sites'].reverse();bad.append(s)
   s=copy.deepcopy(snapshot);row=list(s['blocks'][0]);row[8]=123;s['blocks'][0]=tuple(row);bad.append(s)
   s=copy.deepcopy(snapshot);row=list(s['connections'][0]);row[0]=6;s['connections'][0]=tuple(row);bad.append(s)
   s=copy.deepcopy(snapshot);s['unit_members'][0:2]=reversed(s['unit_members'][0:2]);bad.append(s)
   for i,malformed in enumerate(bad):
    path.write_bytes(encode(malformed));self.assertNotEqual(subprocess.run([str(binary),str(path)],capture_output=True).returncode,0,msg=f'corruption {i}')
if __name__=='__main__':unittest.main()
