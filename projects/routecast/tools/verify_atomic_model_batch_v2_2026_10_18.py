"""CAS rejection/nonmutation, stale/foreign/replayed tickets and epoch fixtures."""
import json,copy,hashlib
from pathlib import Path
from atomic_model_batch_v2 import State
R=Path(__file__).resolve().parents[1]
out=R/'experiments/atomic_model_batch_core_v2_2026-10-18';out.mkdir()
frame=dict(epochs={'7':2,'8':4},records=[dict(connection_id=1,net_id=7,budget_integer=10,answer={'delay':3})])
state=State(frame);digest=state.digest;rejections=0
def valid(s):
 s['records'][0]['answer']['delay']=4;s['epochs']['7']=3
 return s,dict(physical_admission='caller fixture')
def reject(call):
 global rejections
 before=state.snapshot();d=state.digest
 try:call()
 except ValueError:pass
 else:raise AssertionError('rejection missing')
 assert state.snapshot()==before and state.digest==d;rejections+=1
reject(lambda:state.prepare('bad',{'7':2},valid))
reject(lambda:state.prepare(digest,{'7':1},valid))
reject(lambda:state.prepare(digest,{},valid))
for kind in ['metadata','duplicate','epoch_missing','epoch_double','unrelated_epoch','no_change','exception']:
 def invalid(s,kind=kind):
  if kind=='exception':s['records'].clear();raise ValueError('injected validator failure')
  s,_=valid(s)
  if kind=='metadata':s['records'][0]['budget_integer']=11
  if kind=='duplicate':s['records'].append(copy.deepcopy(s['records'][0]))
  if kind=='epoch_missing':s['epochs']['7']=2
  if kind=='epoch_double':s['epochs']['7']=4
  if kind=='unrelated_epoch':s['epochs']['8']=5
  if kind=='no_change':s=copy.deepcopy(frame)
  return s,{}
 reject(lambda:state.prepare(digest,{'7':2},invalid))
t1=state.prepare(digest,{'7':2},valid);t2=state.prepare(digest,{'7':2},valid)
foreign=State(frame).prepare(digest,{'7':2},valid)
reject(lambda:state.commit(foreign));reject(lambda:state.commit(object()))
copy_out=state.snapshot();copy_out['records'].clear();assert state.snapshot()==frame
result=state.commit(t1);assert state.snapshot()['epochs']=={'7':3,'8':4} and result['generation']==1
reject(lambda:state.commit(t1));reject(lambda:state.commit(t2));reject(lambda:state.prepare(digest,{'7':2},valid))
frame['records'].clear();assert len(state.snapshot()['records'])==1
roundtrip=State(dict(epochs={'7':2,'8':4},records=[dict(connection_id=1,net_id=7,budget_integer=10,answer={'delay':3})],ledger={2:1,10:2}))
assert State(roundtrip.snapshot()).digest==roundtrip.digest
rt=roundtrip.prepare(roundtrip.digest,{'7':2},valid);roundtrip.commit(rt)
assert State(roundtrip.snapshot()).digest==roundtrip.digest
paths=[Path(__file__),R/'tools/atomic_model_batch_v2.py']
with (out/'verification.json').open('x') as f:json.dump(dict(status='pass',rejection_fixtures=rejections,bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in paths},scope='Serial JSON CAS semantics; physical/ledger/objective validation belongs to transition caller, not this layer.'),f,indent=2)
print('ATOMIC MODEL CORE PASS',rejections,flush=True)
