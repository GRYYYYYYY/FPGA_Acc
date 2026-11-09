import subprocess,tempfile,unittest
from pathlib import Path
from pack_snapshot import pack
from strict_snapshot_codec import encode
from test_constrained_proposals import engine
from compare_proposals import payload,parse
from native_adapter import color_payload
ROOT=Path(__file__).resolve().parent
class FlatProposalTest(unittest.TestCase):
 def test_candidates_and_forbidden_colors(self):
  with tempfile.TemporaryDirectory() as directory:
   d=Path(directory);binary=d/'query';snapshot=d/'snapshot.bin'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'flat_proposal_query.cpp'),'-o',str(binary)],check=True)
   for seed in range(12):
    e=engine(seed);records,_=pack(e);snapshot.write_bytes(encode(records))
    occupied={p:id for id,p in e.positions.items()}
    for index,u in enumerate(e.units):
     expected=sorted((t.transaction_id,t.score_q20) for t in e._transactions_for_unit(u,occupied))
     result=subprocess.run([str(binary),str(snapshot)],input=payload(e,index),text=True,capture_output=True,check=True)
     self.assertEqual(parse(result.stdout),expected)
    for color in range(4):
     first,_=e.propose_color(color);forbidden={first[0].transaction_id} if first else set()
     reference,_=e.propose_color(color,forbidden)
     result=subprocess.run([str(binary),str(snapshot),'--color'],input=color_payload(e,color,forbidden),text=True,capture_output=True,check=True)
     self.assertEqual(parse(result.stdout),sorted((t.transaction_id,t.score_q20) for t in reference))
if __name__=='__main__':unittest.main()
