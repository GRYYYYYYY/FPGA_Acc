"""Label-dependent recorded-support witness ranking. Never an admitted predictor."""
import json,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from verify_wbuart_map_priority_metrics_v1 import scores,rho
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'wbuart_best_support_ranking_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def measure(values,truth,domain):
 result={}
 for scope,k in [('resource',domain['resource_k']),('spatial',domain['spatial_k'])]:
  a,b=values[scope],truth[scope];pred=sorted(a,key=lambda i:(-a[i],i))[:k];target=sorted(b,key=lambda i:(-b[i],i))[:k];result[scope]={'rho':rho(a,b),'hits':len(set(pred)&set(target)),'k':k}
 return result
def numeric_comparison(a,b):
 nonreg=[];strict=[]
 for scope in ['resource','spatial']:
  x,y=a[scope],b[scope];defined=x['rho'] is not None and y['rho'] is not None;nonreg.extend([defined and x['rho']>=y['rho']-1e-12,x['hits']>=y['hits']]);strict.extend([defined and x['rho']>y['rho']+1e-12,x['hits']>y['hits']])
 return all(nonreg) and any(strict)
def main():
 D.mkdir(exist_ok=False);source=E/'wbuart_map_candidate_coverage_v1_2026-10-20/verification.json';ind=source.parent/'independent_verification_v1.json';assert read(ind)['NET_pools']==77328;files=[Path(__file__),source,ind,E/'wbuart_map_spatial_rank_bounds_v1_2026-10-20/interpretation_v1.json'];bindings={str(p):sha(p) for p in files};(D/'protocol.json').write_text(json.dumps({'status':'FROZEN_ALL72_LABEL_DEPENDENT_BEST_SUPPORT_WITNESS_AGGREGATE_DIAGNOSTIC','selection':'Use already frozen best perNET support symmetric-difference witness from finite pool. Ties keep earlier recorded witness exactly. Replay original origin to certify actual complete candidate. No rank fitting, new paths, new labels or parameter search.','scope':'Only CHANNEL counts/scores, not audited demand frames, serial admissibility, deployable predictions or legal routes. Numeric comparisons retain original four metrics/K/ties/epsilon and source/actual raw_min controls, but no result is accepted as passing original predictor gates. A passing diagnostic shows one aggregate ranking witness; failure does not prove all joint choices fail.','bindings':bindings},indent=2)+'\n');workflow=read(E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json');allrows=read(source)['rows'];graphs={};rows=[]
 for row in allrows:
  case=row['case'];specfile=Path(next(c['specification'] for c in workflow['comparisons'] if c['case']==case));spec=read(specfile);ep=read(row['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge']
  dest=graphs[g];resourcesfile=Path(row['resources']);resources=[json.loads(x) for x in resourcesfile.read_text().splitlines()];channels={r['id'] for r in resources};binsfile=resourcesfile.parent/'spatial_bins.json';bins=read(binsfile);domain=read(spec['domain_proof']);out=Path(row['output']);initial=defaultdict(list)
  for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
  receipt=read(out/'receipt.json');counts=Counter();witnesses=[]
  for net in read(row['payload']):
   n=net['net_id'];origin=net['best']['origin']
   if origin.get('stage')=='initial':records=initial[n]
   else:
    event=receipt['rounds'][origin['round']]['events'][origin['event_index']];assert event['net_id']==n and event['status']==origin['status'];records=event.get('records',event.get('rejected_records'))
   assert records is not None and {q['connection_id'] for q in records}=={q['connection_id'] for q in initial[n]} and all(q['answer']['delay']<=q['budget_integer'] for q in records)
   support={dest[e] for q in records for e in q['answer']['physical_edge_ids'] if dest[e] in channels};assert sorted(support)==net['best']['CHANNEL_nodes'];counts.update(support);witnesses.append({'net_id':n,'origin':origin})
  assert len(witnesses)==1074
  raw=next(r for r in allrows if r['case']==case and r['initializer']=='raw_min' and r['timing_policy']==row['timing_policy'] and r['priority']==row['priority']);rawfile=Path(raw['output'])/'sketch.json';rawcounts={int(n):v for n,v in read(rawfile)['ledger'].items()};truthfile=Path(spec['label_physical_audit']);truthcounts={int(n):v for n,v in read(truthfile)['node_occupancy'].items()};sourcefile=Path(spec['source_frame']);sourcecounts={int(n):v for n,v in read(sourcefile)['ledger'].items()};truth=scores(resources,bins,truthcounts);metrics={name:measure(scores(resources,bins,value),truth,domain) for name,value in [('best_support_label_diagnostic',counts),('previous_native',sourcecounts),('actual_raw_min',rawcounts)]};comparisons={name:numeric_comparison(metrics['best_support_label_diagnostic'],metrics[name]) for name in ['previous_native','actual_raw_min']};d=D/case/row['initializer']/row['timing_policy']/row['priority'];d.mkdir(parents=True);p=d/'label_diagnostic_counts.json';p.write_text(json.dumps({'label_dependent':True,'admitted_predictor':False,'CHANNEL_counts':dict(counts),'witnesses':witnesses},separators=(',',':'))+'\n');result={k:row[k] for k in ['case','initializer','timing_policy','priority','endpoint','resources','payload','output']};result.update(diagnostic_payload=str(p),raw_control=str(rawfile),source_frame=str(sourcefile),truth_payload=str(truthfile),domain_proof=spec['domain_proof'],metrics=metrics,numeric_diagnostic_comparisons=comparisons,both_numeric_comparisons=all(comparisons.values()),admitted_predictor=False);rows.append(result);print(case,row['initializer'],row['timing_policy'],row['priority'],result['both_numeric_comparisons'],flush=True)
  for path in [p,specfile,Path(row['endpoint']),Path(g),resourcesfile,binsfile,Path(row['payload']),out/'initial.json',out/'receipt.json',rawfile,truthfile,sourcefile,Path(spec['domain_proof'])]:bindings[str(path)]=sha(path)
 assert len(rows)==72
 (D/'verification.json').write_text(json.dumps({'status':'ALL72_EXISTING_BEST_SUPPORT_WITNESSES_REPLAYED_AND_AGGREGATE_RANK_DIAGNOSTICS_COMPUTED','rows':rows,'bindings':bindings,'independent_verification_pending':True,'candidate_promoted':False,'original_quality_gate_passes_unchanged':True},indent=2)+'\n')
if __name__=='__main__':main()
