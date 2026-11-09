"""Ensure C++ selects candidates and produces exact statistics without Python enumeration."""
import subprocess,tempfile,unittest
from pathlib import Path
from test_constrained_proposals import engine
from compare_proposals import payload
from fast_adapter import FastCppEngine
ROOT=Path(__file__).resolve().parent

class FastAdapterTest(unittest.TestCase):
 def test_no_python_candidate_enumeration(self):
  with tempfile.TemporaryDirectory() as directory:
   binary=Path(directory)/'server'
   subprocess.run(['g++','-std=c++17','-O2','-Wall','-Wextra','-Werror',str(ROOT/'state_server_fast.cpp'),'-o',str(binary)],check=True)
   for seed in range(4):
    reference=engine(seed);fast=FastCppEngine.__new__(FastCppEngine)
    fast.__dict__.update(reference.__dict__);fast._net_cost_cache={};fast.checks=[]
    fast._server=subprocess.Popen([str(binary)],stdin=subprocess.PIPE,stdout=subprocess.PIPE,text=True)
    def forbidden_enumeration(*args):raise AssertionError('Python candidate enumeration invoked')
    fast._transactions_for_unit=forbidden_enumeration
    try:
     fast._send(payload(fast,0)+' '.join(map(str,[len(fast.focus_blocks),*sorted(fast.focus_blocks)])))
     self.assertEqual(fast._line(),'READY')
     for color in range(4):
      first,_=reference.propose_color(color);forbidden={first[0].transaction_id} if first else set()
      expected,stats=reference.propose_color(color,forbidden)
      actual,actual_stats=fast.propose_color(color,forbidden)
      self.assertEqual([t.audit() for t in actual],[t.audit() for t in expected])
      self.assertEqual(actual_stats,stats)
    finally:
     fast.close()
     fast._server.stdin.close()
     fast._server.stdout.close()

if __name__=='__main__':unittest.main()
