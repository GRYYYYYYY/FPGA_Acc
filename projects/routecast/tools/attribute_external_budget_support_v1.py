"""Full resource budget-path strata, frozen six methods and all3 cases."""
import json,sys
from pathlib import Path
from collections import Counter,defaultdict
sys.path[:0]=[str(Path(__file__).resolve().parent),str(Path(__file__).resolve().parent/'native_resume_prototype')]
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';B=E/'prospective_external_family_native_label_budget_compatibility_v1_2026-10-19';D=E/'prospective_external_family_budget_path_support_attribution_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 audit=read(B/'independent_verification_v1.json');assert all(sha(p)==h for p,h in audit['bindings'].items());D.mkdir(exist_ok=False);bindings={str(B/'independent_verification_v1.json'):sha(B/'independent_verification_v1.json'),str(Path(__file__).resolve()):sha(__file__)};cases=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';sp=P/'specifications'/case/'comparison_spec.json';s=read(sp);methods={'previous_native':(s['source_frame'],s['source_proof']),'raw_min_on':(s['predictions']['raw_min_on']['frame'],s['predictions']['raw_min_on']['proof']),'original_feedback':(s['predictions']['native_retained_on']['frame'],s['predictions']['native_retained_on']['proof'])}
  for name,folder,proof in [('astar_reuse','prospective_external_family_budget_astar_reuse_warm_v1_2026-10-19','independent_verification_v1.json'),('fanout_feedback','prospective_external_family_fanout_order_feedback_v1_2026-10-19',case+'/complete_event_audit.json'),('objective_only','prospective_external_family_objective_only_forecast_v1_2026-10-19',case+'/complete_event_audit.json')]:
   methods[name]=(str(E/folder/case/('frame.json' if name=='astar_reuse' else 'sketch.json')),str(E/folder/proof))
  cases.append(dict(case=case,specification=str(sp),methods={k:dict(frame=f,proof=p) for k,(f,p) in methods.items()}))
 (D/'protocol.json').write_text(json.dumps(dict(cases=cases,policy='All45584 resource IDs percase, masks0=native-unused/1=only compatible native CID paths/2=only over-budget native CID paths/3=both. Exact native path membership, no budget or label modification. Six frozen complete methods, no selection. Over-only does not imply resource unreachable under forecast budget via another path/NET. Support confusion is descriptive, not original four metrics or causality.'),indent=2)+'\n');results=[]
 for c in cases:
  case=c['case'];s=read(c['specification']);ep=read(s['endpoint']);domain=Path(s['domain_proof']).parent;ids={json.loads(x)['id'] for x in (domain/'resources.jsonl').read_text().splitlines()};table={r['connection_id']:r for r in read(B/case/'all_CIDs.json')};lookup={(ep['net_names'][str(q['net_id'])],q['source'],q['sink']):q['connection_id'] for q in ep['connections']};mask=Counter();seen=set();route=P/'native'/case/'output.route'
  for name,paths in physical_paths(route).items():
   for path in paths:
    cid=lookup[name,path[0][0],path[-1][0]];assert cid not in seen;seen.add(cid);bit=2 if table[cid]['over_budget'] else 1
    for n,_ in path:
     if n in ids:mask[n]|=bit
  assert seen==table.keys();truth={int(n) for n,v in read(s['label_physical_audit'])['node_occupancy'].items() if v};assert {n for n,v in mask.items() if v}==truth&ids
  ledgers={}
  for method,arm in c['methods'].items():
   proof=read(arm['proof']);assert all(sha(p)==h for p,h in proof['bindings'].items());assert proof['bindings'][arm['frame']]==sha(arm['frame']);ledgers[method]={int(n):v for n,v in read(arm['frame'])['ledger'].items()};bindings[arm['proof']]=sha(arm['proof']);bindings[arm['frame']]=sha(arm['frame'])
  counts=Counter(mask.get(n,0) for n in ids);stats={m:{str(k):dict(resources=counts[k],supported=0,missed=0) for k in (0,1,2,3)} for m in ledgers};out=D/case;out.mkdir(parents=True);rp=out/'all_resources.jsonl'
  with rp.open('x') as f:
   for n in sorted(ids):
    k=mask.get(n,0);values={m:l.get(n,0) for m,l in ledgers.items()};f.write(json.dumps(dict(id=n,budget_path_mask=k,counts=values))+'\n')
    for m,v in values.items():stats[m][str(k)]['supported']+=v>0;stats[m][str(k)]['missed']+=v==0
  row=dict(case=case,resources=len(ids),mask_counts=dict(counts),method_strata=stats);results.append(row)
  for p in [rp,route,B/case/'all_CIDs.json',Path(s['label_physical_audit']),domain/'resources.jsonl',Path(c['specification'])]:bindings[str(p)]=sha(p)
  print(case,'strata',dict(counts),'prior_misses',{k:v['missed'] for k,v in stats['previous_native'].items()},flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'summary.json').write_text(json.dumps(dict(status='ALL136752_RESOURCE_IDS_BUDGET_PATH_STRATA_AND18_SUPPORT_TABLES_COMPLETE',rows=results,bindings=bindings,scope=read(D/'protocol.json')['policy']),indent=2)+'\n')
if __name__=='__main__':main()
