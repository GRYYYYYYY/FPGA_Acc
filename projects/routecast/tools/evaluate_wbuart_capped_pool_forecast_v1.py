"""Independent bitset/Fraction marginals and fixed original ranking comparisons."""
import json,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
from exact_factor_elimination_v1 import sha
from prediction_metrics import compare
from verify_wbuart_best_support_ranking_v1 import normalize
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_capped_pool_forecast_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def main():
 source=D/'forecasts_frozen.json';v=read(source);assert v['target_payloads_read'] is False and len(v['rows'])==72
 assert all(sha(p)==h for p,h in v['bindings'].items())
 inventory=E/'wbuart_joint_aggregate_L1_v1_2026-10-20/verification.json';old=read(inventory)['rows'];graphs={};results=[];bindings={str(source):sha(source),str(inventory):sha(inventory),str(Path(__file__)):sha(__file__),str(R/'tools/prediction_metrics.py'):sha(R/'tools/prediction_metrics.py'),str(R/'tools/verify_wbuart_best_support_ranking_v1.py'):sha(R/'tools/verify_wbuart_best_support_ranking_v1.py')}
 for r in v['rows']:
  row=next(x for x in old if all(x[k]==r[k] for k in ['case','initializer','timing_policy','priority']));ep=read(r['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];resources=[json.loads(x) for x in Path(r['resources']).read_text().splitlines()];ids=sorted(x['id'] for x in resources);masks={n:1<<i for i,n in enumerate(ids)};pools=defaultdict(set);initial=defaultdict(list);out=Path(r['output'])
  def add(net,rs):
   mask=0
   for q in rs:
    for e in q['answer']['physical_edge_ids']:mask|=masks.get(dest[e],0)
   pools[net].add(mask)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  for n,rs in initial.items():add(n,rs)
  for rnd in read(out/'receipt.json')['rounds']:
   for event in rnd['events']:
    rs=event.get('records',event.get('rejected_records'))
    if rs is not None:add(event['net_id'],rs)
  probabilities=defaultdict(list)
  for choices in pools.values():
   inclusion=Counter()
   for mask in choices:
    while mask:
     bit=mask&-mask;inclusion[ids[bit.bit_length()-1]]+=1;mask-=bit
   for node,count in inclusion.items():probabilities[node].append(F(count,len(choices)))
  counts={};capacities={item['id']:item['capacity'] for item in resources}
  for node,ps in probabilities.items():
   # Independent full polynomial expansion; no saturated-state production helper.
   mass=[F(1)]
   for probability in ps:
    nxt=[F(0)]*(len(mass)+1)
    for k,value in enumerate(mass):nxt[k]+=value*(1-probability);nxt[k+1]+=value*probability
    mass=nxt
   counts[node]=sum((min(k,capacities[node])*value for k,value in enumerate(mass)),F(0))
  forecast=read(r['forecast']);assert forecast['label_dependent'] is False and forecast['NETs']==len(pools) and forecast['distinct_patterns']==sum(map(len,pools.values()))
  assert dict(counts)=={int(n):F(c,forecast['denominator']) for n,c in forecast['numerators'].items()}
  bins=read(Path(r['resources']).parent/'spatial_bins.json');domain=read(row['domain_proof']);truth=normalize(resources,bins,{int(n):c for n,c in read(row['truth_payload'])['node_occupancy'].items()});methods={'capped_pool':counts,'previous_native':{int(n):c for n,c in read(row['source_frame'])['ledger'].items()},'actual_raw_min':{int(n):c for n,c in read(row['raw_control'])['ledger'].items()}};metrics={}
  for name,data in methods.items():
   values=normalize(resources,bins,data);metrics[name]={}
   for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
    m=compare(values[scope],truth[scope],k);metrics[name][scope]={'rho':m['spearman'],'k':k,'hits':round(m['precision_at_k']*k)}
  checks={}
  for control in ['previous_native','actual_raw_min']:
   nonreg=[];strict=[]
   for scope in ['resource','spatial']:
    a,b=metrics['capped_pool'][scope],metrics[control][scope];valid=a['rho'] is not None and b['rho'] is not None;nonreg.extend([valid and a['rho']>=b['rho']-1e-12,a['hits']>=b['hits']]);strict.extend([valid and a['rho']>b['rho']+1e-12,a['hits']>b['hits']])
   checks[control]=all(nonreg) and any(strict)
  result={k:r[k] for k in ['case','initializer','timing_policy','priority','forecast','marginalization_and_input_load_seconds']};result.update(metrics=metrics,comparisons=checks,both_comparisons=all(checks.values()));results.append(result)
  for p in [Path(row['truth_payload']),Path(row['source_frame']),Path(row['raw_control']),Path(row['domain_proof']),Path(r['resources']).parent/'spatial_bins.json']:bindings[str(p)]=sha(p)
  print('CAPPED_POOL_EVALUATED',len(results),r['case'],result['both_comparisons'],flush=True)
 primary=[r for r in results if (r['initializer'],r['timing_policy'],r['priority'])==('native_retained','warm_timing_round_updated','MAP')];assert len(primary)==9
 report={'status':'ALL72_SOURCE_ONLY_CAPPED_FORECASTS_INDEPENDENTLY_REBUILT_AND_EVALUATED','rows':results,'primary':primary,'all_config_pass':sum(r['both_comparisons'] for r in results),'primary_pass':sum(r['both_comparisons'] for r in primary),'metric_vectors':216,'bindings':bindings,'scope':'Development forecast ranking only. Input load/marginalization timing excludes previously paid candidate generation/native query setup; no end-to-end benefit, route legality or unseen-family claim. Promotion requires original complete study gates, not numerical comparisons alone.'}
 p=D/'evaluation_v1.json';assert not p.exists();p.write_text(json.dumps(report,indent=2)+'\n');print('CAPPED_POOL_COMPLETE',report['primary_pass'],report['all_config_pass'])
if __name__=='__main__':main()
