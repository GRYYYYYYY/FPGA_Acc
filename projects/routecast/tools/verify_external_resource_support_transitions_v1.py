"""Independent support-set intersections, all-ID table and phi/metric identity."""
import json,math
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prospective_external_family_resource_support_transitions_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 v=read(D/'verification.json');p=read(D/'protocol.json');assert v['status']=='ALL18_ALL_ID_RESOURCE_SUPPORT_TRANSITIONS_PREPARED'
 for r in [v,p]:assert all(sha(q)==h for q,h in r['bindings'].items())
 observed={(r['case'],r['method']):r for r in v['rows']};assert len(observed)==len(v['rows'])==18;bounded=E/'prospective_external_family_capacity_bounded_utilization_v1_2026-10-19/quality_summary.json';bsummary={r['case']:r for r in read(bounded)['rows']};bprotocol={r['case']:r for r in read(bounded.parent/'protocol.json')['cases']};bindings={str(q):sha(q) for q in [Path(__file__).resolve(),D/'verification.json',D/'protocol.json',bounded,bounded.parent/'protocol.json']};checks=0;identities=[]
 for spec in p['cases']:
  domain=Path(spec['domain_proof']);resources=[json.loads(s) for s in (domain.parent/'resources.jsonl').read_text().splitlines()];U={r['id'] for r in resources};assert len(U)==45584 and all(r['capacity']==1 for r in resources);native={int(n):x for n,x in read(spec['label_physical_audit'])['node_occupancy'].items()};T={n for n in U if native.get(n,0)>0};assert all(native.get(n,0) in (0,1) for n in U);frames={arm['name']:read(arm['frame']) for arm in spec['arms']};sets={name:{int(n) for n,x in frame['ledger'].items() if x>0}&U for name,frame in frames.items()};S=sets['previous_native'];table=D/spec['case']/'all_resource_transitions.jsonl';seen=set()
  for line in table.open():
   r=json.loads(line);n=r['id'];assert n in U and n not in seen;seen.add(n);assert r['prior']==int(n in S) and r['truth']==int(n in T);assert r['prediction_support']=={name:int(n in value) for name,value in sets.items()}
  assert seen==U
  for arm in spec['arms']:
   name=arm['name'];Q=sets[name];r=observed[spec['case'],name];cells={}
   for a in (0,1):
    for b in (0,1):
     for t in (0,1):cells[f'{a}{b}{t}']=len((S if a else U-S)&(Q if b else U-Q)&(T if t else U-T))
   assert r['transition_counts']==cells and sum(cells.values())==r['resources']==len(U);tp,fp,fn,tn=len(Q&T),len(Q-T),len(T-Q),len(U-(Q|T));den=(tp+fp)*(tp+fn)*(tn+fp)*(tn+fn);phi=(tp*tn-fp*fn)/math.sqrt(den) if den else None;assert r['confusion']==dict(TP=tp,FP=fp,FN=fn,TN=tn,binary_support_phi=phi);add=Q-S;remove=S-Q;at,af,rt,rf=len(add&T),len(add-T),len(remove&T),len(remove-T);assert (r['added_true_used'],r['added_true_unused'],r['removed_true_used'],r['removed_true_unused'])==(at,af,rt,rf);assert r['delta_TP']==tp-len(S&T)==at-rt and r['delta_FP']==fp-len(S-T)==af-rf;assert r['delta_correct']==at+rf-af-rt
   if name=='endpoint_local':
    assert bprotocol[spec['case']]['candidate_frame']==arm['frame'];rho=bsummary[spec['case']]['candidate_metrics']['resource']['spearman'];assert abs(phi-rho)<1e-12;identities.append(dict(case=spec['case'],binary_support_phi=phi,independent_bounded_head_resource_spearman=rho,delta_TP=r['delta_TP'],delta_FP=r['delta_FP']))
   if name=='previous_native':assert abs(phi-read(arm['comparison'])['metrics']['previous_native']['resource']['spearman'])<1e-12
   checks+=1
  bindings[str(table)]=sha(table)
 assert checks==18 and all(sha(q)==h for q,h in bindings.items());(D/'independent_verification_v1.json').write_text(json.dumps(dict(status='ALL18_ALL_ID_SUPPORT_TRANSITIONS_SET_RECONSTRUCTED_WITH_PHI_METRIC_IDENTITIES',checks=checks,all_ID_rows_verified=136752,bounded_head_identities=identities,bindings=bindings,scope='Error mechanism attribution on frozen exposed cases, no new model or acceptance criterion. Raw multiplicity and support are distinct; binary phi identity applies to bounded unit-capacity head.'),indent=2)+'\n');print('PASS',checks,json.dumps(identities))
if __name__=='__main__':main()
