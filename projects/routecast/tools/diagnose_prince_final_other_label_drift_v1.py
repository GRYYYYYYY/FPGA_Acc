"""Baseline final-label ownership versus intervened terminal route; not new legal truth if failed."""
import json
from collections import defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from evaluate_prince_ready_owner_forecast_v1 import final_owners
R=Path(__file__).resolve().parents[1];D=R/'experiments/prince_final_other_oracle_trial_v1_2026-10-20'
def main():
 pp=D/'protocol.json';vp=D/'verification.json';jobs=json.loads(pp.read_text())['jobs'];rows={x['case']:x for x in json.loads(vp.read_text())['rows']};bindings={str(p):sha(p) for p in [pp,vp,Path(__file__)]};results=[]
 for job in jobs:
  if job['mode']!='oracle':continue
  record=rows[job['case']];payload=Path(job['oracle_input']['payload']);assert sha(payload)==job['oracle_input']['sha256'];lines=payload.read_text().splitlines();assignment={int(node):int(code) for node,code in (line.split() for line in lines[8:])};old=defaultdict(set)
  for node,code in assignment.items():
   if code:old[code-1].add(node)
  route=Path(job['directory'])/'output.route';new=final_owners(route);inverse=defaultdict(set)
  for net,group in new.items():
   for node in group:inverse[node].add(net)
  changed=sum(new.get(net,set())!=old.get(net,set()) for net in old.keys()|new.keys());owner_changes=sum(inverse[node]!=({code-1} if code else set()) for node,code in assignment.items());unused_now_used=sum(code==0 and bool(inverse[node]) for node,code in assignment.items());same_count_new_owner=sum(code!=0 and len(inverse[node])==1 and inverse[node]!={code-1} for node,code in assignment.items());results.append(dict(case=job['case'],terminal_native_legal=record['native_full_check_pass'],NET_channel_union_changes=changed,CHANNEL_owner_set_changes=owner_changes,baseline_unused_CHANNELs_now_used=unused_now_used,occupied_CHANNELs_same_count_different_owner=same_count_new_owner));bindings[str(payload)]=sha(payload);bindings[str(route)]=sha(route)
 assert len(results)==6 and all(x['NET_channel_union_changes']>0 for x in results);(D/'factual_label_policy_drift_v1.json').write_text(json.dumps(dict(rows=results,bindings=bindings,interpretation='Exact final labels from baseline are not invariant under intervened routing policy. Terminal states of failed runs are diagnostic ownership, not legal future truth. This is not proof that lowered costs caused failure.'),indent=2)+'\n');print(json.dumps(results))
if __name__=='__main__':main()
