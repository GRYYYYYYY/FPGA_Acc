"""Count exact old-list comparisons implied by authenticated complete trace."""
import json,sys
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/ultraembedded_mmc_actual_old_linear_fraction_cache_workflow_v12_2026-10-10'
vp=D/'verification.json';v=json.loads(vp.read_text());assert v['all_cases_both_complete_arms_authenticated']
model=D/'seed/model/mmc';proof_path=model/'verification.json';p=json.loads(proof_path.read_text());assert v['bindings'][str(proof_path)]==sha(proof_path)
assert p['complete_atomic_NET_replay_epochs_affected_schedule_priceupdates_and_full_rebuild_pass']
rp=model/'receipt.json';r=json.loads(rp.read_text());assert v['bindings'][str(rp)]==sha(rp)
initial=model/'initial.json';assert r['files'][str(initial)]==sha(initial)
groups=defaultdict(list)
for rec in json.loads(initial.read_text())['records']:groups[rec['net_id']].append(rec)
rows=[];rounds=[]
for roundrow in r['rounds']:
 scans=lookups=skipped=0
 for event in roundrow['events']:
  old=groups[event['net_id']];positions={x['connection_id']:i+1 for i,x in enumerate(old)};assert len(positions)==len(old)
  excluded={x['connection_id'] for x in event.get('primary_attempts',[]) if x['physical_edge_ids'] is None}
  count=sum(position for q,position in positions.items() if q not in excluded)
  requested=len(old)-len(excluded);scans+=count;lookups+=requested;skipped+=len(excluded)
  rows.append(dict(round_index=roundrow['round_index'],net_id=event['net_id'],connections=len(old),budget_lookups=requested,list_comparisons=count))
  if event['status']=='COMMITTED':
   new=event['records'];assert {x['connection_id'] for x in new}==set(positions);groups[event['net_id']]=new
 rounds.append(dict(round_index=roundrow['round_index'],affected_nets=len(roundrow['events']),budget_lookups=lookups,list_comparisons=scans,not_settled_short_circuit_queries=skipped))
assert sum(x['affected_nets'] for x in rounds)==p['events']
O=R/'experiments/mmc_old_budget_lookup_work_v1_2026-10-10';O.mkdir()
out=dict(bindings={**closure([Path(__file__),R/'tools/run_resident_actual_old_joint_fallback_linear_v11.py']),str(vp):sha(vp),str(proof_path):sha(proof_path),str(rp):sha(rp),str(initial):sha(initial)},rounds=rounds,total_list_comparisons=sum(x['list_comparisons'] for x in rounds),total_budget_lookups=sum(x['budget_lookups'] for x in rounds),largest_events=sorted(rows,key=lambda x:x['list_comparisons'],reverse=True)[:20],scope='Exact comparison count implied by original next(old record ID) lookup and complete authenticated actual-old trace. No measured CPU instruction/time profile or realized indexed-model gain. Only that lookup is counted, not other path search, fallback, audits or total workflow cost.')
(O/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','largest_events']},indent=2))
