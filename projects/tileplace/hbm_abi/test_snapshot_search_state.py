import subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from strict_snapshot_codec import encode
from test_constrained_proposals import engine
from compare_proposals import parse
from test_snapshot_search import query
ROOT=Path(__file__).resolve().parent
class SearchStateTest(unittest.TestCase):
 def test_commit_rejection_and_restore_search(self):
  with tempfile.TemporaryDirectory() as directory:
   d=Path(directory);binary=d/'server';snapshot=d/'snapshot.bin'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'snapshot_search_server.cpp'),'-o',str(binary)],check=True)
   commits=0
   for seed in range(12):
    e=engine(seed);records,_=pack(e);snapshot.write_bytes(encode(records));initial=dict(e.positions)
    commands=[];expected=[]
    def capture():
     for color in range(4):
      transactions,_=e.propose_color(color)
      commands.append('QUERY\n'+query(e,color,True))
      expected.append(sorted((t.transaction_id,t.score_q20) for t in transactions))
    capture();commands.append('SAVE 0\n')
    occupied={p:id for id,p in e.positions.items()}
    candidates=[t for u in e.units for t in e._transactions_for_unit(u,occupied)]
    self.assertTrue(candidates)
    transaction=min(candidates,key=lambda t:(t.score_q20,t.transaction_id))
    changes=dict(transaction.transaction_id[2])
    commands.append('COMMIT '+str(len(changes))+'\n'+'\n'.join(' '.join(map(str,(id,*p))) for id,p in sorted(changes.items()))+'\n')
    e.apply([transaction]);commits+=1;capture()
    ids=list(e.positions);bad=e.positions[ids[1]]
    commands.append('COMMIT 1\n'+' '.join(map(str,(ids[0],*bad)))+'\n');capture()
    commands.append('RESTORE 0\n');e.restore(initial);capture()
    result=subprocess.run([str(binary),str(snapshot)],input=''.join(commands),text=True,capture_output=True,check=True)
    actual=[];buffer=[];statuses=[]
    for line in result.stdout.splitlines():
     if line=='END':actual.append(parse('\n'.join(buffer)));buffer=[]
     elif line in ['SAVED','COMMITTED','REJECTED','RESTORED']:statuses.append(line)
     else:buffer.append(line)
    self.assertEqual(actual,expected,msg=f'seed {seed}')
    self.assertEqual(statuses,['SAVED','COMMITTED','REJECTED','RESTORED'])
   self.assertEqual(commits,12)
if __name__=='__main__':unittest.main()
