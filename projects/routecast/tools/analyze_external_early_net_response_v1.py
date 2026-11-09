"""All cleanNET runtime input differences, not label-conditioned selection."""
import json,sys
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19';P=E/'prospective_external_family_temporal_prior_errors_v1_2026-10-19';D=E/'prospective_external_family_early_net_response_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def load(path):
 result={}
 for line in path.open():
  x=line.split();kind=x[0];it,order,net=map(int,x[1:4]);r=result.setdefault((it,net),dict(order=order,C={}))
  assert r['order']==order
  if kind=='C':
   pin=int(x[4]);assert pin not in r['C'];r['C'][pin]=(float(x[5]),float(x[6]))
  else:
   assert kind not in r;nodes={}
   for item in x[6:]:
    n,occ,acc,pres=item.split(':');nodes[int(n)]=(int(occ),float(acc),float(pres))
   assert len(nodes)==int(x[5]);r[kind]=nodes
 return result

def main():
 audit=read(I/'all_case_early_trace_verification_v1.json');assert len(audit['rows'])==4 and all(sha(p)==h for p,h in audit['bindings'].items());equiv=read(I/'all_case_verification_v1.json');assert all(r['final_route_identical'] for r in equiv['rows']);D.mkdir(exist_ok=False);bindings={str(I/'all_case_early_trace_verification_v1.json'):sha(I/'all_case_early_trace_verification_v1.json'),str(I/'all_case_verification_v1.json'):sha(I/'all_case_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};old=load(I/'source/early_net_trace.tsv');summaries=[]
 for c in read(I/'target_manifest.json')['cases']:
  case=c['case'];new=load(I/case/'early_net_trace.tsv');assert old.keys()==new.keys();clean={r['net_id'] for r in read(P/case/'NETs.json') if not r['edit_mask']};records=[]
  for (it,net),a in sorted(old.items()):
   if net not in clean:continue
   b=new[it,net];assert a['order']==b['order'] and a['C'].keys()==b['C'].keys();shared=a['B'].keys()&b['B'].keys();fields={}
   for index,name in enumerate(['occupancy_changed','history_changed','present_changed']):fields[name]=any(a['B'][n][index]!=b['B'][n][index] for n in shared)
   r=dict(iteration=it,net_id=net,order=a['order'],before_support_diff=a['B'].keys()!=b['B'].keys(),after_support_diff=a['A'].keys()!=b['A'].keys(),delay_changed=any(a['C'][p][0]!=b['C'][p][0] for p in a['C']),criticality_changed=any(a['C'][p][1]!=b['C'][p][1] for p in a['C']),**fields);r['new_divergence']=not r['before_support_diff'] and r['after_support_diff'];records.append(r)
  out=D/case;out.mkdir(parents=True);rp=out/'all_clean_NET_observations.json';rp.write_text(json.dumps(records,indent=2)+'\n');per=[]
  flags=['occupancy_changed','history_changed','present_changed','delay_changed','criticality_changed']
  for it in (1,2,3):
   group=[r for r in records if r['iteration']==it];fresh=[r for r in group if r['new_divergence']];cells=Counter(tuple(r[k] for k in ['before_support_diff','after_support_diff']+flags) for r in group);per.append(dict(iteration=it,all_clean_NETs=len(group),new_divergences=len(fresh),new_with_each_flag={k:sum(r[k] for r in fresh) for k in flags},new_any_observed_input_changed=sum(any(r[k] for k in flags) for r in fresh),new_no_observed_input_changed=sum(not any(r[k] for k in flags) for r in fresh),first_new_order=min((r['order'] for r in fresh),default=None),cells=[dict(values=list(k),count=v) for k,v in sorted(cells.items())]))
  row=dict(case=case,rounds=per);summaries.append(row)
  for p in [rp,I/case/'early_net_trace.tsv',P/case/'NETs.json']:bindings[str(p)]=sha(p)
  print(json.dumps(dict(case=case,rounds=[{k:v for k,v in r.items() if k!='cells'} for r in per])),flush=True)
 bindings[str(I/'source/early_net_trace.tsv')]=sha(I/'source/early_net_trace.tsv');assert all(sha(p)==h for p,h in bindings.items());(D/'summary.json').write_text(json.dumps(dict(status='ALL3_ALL_CLEAN_NETS_FIRST3_RUNTIME_INPUT_RESPONSE_PARTITIONED',rows=summaries,bindings=bindings,flag_order=['before_support_diff','after_support_diff']+flags,scope='Occupancy/acc/present only shared old routed CHANNELs, not searched alternative nodes/nonconfigurable groups/bounding-box state or sink scheduling. Criticality is raw production setup criticality, not transformed internal objective; net_delay observed per-call. No-observed-change does not prove identical router inputs. No causal or predictor quality claim.'),indent=2)+'\n')
if __name__=='__main__':main()
