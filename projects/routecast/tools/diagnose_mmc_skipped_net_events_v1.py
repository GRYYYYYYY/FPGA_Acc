"""Full event census for NETs omitted by the historical affected schedule."""
import collections,datetime,hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];O=R/'experiments/mmc_full_schedule_control_recovery_v1_2026-10-12';A=R/'experiments/mmc_multiplicative_feedback_trial_v1_2026-10-10/model'
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
bindings={str(Path(__file__).resolve()):sha(Path(__file__).resolve())}
def read(p):
 bindings[str(p)]=sha(p);return json.loads(p.read_text())
proof=read(O/'schedule_comparison_v1.json')
for p,h in proof['bindings'].items():assert sha(p)==h,p;bindings[p]=h
ar=read(A/'receipt.json');fr=read(O/'model/receipt.json');frame=read(O/'model/round0.json')
assert ar['rounds'][1]['changed_nodes']==fr['rounds'][1]['changed_nodes']
affected=set(ar['rounds'][1]['affected_nets']);old={}
for x in frame['records']:old.setdefault(x['net_id'],{})[x['connection_id']]=x
counts=collections.Counter();rows=[];prior_changes=0
for index,e in enumerate(fr['rounds'][1]['events']):
 net=e['net_id'];committed=e['status']=='COMMITTED';new={x['connection_id']:x for x in e.get('records',[])} if committed else old[net]
 assert new.keys()==old[net].keys()
 changed=[cid for cid,x in new.items() if x['answer']['physical_edge_ids']!=old[net][cid]['answer']['physical_edge_ids']]
 if net not in affected:
  counts['nets']+=1;counts[e['status']]+=1;counts['changed_nets']+=bool(changed);counts['changed_connections']+=len(changed)
  if changed:
   rows.append({'net_id':net,'event_index':index,'prior_path_changing_commits':prior_changes,'changed_connection_ids':changed,'prospective_overflow_delta':e['prospective_overflow_delta']})
 if changed:prior_changes+=1
assert counts['nets']==35940
assert all(sha(p)==h for p,h in bindings.items())
out={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'bindings':bindings,'same_round1_changed_node_map':True,'skipped_net_census':dict(counts),'changed_skipped_events':rows,'full_round1_path_changing_commits':prior_changes,'scope':'Complete audited event census, relative to common round0. Earlier path-changing commits are counted, not proof of occupancy snapshot inequality or causality. Distinguishing frozen-state schedule omission from intervening state evolution requires a controlled per-NET replay. No new speed or quality claim.'}
p=O/'skipped_net_event_diagnosis_v1.json';assert not p.exists();p.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'counts':dict(counts),'first_changed_skipped_events':rows[:5]},indent=2))
