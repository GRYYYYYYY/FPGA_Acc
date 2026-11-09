"""Exact owner deltas before round2 NET2, all resources and all3 cases."""
import json,sys
from pathlib import Path
from collections import defaultdict,Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from analyze_external_early_net_response_v1 import load
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19';P=E/'prospective_external_family_temporal_prior_errors_v1_2026-10-19';D=E/'prospective_external_family_net85_net2_pressure_handoff_v2_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def owners(trace):
 first=defaultdict(set);current=defaultdict(set)
 for (it,net),r in trace.items():
  if it!=1:continue
  for n in r['A']:first[n].add(net)
 for n,ns in first.items():current[n]=set(ns)
 for n in trace[2,85]['B']:current[n].remove(85)
 for n in trace[2,85]['A']:current[n].add(85)
 assert trace[2,85]['order']==0 and trace[2,2]['order']==1
 for n,(occ,acc,pres) in trace[2,2]['B'].items():assert occ==len(current[n]) and acc==1 and pres==1+.5*occ
 return first,current

def main():
 receipt=read(I/'all_case_early_trace_verification_v1.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());D.mkdir(exist_ok=False);bindings={str(I/'all_case_early_trace_verification_v1.json'):sha(I/'all_case_early_trace_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};old=load(I/'source/early_net_trace.tsv');oldfirst,oldcurrent=owners(old);rows=[]
 for c in read(I/'target_manifest.json')['cases']:
  case=c['case'];new=load(I/case/'early_net_trace.tsv');newfirst,newcurrent=owners(new);classes={r['net_id']:bool(r['edit_mask']) for r in read(P/case/'NETs.json')};assert classes[85] and not classes[2];assert old[2,2]['B'].keys()==new[2,2]['B'].keys();assert old[2,2]['C']==new[2,2]['C'];resources=oldfirst.keys()|oldcurrent.keys()|newfirst.keys()|newcurrent.keys();net2=set(old[2,2]['B']);records=[]
  for n in sorted(resources):
   a,b=oldcurrent.get(n,set()),newcurrent.get(n,set());previous=len(newfirst.get(n,set()))-len(oldfirst.get(n,set()));net85_prior=int(85 in newfirst.get(n,set()))-int(85 in oldfirst.get(n,set()));net85_current=int(85 in b)-int(85 in a);net85_step=net85_current-net85_prior;other_edited=sum(int(x in b)-int(x in a) for x in (a|b)-{85} if classes[x]);other_clean=sum(int(x in b)-int(x in a) for x in (a|b)-{85} if not classes[x]);delta=len(b)-len(a);assert delta==net85_current+other_edited+other_clean==previous+net85_step
   records.append(dict(id=n,on_NET2_prior_support=n in net2,source_owners=sorted(a),target_owners=sorted(b),source_first_owners=sorted(oldfirst.get(n,set())),target_first_owners=sorted(newfirst.get(n,set())),occupancy_delta=delta,prior_round_delta=previous,NET85_prior_delta=net85_prior,NET85_current_delta=net85_current,NET85_step_delta=net85_step,other_edited_delta=other_edited,other_clean_delta=other_clean))
  selected=[r for r in records if r['on_NET2_prior_support'] and r['occupancy_delta']];row=dict(case=case,all_observed_CHANNEL_resources=len(records),NET2_prior_support=len(net2),NET2_occupancy_changed_resources=len(selected),NET2_change_with_NET85_current_contribution=sum(r['NET85_current_delta']!=0 for r in selected),NET2_change_NET85_current_only=sum(r['NET85_current_delta']==r['occupancy_delta'] and r['other_edited_delta']==r['other_clean_delta']==0 for r in selected),NET2_change_with_NET85_new_step_contribution=sum(r['NET85_step_delta']!=0 for r in selected),NET2_change_with_prior_round_delta=sum(r['prior_round_delta']!=0 for r in selected),NET2_change_with_other_clean_delta=sum(r['other_clean_delta']!=0 for r in selected),changed_NET2_rows=selected);rows.append(row);out=D/case;out.mkdir(parents=True)
  with (out/'all_resource_owner_deltas.jsonl').open('x') as f:
   for r in records:f.write(json.dumps(r)+'\n')
  for p in [out/'all_resource_owner_deltas.jsonl',I/case/'early_net_trace.tsv',P/case/'NETs.json']:bindings[str(p)]=sha(p)
  print(json.dumps({k:v for k,v in row.items() if k!='changed_NET2_rows'}),flush=True)
 bindings[str(I/'source/early_net_trace.tsv')]=sha(I/'source/early_net_trace.tsv');assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_EXACT_PRE_NET2_OWNER_REPLAY_AND_NET85_PRIOR_CURRENT_STEP_DECOMPOSITION_COMPLETE',rows=rows,bindings=bindings,scope='Algebraic observed ownership decomposition, no native counterfactual. Signed contributions can cancel. NET85 current owner contribution differs from its round2 change; both retained. No inference labels used, no causal necessity/quality claim.'),indent=2)+'\n')
if __name__=='__main__':main()
