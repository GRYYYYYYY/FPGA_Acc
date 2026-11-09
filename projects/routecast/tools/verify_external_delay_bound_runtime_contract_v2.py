"""Float32 bound/gate replay and shared-SINK final flag reconciliation, all6 equivalence."""
import json,hashlib,struct,math
from pathlib import Path
from collections import defaultdict
import sys
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from verify_external_native_seed_feasibility_v1 import route_nodes
D=R/'experiments/prospective_external_family_native_delay_bound_contract_observer_v1_2026-10-19';B=R/'experiments/prospective_external_family_native_delay_bound_index_v1_2026-10-19'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(p.read_text())
def f32(x):return struct.unpack('f',struct.pack('f',float(x)))[0]
def main():
 v=read(D/'verification.json');assert all(sha(p)==h for p,h in v['bindings'].items());bindings={str(D/'verification.json'):sha(D/'verification.json'),str(Path(__file__).resolve()):sha(__file__)};results=[];examples=[]
 for i in (1,2,3):
  for arm in ('cold','seed'):
   case=f'w160/episode_{i:02d}/{arm}';out=D/case/'native';base=B/case/'native';a,b=read(out/'verification.json'),read(base/'verification.json');assert a['status']==b['status']=='FULL_PHYSICAL_AND_CANONICAL_PASS';assert all(a[k]==b[k] for k in ('wirelength','diagnostic_cpd_ns','iterations'));assert route_nodes(out/'output.route')==route_nodes(base/'output.route');assert all(sha(out/n)==sha(base/n) for n in ('initial_connections.tsv','first_iteration.route'))
   path=out/'delay_bound_calls.tsv';calls={};current=None
   for line in path.open():
    x=line.rstrip().split('\t')
    if x[0]=='H':
     call=int(x[1]);assert call not in calls;current=dict(maxcrit=f32(x[2]),ctol=f32(x[3]),dtol=f32(x[4]),stable=bool(int(x[5])),rows=[]);calls[call]=current
    else:
     assert x[0]=='P' and current is calls[int(x[1])];net,pin,sink=map(int,x[2:5]);bound,delay,crit=map(f32,x[5:8]);before=bool(int(x[8]));after=f32(x[9]);flag=bool(int(x[10]));assert pin>=1 and math.isfinite(bound) and bound>=0 and math.isfinite(delay) and delay>=0
     eligible=bound!=0 and delay>=bound and crit>=f32(current['maxcrit']*current['ctol']) and delay>=f32(bound*current['dtol'])
     expected_bound=bound if bound==0 else min(bound,delay);assert after==expected_bound,(case,call,net,pin,bound,delay,after,expected_bound)
     if bound==0 or delay<bound:assert crit==-1
     else:assert 0<=crit<=1
     current['rows'].append(dict(net=net,pin=pin,sink=sink,bound=bound,delay=delay,crit=crit,bound_after=after,eligible=eligible,final_flag=flag,flag_before=before))
   total=first=later=aliases=lost=eligible_count=0;cohort=None;call_summaries=[]
   for call,c in calls.items():
    rs=c['rows'];ids={(r['net'],r['pin']) for r in rs};assert len(ids)==len(rs);assert len(rs)==15970
    if cohort is None:cohort=ids
    assert ids==cohort;assert c['stable']==(not any(r['eligible'] for r in rs));groups=defaultdict(list)
    for r in rs:groups[r['net'],r['sink']].append(r)
    lost_now=0
    for key,gs in groups.items():
     assert all(r['final_flag']==gs[-1]['eligible'] for r in gs)
     if len(gs)>1:
      aliases+=1
      if any(r['eligible'] for r in gs) and not gs[-1]['final_flag']:
       lost+=1;lost_now+=1
       if len(examples)<18:examples.append(dict(case=case,call=call,net=key[0],sink=key[1],pins=gs))
    total+=len(rs);first+=sum(r['pin']==1 for r in rs);later+=sum(r['pin']>1 for r in rs);eligible_count+=sum(r['eligible'] for r in rs);call_summaries.append(dict(call=call,eligible_pins=sum(r['eligible'] for r in rs),final_true_unique_sink_flags=sum(gs[-1]['final_flag'] for gs in groups.values()),eligible_shared_sink_groups_with_false_final=lost_now))
   assert calls and first and later
   bindings[str(path)]=sha(path);bindings[str(out/'verification.json')]=sha(out/'verification.json');bindings[str(base/'verification.json')]=sha(base/'verification.json');results.append(dict(case=case,exact_corrected_baseline_final_equivalent=True,force_calls=len(calls),pin_records=total,first_sink_records=first,later_sink_records=later,shared_sink_group_calls=aliases,shared_sink_contract_covered=aliases>0,eligible_pins=eligible_count,eligible_shared_sink_groups_with_false_final=lost,call_summaries=call_summaries));print(json.dumps({k:v for k,v in results[-1].items() if k!='call_summaries'}),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'runtime_contract_verification_v2.json').write_text(json.dumps(dict(status='ALL6_OWN_PIN_BOUNDS_GATES_AND_OUTPUT_EQUIVALENCE_REPLAYED_ALIAS_COVERAGE_REPORTED',rows=results,shared_sink_overwrite_examples=examples,bindings=bindings,limitations='Shared-SINK coverage requires nonzero shared_sink_group_calls; absence is not a passed alias fixture. v1 incorrectly required aliases in every actual case and failed its coverage assertion; original native runs unchanged. Replays actual function call inputs/outputs, not skipped force calls or inner connection search. Own-index correction and shared-SINK last-writer semantics distinguished. Shared flag loss not automatically a cause of QoR regression.'),indent=2)+'\n')
if __name__=='__main__':main()
