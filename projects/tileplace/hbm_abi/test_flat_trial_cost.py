import random,subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from snapshot_codec import encode
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent

def queries(reference,count,seed):
 rng=random.Random(seed);payload=[str(count)];expected=[]
 for _ in range(count):
  changed=frozenset(rng.sample(list(reference.positions),rng.randrange(len(reference.positions)+1)))
  changes={id:tuple(rng.randrange(-20,21) for _ in range(4)) for id in changed}
  touched=set().union(*(reference.block_nets[id] for id in changed)) if changed else set()
  candidate=dict(reference.positions);candidate.update(changes)
  before,after=reference._cost_pair(touched,changed,candidate);expected.append((*before,*after))
  payload.append(f'{len(touched)} {len(changed)}')
  payload.append(' '.join(map(str,sorted(touched))))
  payload.extend(' '.join(map(str,(id,*p))) for id,p in sorted(changes.items()))
 return '\n'.join(payload)+'\n',expected
class TrialTest(unittest.TestCase):
 def test_candidate_pairs_without_mutation(self):
  with tempfile.TemporaryDirectory() as directory:
   directory=Path(directory);binary=directory/'query';snapshot=directory/'snapshot.bin'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'flat_trial_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    reference=engine(seed);initial=dict(reference.positions);records,_=pack(reference);snapshot.write_bytes(encode(records))
    data,expected=queries(reference,100,seed)
    result=subprocess.run([str(binary),str(snapshot)],input=data,text=True,capture_output=True,check=True)
    self.assertEqual([tuple(map(int,line.split())) for line in result.stdout.splitlines()],expected)
    self.assertEqual(reference.positions,initial)
if __name__=='__main__':unittest.main()
