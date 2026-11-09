import subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from snapshot_codec import encode
from test_constrained_proposals import engine
ROOT=Path(__file__).resolve().parent
class FlatStateTest(unittest.TestCase):
 def test_commit_reject_restore_cost_consistency(self):
  with tempfile.TemporaryDirectory() as directory:
   directory=Path(directory);binary=directory/'query';path=directory/'snapshot.bin'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'flat_state_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    reference=engine(seed);snapshot,_=pack(reference);path.write_bytes(encode(snapshot));initial=dict(reference.positions)
    lines=[];expected=[];nets=set(reference.net_members)
    def evaluate(changes):
     candidate=dict(reference.positions);candidate.update(changes)
     before,after=reference._cost_pair(nets,frozenset(changes),candidate)
     values=[len(nets),*sorted(nets),len(changes)]
     for id,p in sorted(changes.items()):values.extend([id,*p])
     lines.append('EVAL '+' '.join(map(str,values)));expected.append(' '.join(map(str,(*before,*after))))
    evaluate({})
    for _ in range(2):
     occupied={p:id for id,p in reference.positions.items()}
     selected=next(t for u in reference.units for t in reference._transactions_for_unit(u,occupied))
     evaluate(selected.trial)
     values=[len(selected.trial)]
     for id,p in sorted(selected.trial.items()):values.extend([id,*p])
     lines.append('COMMIT '+' '.join(map(str,values)));expected.append('OK');reference.apply([selected]);evaluate({})
    lines.append('COMMIT 1 0 99999 0 0 0');expected.append('REJECT');evaluate({})
    lines.append('RESTORE');expected.append('OK');reference.restore(initial);evaluate({})
    result=subprocess.run([str(binary),str(path)],input='\n'.join(lines)+'\n',text=True,capture_output=True,check=True)
    self.assertEqual([line.strip() for line in result.stdout.splitlines()],expected)
if __name__=='__main__':unittest.main()
