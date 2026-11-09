import random,unittest
from terminal_capacity_gate import terminal_cut,commit_with_terminal_preflight
from move_prediction_transaction import MoveState,MovePredictionTransaction
class TestGate(unittest.TestCase):
 def test_exhaustive_assignment_reference(self):
  rng=random.Random(21)
  for _ in range(100):
   caps={p:rng.randrange(3) for p in range(4)};options=[{p for p in caps if rng.randrange(2)} for n in range(rng.randrange(1,7))]
   def assign(i,used):
    if i==len(options):return True
    for p in options[i]:
     if used.get(p,0)<caps[p]:
      used[p]=used.get(p,0)+1
      if assign(i+1,used):return True
      used[p]-=1
    return False
   self.assertEqual(terminal_cut(enumerate(options),caps)['status']=='INFEASIBLE',not assign(0,{}))
 def test_preflight_and_unknown(self):
  s=MoveState(0,'a'*64,b'p',b'e',b'r',b'b',b'o');tx=MovePredictionTransaction(s);calls=[]
  def build(old):calls.append(1);return MoveState(1,old.context,b'p',b'e',b'r',b'b',b'o')
  self.assertEqual(commit_with_terminal_preflight(tx,0,lambda old:terminal_cut([(0,{1}),(1,{1})],{1:1}),build,lambda s:True),'INFEASIBLE');self.assertIs(tx.snapshot(),s);self.assertEqual(calls,[])
  self.assertEqual(commit_with_terminal_preflight(tx,0,lambda old:terminal_cut([(0,{1}),(1,{1})],{1:1},1),build,lambda s:False),'REJECTED');self.assertIs(tx.snapshot(),s);self.assertEqual(calls,[1])
  self.assertEqual(commit_with_terminal_preflight(tx,1,lambda old:None,build,lambda s:True),'STALE')
 def test_invalid_inputs(self):
  for obligations,caps in [([(0,{1}),(0,{2})],{1:1,2:1}),([(0,{True})],{True:1}),([(0,{1})],{1:True})]:
   with self.assertRaises(ValueError):terminal_cut(obligations,caps)
