import copy,subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from strict_snapshot_codec import encode
from test_constrained_proposals import engine
from compare_proposals import parse
from test_snapshot_search import query
ROOT=Path(__file__).resolve().parent
class FeedbackSearchTest(unittest.TestCase):
 def test_atomic_update_and_whole_snapshot_restore(self):
  with tempfile.TemporaryDirectory() as directory:
   d=Path(directory);binary=d/'server'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'feedback_search_server.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    e=engine(seed);records,_=pack(e);initial=d/'initial.bin';initial.write_bytes(encode(records));commands=[];expected=[]
    def capture():
     for color in range(4):
      t,_=e.propose_color(color);commands.append('QUERY\n'+query(e,color,True));expected.append(sorted((x.transaction_id,x.score_q20) for x in t))
    capture();commands.append('SAVE 0\n')
    e.pressure_q16={edge:weight*7+123 for edge,weight in e.pressure_q16.items()}
    e.path_edges_q16={edge:weight*3 for edge,weight in e.path_edges_q16.items()};e.focus_blocks={6}
    updated,_=pack(e);refresh=d/'refresh.bin';refresh.write_bytes(encode(updated));commands.append(f'FEEDBACK {refresh}\n');capture()
    corrupt=d/'corrupt.bin';corrupt.write_bytes(refresh.read_bytes()[:-1])
    topology=copy.deepcopy(updated);row=list(topology['connections'][0]);row[-1]+=1;topology['connections'][0]=tuple(row)
    altered=d/'topology.bin';altered.write_bytes(encode(topology))
    occupied={p:id for id,p in e.positions.items()};candidates=[t for u in e.units for t in e._transactions_for_unit(u,occupied)]
    self.assertTrue(candidates);e.apply([candidates[0]]);moved,_=pack(e)
    mismatch=d/'mismatch.bin';mismatch.write_bytes(encode(moved));e.restore(dict(zip((r[0] for r in updated['blocks']),updated['positions'])))
    for bad in [corrupt,altered,mismatch]:commands.append(f'FEEDBACK {bad}\n');capture()
    commands.append('RESTORE 0\n');e=engine(seed);capture()
    result=subprocess.run([str(binary),str(initial)],input=''.join(commands),text=True,capture_output=True,check=True)
    actual=[];buffer=[];statuses=[]
    for line in result.stdout.splitlines():
     if line=='END':actual.append(parse('\n'.join(buffer)));buffer=[]
     elif line in ['SAVED','UPDATED','REJECTED_FEEDBACK','RESTORED']:statuses.append(line)
     else:buffer.append(line)
    self.assertEqual(actual,expected,msg=f'seed {seed}')
    self.assertEqual(statuses,['SAVED','UPDATED',*(['REJECTED_FEEDBACK']*3),'RESTORED'])
if __name__=='__main__':unittest.main()
