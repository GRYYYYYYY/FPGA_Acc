"""Real archived movements, immutable joint state and injected publication failures."""
import json,hashlib,shutil
from pathlib import Path
from collections import Counter
from dataclasses import replace
from prepared_csr import read
from pre_route_endpoints import sha
from incremental_channel_pressure import ChannelPressure
from move_prediction_transaction import MoveState,MovePredictionTransaction

root=Path(__file__).resolve().parents[1];base=root/'experiments';parent=base/'adder_tree_online_rc_budget_net_sequence_v2_2026-10-06';out=base/'adder_tree_whole_move_publication_2026-10-06';out.mkdir();(out/'sources').mkdir()
names=['audit_whole_move_publication.py','move_prediction_transaction.py','incremental_channel_pressure.py','prepared_csr.py','pre_route_endpoints.py']
for n in names:shutil.copyfile(root/'tools'/n,out/'sources'/n)
receipt=json.loads((parent/'receipt.json').read_text());verification=json.loads((parent/'verification.json').read_text());assert sha(parent/'receipt.json')==verification['receipt_sha256']
sequence=base/'adder_tree_2L032_move_sequence_2026-10-06';sp=json.loads((sequence/'protocol.json').read_text());graph=sp['inputs']['rr_graph'];prepared=base/'adder_tree_family_length_switch_csr_2026-10-06/adder_tree_2L_032bits/csr';m,f=read(prepared,graph['sha256']);context=hashlib.sha256((graph['sha256']+sha(prepared/'manifest.json')+sha(base/'adder_tree_family_exact_buffered_rc_classes_2026-10-06/adder_tree_2L_032bits/receipt.json')).encode()).hexdigest()
states=[]
for k in range(4):
 prediction=parent/f'step_{k}_prediction.json';assert sha(prediction)==receipt['steps'][k]['prediction_sha256'];p=json.loads(prediction.read_text());pressure=ChannelPressure(f['types'],f['capacities']);pressure.refresh(Counter({int(n):v for n,v in p['node_occupancy'].items()}),range(m['nodes']))
 placement=Path(sp['inputs']['reference_place']['path']) if k==0 else sequence/f'step_{k}.place';endpoints=base/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json' if k==0 else sequence/f'step_{k}_endpoints.json'
 states.append(MoveState(k,context,placement.read_bytes(),endpoints.read_bytes(),prediction.read_bytes(),(base/'adder_tree_online_move_rc_budgets_2026-10-06'/f'step_{k}_budgets.json').read_bytes(),pressure.payload(graph['sha256']).encode()))
tx=MovePredictionTransaction(states[0]);reports=[]
for expected in states[1:]:
 old=tx.snapshot();failures=[]
 for phase in ('placement','endpoints','prediction','budgets','pressure'):
  def build(current):
   values={}
   for name in ('placement','endpoints','prediction','budgets','pressure'):
    values[name]=getattr(expected,name)
    if name==phase:raise RuntimeError('injected '+phase)
   return replace(current,epoch=current.epoch+1,**values)
  status=tx.commit(old.epoch,build,lambda candidate:candidate==expected);assert status=='FAILED' and tx.snapshot() is old;failures.append(phase)
 assert tx.commit(old.epoch,lambda current:expected,lambda candidate:False)=='REJECTED' and tx.snapshot() is old
 assert tx.commit(old.epoch,lambda current:expected,lambda candidate:candidate==expected)=='COMMITTED';assert tx.snapshot() is expected
 assert tx.commit(old.epoch,lambda current:expected,lambda candidate:True)=='STALE' and tx.snapshot() is expected
 reports.append({'epoch':expected.epoch,'failure_phases_preserve_previous_snapshot':failures,'validation_rejection_preserves_previous':True,'success_publishes_all_payloads_together':True,'stale_request_preserves_new_snapshot':True,'payload_sha256':{n:hashlib.sha256(getattr(expected,n)).hexdigest() for n in ('placement','endpoints','prediction','budgets','pressure')}})
assert all(sha(root/'tools'/n)==sha(out/'sources'/n) for n in names)
(out/'receipt.json').write_text(json.dumps({'parent_verification_sha256':sha(parent/'verification.json'),'sources_sha256':{n:sha(out/'sources'/n) for n in names},'steps':reports,'scope':'Actual archived candidate bytes and joint memory-pointer publication with injected assembly/validation failures. Callback validates archived exact bytes; no online search-stage injection, external file atomicity, concurrent readers stress or native STA proof.'},indent=2)+'\n');print(json.dumps({'moves':3,'injected_failures':15,'validation_rejections':3,'successes':3,'stale_rejections':3}))
