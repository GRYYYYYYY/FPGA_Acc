import copy,random,subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent

def payload(s,trials):
 rows=[f"{len(s['blocks'])} {len(s['sites'])} {len(s['regions'])} {len(trials)}"]
 for name in ['blocks','positions','sites','regions']:rows.extend(' '.join(map(str,row)) for row in s[name])
 for trial in trials:
  rows.append(str(len(trial)))
  rows.extend(' '.join(map(str,(id,*p))) for id,p in trial)
 return '\n'.join(rows)+'\n'
class TrialLegalityArrayTest(unittest.TestCase):
 def test_constraints_occupancy_and_faults(self):
  rng=random.Random(32);queries=0;valid_count=0
  with tempfile.TemporaryDirectory() as d:
   binary=Path(d)/'query'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'trial_legality_array_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    e=engine(seed);s,_=pack(e);occupied={p:id for id,p in e.positions.items()}
    trials=[[],*([ (id,p)] for id,p in e.positions.items())]
    for _ in range(500):
     ids=rng.sample(list(e.positions),rng.randrange(1,5));trial=[]
     for id in ids:
      p=rng.choice(list(e.site_by_loc)) if rng.randrange(4) else tuple(rng.randrange(-12,13) for _ in range(4))
      trial.append((id,p))
     trials.append(trial)
    for unit in e.units:trials.extend(list(t.trial.items()) for t in e._transactions_for_unit(unit,occupied))
    expected=[(int(e._valid_trial(dict(t),frozenset(id for id,p in t),occupied)),0) for t in trials]
    result=subprocess.run([str(binary)],input=payload(s,trials),text=True,capture_output=True,check=True)
    self.assertEqual([tuple(map(int,row.split())) for row in result.stdout.splitlines()],expected)
    queries+=len(trials);valid_count+=sum(v for v,status in expected)
    faults=[(s,[[(999,e.positions[0])]],(0,1)),(s,[[(0,e.positions[0]),(0,e.positions[0])]],(0,1))]
    bad=copy.deepcopy(s);row=list(bad['blocks'][0]);row[6]=2**64-1;row[7]=1;bad['blocks'][0]=tuple(row)
    faults.append((bad,[[(0,e.positions[0])]],(0,2)))
    for records,trial,expected_fault in faults:
     result=subprocess.run([str(binary)],input=payload(records,trial),text=True,capture_output=True,check=True)
     self.assertEqual(tuple(map(int,result.stdout.split())),expected_fault)
  self.assertGreater(valid_count,100)
  print(f'{queries} legality queries ({valid_count} valid), 36 faults pass')
if __name__=='__main__':unittest.main()
