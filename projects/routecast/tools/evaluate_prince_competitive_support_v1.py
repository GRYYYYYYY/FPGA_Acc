"""Frozen competitive candidate-support feasibility; not a forecast model or gate."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from verify_prince_ready_owner_forecast_v1 import ready_inverse,final_inverse
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'prince_competitive_support_v1_2026-10-20';S=E/'prince_competitive_frontier_trial_v1_2026-10-20';Q=E/'prince_causal_query_frontier_v1_2026-10-20'
def load(p):return json.loads(Path(p).read_text())
def score(support,ready,new,arrivals):
 eligible={(net,n) for net,n in support if net not in ready.get(n,set())};nodes={n for net,n in eligible if not ready.get(n)};tp=len(eligible&new);ntp=len(nodes&arrivals)
 return dict(new_pair_candidates=len(eligible),true_new_final_pairs=tp,new_pair_precision=tp/len(eligible) if eligible else None,new_pair_recall=tp/len(new),global_arrival_candidates=len(nodes),true_global_arrivals=ntp,global_arrival_precision=ntp/len(nodes) if nodes else None,global_arrival_recall=ntp/len(arrivals))
def main():
 frozen=load(D/'frozen_inputs.json');assert all(sha(p)==h for p,h in frozen['bindings'].items());qf=load(Q/'frozen_inputs.json');queries={r['case']:r for r in qf['rows']};qp=Q/'feasibility_screen_v1.json';prior={r['case']:r for r in load(qp)['rows']};bindings={str(p):sha(p) for p in [D/'frozen_inputs.json',Q/'frozen_inputs.json',qp,Path(__file__)]};rows=[]
 for row in frozen['rows']:
  c=row['case']
  if row['status']!='COMPETITIVE_SUPPORT_FROZEN_NO_LABELS':rows.append(dict(case=c,status=row['status']));continue
  t=row['ready_iteration'];src=S/c/'capture';op=src/'owners'/f'owners_{t}.bin';lp=src/'queries.tsv.ledger.bin';ready=ready_inverse(op);final=final_inverse(lp);new={(net,n) for n,owners in final.items() for net in owners if net not in ready.get(n,set())};arrivals={n for net,n in new if not ready.get(n)};supports={name:{} for name in ['raw','preheap','pop']}
  for i,path in row['paths'].items():
   i=int(i);a=list(map(json.loads,Path(path).open()));assert all(x['iteration']==i for x in a);assert len({(x['net'],x['node']) for x in a})==len(a)
   supports['preheap'][i]={(x['net'],x['node']) for x in a if x['preheap_accepted']>0};supports['pop'][i]={(x['net'],x['node']) for x in a if x['valid_pop']>0};rawp=Path(queries[c]['paths'][str(i)]);supports['raw'][i]={(x['net'],x['node']) for x in map(json.loads,rawp.open())};bindings[str(rawp)]=sha(rawp)
  modes={};differences={}
  for mode,phases in [('ready',[t]),('two_phase_union',[t-1,t])]:
   selected={name:set().union(*(per[i] for i in phases)) for name,per in supports.items()};modes[mode]={name:score(s,ready,new,arrivals) for name,s in selected.items()};assert modes[mode]['raw']==prior[c]['methods'][mode];differences[mode]={}
   for name,other in [('preheap','pop'),('pop','preheap'),('preheap','raw'),('pop','raw')]:
    only=selected[name]-selected[other];differences[mode][f'{name}_minus_{other}']=dict(total_pairs=len(only),**score(only,ready,new,arrivals))
  rows.append(dict(case=c,status='COMPETITIVE_SUPPORT_SCREENED',new_final_owner_pairs=len(new),global_arrivals=len(arrivals),methods=modes,differences=differences));print(c,{mode:{name:(m['new_pair_candidates'],m['true_new_final_pairs'],round(m['new_pair_precision'],5),round(m['new_pair_recall'],4)) for name,m in ms.items()} for mode,ms in modes.items()},flush=True)
  for p in [op,lp]:bindings[str(p)]=sha(p)
 assert len(rows)==9 and all(sha(p)==h for p,h in bindings.items())
 with (D/'verification.json').open('x') as f:json.dump(dict(status='COMPETITIVE_SUPPORT_FEASIBILITY_SCREENED_NO_FORECAST_ADMISSION',rows=rows,bindings=bindings,full9_gate=False,scope='Exact candidate support/precision/recall only;not learned probabilities,original full-domain metric gate,native benefit,fullpaid,unseen or hardware evidence.'),f,indent=2);f.write('\n')
if __name__=='__main__':main()
