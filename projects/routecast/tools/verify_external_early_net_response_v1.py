"""Independent decimal token joins and all-cleanNET runtime partition checks."""
import json,sys
from pathlib import Path
from decimal import Decimal as N
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_early_net_observer_v1_2026-10-19';D=E/'prospective_external_family_early_net_response_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def parse(path):
 nodes={};timing={};order={}
 with path.open() as f:
  for line in f:
   x=line.split();phase=x[0];it,o,net=map(int,x[1:4]);key=(it,net);order[key]=o
   if phase=='C':timing[it,net,int(x[4])]=(N(x[5]),N(x[6]))
   else:nodes[it,net,phase]={int(y.split(':')[0]):tuple(N(v) for v in y.split(':')[1:]) for y in x[6:]}
 return nodes,timing,order

def main():
 s=read(D/'summary.json');assert all(sha(p)==h for p,h in s['bindings'].items());a,ta,oa=parse(I/'source/early_net_trace.tsv');pins={}
 for it,net,pin in ta:pins.setdefault((it,net),[]).append(pin)
 results=[]
 for case in s['rows']:
  name=case['case'];b,tb,ob=parse(I/name/'early_net_trace.tsv');records=read(D/name/'all_clean_NET_observations.json');assert len({(r['iteration'],r['net_id']) for r in records})==len(records);cells={it:Counter() for it in (1,2,3)}
  for r in records:
   it,n=r['iteration'],r['net_id'];left,right=a[it,n,'B'],b[it,n,'B'];shared=left.keys()&right.keys();flags=[left.keys()!=right.keys(),a[it,n,'A'].keys()!=b[it,n,'A'].keys()]+[any(left[x][j]!=right[x][j] for x in shared) for j in (0,1,2)]+[any(ta[it,n,p][j]!=tb[it,n,p][j] for p in pins[it,n]) for j in (0,1)];assert tuple(flags)==tuple(r[k] for k in s['flag_order']);assert r['new_divergence']==(not flags[0] and flags[1]);assert r['order']==oa[it,n]==ob[it,n];cells[it][tuple(flags)]+=1
  for published in case['rounds']:
   it=published['iteration'];assert cells[it]=={tuple(r['values']):r['count'] for r in published['cells']};group=[r for r in records if r['iteration']==it];fresh=[r for r in group if not r['before_support_diff'] and r['after_support_diff']];assert len(group)==published['all_clean_NETs'] and len(fresh)==published['new_divergences'];flags=s['flag_order'][2:];assert {k:sum(r[k] for r in fresh) for k in flags}==published['new_with_each_flag'];assert sum(any(r[k] for k in flags) for r in fresh)==published['new_any_observed_input_changed'];assert sum(not any(r[k] for k in flags) for r in fresh)==published['new_no_observed_input_changed'];assert min((r['order'] for r in fresh),default=None)==published['first_new_order']
  results.append(dict(case=name,all_clean_NET_round_records=len(records)))
 with (D/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_RUNTIME_RESPONSE_FLAGS_AND_PARTITIONS_DECIMAL_RECONSTRUCTED',rows=results,bindings={str(D/'summary.json'):sha(D/'summary.json'),str(Path(__file__).resolve()):sha(__file__)}),f,indent=2)
 print('ALL3_RUNTIME_RESPONSE_PARTITIONS_VERIFIED')
if __name__=='__main__':main()
