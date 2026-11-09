"""Authenticate per-round retained old trees, not routing improvement evidence."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
M=R/'experiments/mmc_triangular_span_v9_2026-10-09/model'
D=R/'experiments/retained_old_tree_identity_v1_2026-10-09';assert not D.exists()
bindings=closure([Path(__file__)])
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
proof=load(M.parent/'verification.json');assert proof['complete_candidate_physical_and_events_pass']
for field in ('bindings','files'):
 for p,h in proof.get(field,{}).items():assert sha(p)==h;bindings[p]=h
initial=load(M/'initial.json');previous=load(M/'round0.json');final=load(M/'round1.json');receipt=load(M/'receipt.json')
floors={r['connection_id']:r for r in initial['records']}
frames=[initial,previous,final];indexes=[{r['connection_id']:r for r in f['records']} for f in frames]
groups=defaultdict(list)
for cid,r in floors.items():groups[r['net_id']].append(cid)
rows=[];counts=Counter()
for i,roundrow in enumerate(receipt['rounds']):
 for e in roundrow['events']:
  if e['status']!='RETAIN_BUDGET_OR_UNREACHABLE':continue
  net=e['net_id'];epoch=1 if i==0 else previous['epochs'][str(net)]
  assert epoch==e['old_epoch']==e['new_epoch']
  changed=[]
  for cid in groups[net]:
   old=indexes[i][cid];after=indexes[i+1][cid]
   assert old==after
   if old['answer']['physical_edge_ids']!=floors[cid]['answer']['physical_edge_ids']:changed.append(cid)
  counts['events']+=1;counts['old_tree_differs_from_initial_events']+=bool(changed);counts['different_connection_occurrences']+=len(changed)
  rows.append(dict(round=i,net_id=net,old_epoch=epoch,connection_occurrences=len(groups[net]),old_tree_differs_from_initial=bool(changed),different_connection_ids=changed))
assert counts['events']==2192 and all(sha(p)==h for p,h in bindings.items())
D.mkdir();f=D/'events.json';f.write_text(json.dumps(rows)+'\n');bindings[str(f)]=sha(f)
r=dict(bindings=bindings,all_retained_events_preserve_exact_old_records_and_epoch=True,counts=dict(counts),scope='Authenticated original event and frame identity only. Different from initial is not quality regression, candidate replacement gain or causal evidence.')
(D/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r['counts']))
