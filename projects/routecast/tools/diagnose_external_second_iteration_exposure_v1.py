"""All-cleanNET second-pass divergence partition, no fitting or final-label use."""
import json,csv,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
from analyze_external_iteration_support_propagation_v1 import snapshots
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_iteration_support_observer_v1_2026-10-19';P=E/'prospective_external_family_temporal_prior_errors_v1_2026-10-19';D=E/'prospective_external_family_second_iteration_exposure_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def initial(path):
 with path.open() as f:return {(int(r['net']),int(r['pin'])):r for r in csv.DictReader(f,delimiter='\t')}
def main():
 receipt=read(I/'all_case_trace_verification_v1.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());D.mkdir(exist_ok=False);bindings={str(I/'all_case_trace_verification_v1.json'):sha(I/'all_case_trace_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};source=list(x for _,x in __import__('itertools').islice(snapshots(I/'source/iteration_support.tsv'),2));assert len(source)==2;oldcrit=initial(I/'source/initial_connections.tsv');rows=[]
 for c in read(I/'target_manifest.json')['cases']:
  case=c['case'];target=list(x for _,x in __import__('itertools').islice(snapshots(I/case/'iteration_support.tsv'),2));clean={r['net_id'] for r in read(P/case/'NETs.json') if not r['edit_mask']};a,b=source[0],target[0];demand_a=Counter(x for ns in a.values() for x in ns);demand_b=Counter(x for ns in b.values() for x in ns);delta={x for x in demand_a.keys()|demand_b.keys() if demand_a[x]!=demand_b[x]};boolean={x for x in delta if (demand_a[x]>1)!=(demand_b[x]>1)};newcrit=initial(I/case/'initial_connections.tsv');changedcrit={net for (net,pin),q in oldcrit.items() if float(q['criticality'])!=float(newcrit[net,pin]['criticality'])};counts=Counter();records=[]
  for net in sorted(clean):
   first_diff=a[net]!=b[net];second_diff=source[1][net]!=target[1][net];count_exposed=bool((a[net]|b[net])&delta);overuse_exposed=bool((a[net]|b[net])&boolean);crit_changed=net in changedcrit;key=(first_diff,second_diff,count_exposed,overuse_exposed,crit_changed);counts[key]+=1;records.append(dict(net_id=net,first_support_diff=first_diff,second_support_diff=second_diff,first_demand_difference_exposed=count_exposed,first_boolean_overuse_difference_exposed=overuse_exposed,initial_criticality_changed=crit_changed))
  out=D/case;out.mkdir(parents=True);rp=out/'all_clean_NETs.json';rp.write_text(json.dumps(records,indent=2)+'\n');new=[r for r in records if not r['first_support_diff'] and r['second_support_diff']];row=dict(case=case,clean_NETs=len(clean),first_demand_different_resources=len(delta),first_boolean_overuse_different_resources=len(boolean),new_second_round_divergences=len(new),new_count_exposed=sum(r['first_demand_difference_exposed'] for r in new),new_initial_criticality_changed=sum(r['initial_criticality_changed'] for r in new),new_either_exposed=sum(r['first_demand_difference_exposed'] or r['initial_criticality_changed'] for r in new),cells=[dict(first_diff=k[0],second_diff=k[1],count_exposed=k[2],boolean_exposed=k[3],initial_criticality_changed=k[4],count=v) for k,v in sorted(counts.items())]);rows.append(row)
  for p in [rp,I/case/'iteration_support.tsv',I/case/'initial_connections.tsv',P/case/'NETs.json']:bindings[str(p)]=sha(p)
  print(json.dumps({k:v for k,v in row.items() if k!='cells'}),flush=True)
 for p in [I/'source/iteration_support.tsv',I/'source/initial_connections.tsv']:bindings[str(p)]=sha(p)
 assert all(sha(p)==h for p,h in bindings.items());(D/'summary.json').write_text(json.dumps(dict(status='ALL3_ALL_CLEAN_NETS_FULL_DEMAND_AND_INITIAL_CRITICALITY_EXPOSURE_PARTITIONED',rows=rows,bindings=bindings,scope='Only baseline boundary exposure, not runtime full cost: first iteration history increment is zero; next present factor .5. Counts omit nonCHANNEL/nonconfigurable group effects and within-round occupancy changes, and initial criticality precedes first-route STA refresh. No causal/quality claim.'),indent=2)+'\n')
if __name__=='__main__':main()
