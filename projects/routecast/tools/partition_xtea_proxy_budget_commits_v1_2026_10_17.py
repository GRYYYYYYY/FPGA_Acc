"""Describe actual commit changes by overflow delta; no counterfactual replay."""
import hashlib,json
from collections import Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_proxy_budget_commit_partition_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
bindings={str(Path(__file__).resolve()):sha(__file__)}
control=R/'experiments/xtea_continue_primary_audit_fixture_v1_2026-10-17/model';proxy=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model'
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
original={r['connection_id']:r['budget_integer'] for r in load(control/'initial.json')['records']};rows=[]
for method,model in [('control',control),('proxy',proxy)]:
 initial=load(model/'initial.json');receipt=load(model/'receipt.json');final=load(model/'sketch.json');state={r['connection_id']:r for r in initial['records']};epochs={r['net_id']:1 for r in state.values()}
 for rd in receipt['rounds']:
  counts=Counter();changed_net_ids={};extra_counts=Counter()
  for e in rd['events']:
   net=e['net_id'];assert e['old_epoch']==epochs[net]
   if e['status']!='COMMITTED':assert e['new_epoch']==epochs[net];counts['retained']+=1;continue
   records=e['records'];changes=sum(r['answer']['physical_edge_ids']!=state[r['connection_id']]['answer']['physical_edge_ids'] for r in records)
   delta=e['prospective_overflow_delta'];assert delta<=0
   key=('negative_overflow' if delta<0 else 'zero_overflow')+('/changed_paths' if changes else '/identical_paths')
   counts[key]+=1;counts[key+'/changed_connection_ops']+=changes
   if changes:changed_net_ids.setdefault(key,[]).append(net)
   extra=sum(r['answer']['delay']>original[r['connection_id']] for r in records)
   if extra:extra_counts[key+'/commits_with_new_allowance_users']+=1;extra_counts[key+'/new_allowance_connection_ops']+=extra
   for r in records:state[r['connection_id']]=r
   epochs[net]+=1;assert e['new_epoch']==epochs[net]
  rows.append(dict(method=method,round_index=rd['round_index'],event_count=len(rd['events']),counts=dict(counts),extra_allowance_counts=dict(extra_counts),changed_NETs_by_partition=changed_net_ids))
 assert state=={r['connection_id']:r for r in final['records']}
assert all(sha(k)==h for k,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all2896_events_per_method_and_final_states_replayed=True,rows=rows,scope='Observed transaction partition only. Repeated commits/connection operations, not distinct final users. Zero-overflow changed commits may improve the existing exact objective and are not inherently useless; withholding them changes future search/prices and requires a fresh audited experiment. No predicted quality or time effect.'),f,indent=2);f.write('\n')
print(json.dumps([{k:v for k,v in row.items() if k!='changed_NETs_by_partition'} for row in rows],indent=2))
