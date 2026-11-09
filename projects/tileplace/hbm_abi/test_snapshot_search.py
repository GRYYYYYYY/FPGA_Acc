import subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from strict_snapshot_codec import encode
from test_constrained_proposals import engine
from compare_proposals import parse
ROOT=Path(__file__).resolve().parent

def query(e,selector,color,forbidden=()):
 c=e.config;rows=[f'{selector} {int(color)} {c.page_width} {c.page_height} {c.candidate_limit} {c.chain_candidate_limit} {c.timing_weight} {c.routed_timing_weight} {c.congestion_weight}',str(len(e.guarded))]
 rows.extend(f'{a} {b} {d+c.critical_distance_slack}' for a,b,_,d in e.guarded)
 rows.append(str(len(forbidden)))
 for kind,units,trial in sorted(forbidden):
  rows.append(f'{kind} {len(units)}')
  rows.extend(' '.join(map(str,(len(u),*u))) for u in units)
  rows.append(str(len(trial)))
  rows.extend(' '.join(map(str,(id,*p))) for id,p in trial)
 return '\n'.join(rows)+'\n'
class SnapshotSearchTest(unittest.TestCase):
 def test_binary_metadata_candidates(self):
  with tempfile.TemporaryDirectory() as directory:
   d=Path(directory);binary=d/'query';snapshot=d/'snapshot.bin'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'snapshot_search_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    e=engine(seed);records,_=pack(e);snapshot.write_bytes(encode(records))
    occupied={p:id for id,p in e.positions.items()}
    for index,u in enumerate(e.units):
     expected=sorted((t.transaction_id,t.score_q20) for t in e._transactions_for_unit(u,occupied))
     result=subprocess.run([str(binary),str(snapshot)],input=query(e,index,False),text=True,capture_output=True,check=True)
     self.assertEqual(parse(result.stdout),expected)
    for color in range(4):
     first,_=e.propose_color(color);forbidden={first[0].transaction_id} if first else set()
     reference,_=e.propose_color(color,forbidden)
     result=subprocess.run([str(binary),str(snapshot)],input=query(e,color,True,forbidden),text=True,capture_output=True,check=True)
     self.assertEqual(parse(result.stdout),sorted((t.transaction_id,t.score_q20) for t in reference))
if __name__=='__main__':unittest.main()
