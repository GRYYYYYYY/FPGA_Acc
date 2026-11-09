"""A score projection cannot masquerade as unchanged NET-owned physical state."""
import json,struct
from pathlib import Path
from pre_route_endpoints import sha
from owner_conditioned_pressure_v2 import Snapshot,PHASE
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_owned_ready_trial_v1_2026-10-20'
def main():
 p=D/'pressure_input_bridge_verification_v1.json';v=json.loads(p.read_text());bindings={str(p):sha(p),str(Path(__file__)):sha(__file__),str(R/'tools/owner_conditioned_pressure_v2.py'):sha(R/'tools/owner_conditioned_pressure_v2.py)};rows=[];rejected=0;unchanged=0
 for row in v['rows']:
  case=row['case'];i=row['iteration'];d=D/case/'capture';op=d/'owners'/f'owners_{i}.bin';raw=op.read_bytes();_,count=struct.unpack_from('<QQ',raw,8);offset=24;owners={}
  for _ in range(count):
   net,endpoint,n=struct.unpack_from('<QQQ',raw,offset);offset+=24;owners[net]=frozenset(struct.unpack_from('<'+'Q'*n,raw,offset));offset+=n*8
  rp=d/'boundary'/f'iteration_{i}.bin';data=rp.read_bytes();caps={};occ={}
  for n,kind,c,capacity,bits in struct.iter_unpack('<QIiiI',data[24:]):
   if kind in [4,5]:caps[n]=capacity;occ[n]=c
  projected={n:min(c,caps[n]) for n,c in occ.items()};pres=list(map(int,(d/'callback.tsv.owners.tsv').read_text().splitlines()[i-1].split()))[-1];identity=(case,i,PHASE);changed=sum(projected[n]!=occ[n] for n in occ)
  if changed:
   try:Snapshot(identity,caps,projected,owners,pres)
   except ValueError as exc:assert str(exc)=='uniqueNET owner/count mismatch';rejected+=1
   else:raise AssertionError('projected scalar counts admitted with unchanged physical owners')
  else:Snapshot(identity,caps,projected,owners,pres);unchanged+=1
  rows.append(dict(case=case,iteration=i,changed_CHANNEL_counts=changed,rejected_as_inconsistent_owner_state=bool(changed)));bindings[str(op)]=sha(op);bindings[str(rp)]=sha(rp)
 assert rejected+unchanged==33 and rejected>0;assert all(sha(p)==h for p,h in bindings.items());(D/'projected_owner_state_rejection_v1.json').write_text(json.dumps(dict(rows=rows,rejected_changed_score_projections=rejected,accepted_unchanged_capacity_feasible_states=unchanged,bindings=bindings,scope='Real copied owner/occupancy inputs: clipping counts without changing NET ownership is rejected if any count changes. Unchanged feasible snapshots stay admissible. This protects physical-state identity, not score-forecast evaluation: projected scores remain valid as separate forecast quantities, not physical ledgers.'),indent=2)+'\n');print('PROJECTED_OWNER_STATE_CONTRACT',rejected,unchanged)
if __name__=='__main__':main()
