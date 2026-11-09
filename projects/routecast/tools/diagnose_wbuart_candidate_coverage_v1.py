"""Finite stored NET candidate coverage diagnostic, not a deployable oracle."""
import json,hashlib,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from native_route_ledger_import_compact import physical_paths
E=R/'experiments';D=E/'wbuart_candidate_coverage_v1_2026-10-20'
def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 D.mkdir(exist_ok=False);M=E/'wbuart_fixed_horizon_trial_v1_2026-10-20/manifest.json';W=E/'wbuart_native_evaluation_v1_2026-10-20/workflow.json';review=M.parent/'work_review_v1.json';assert read(review)['events']==618624;bindings={str(p):sha(p) for p in [Path(__file__),M,W,review]};graphs={};rows=[]
 for c in read(M)['cases']:
  spec=read(next(x['specification'] for x in read(W)['comparisons'] if x['case']==c['case']));ep=read(spec['endpoint']);g=ep['inputs']['graph']['path']
  if g not in graphs:graphs[g]=[int(e.get('sink_node')) for _,e in ET.iterparse(g) if e.tag=='edge'];bindings[g]=sha(g)
  dest=graphs[g];resources=Path(spec['domain_proof']).parent/'resources.jsonl';channels={json.loads(l)['id'] for l in resources.read_text().splitlines()};names={name:int(n) for n,name in ep['net_names'].items()};route=Path(spec['label_physical_audit']).parent/'output.route';target={names[name]:frozenset(n for branch in paths for n,sw in branch if n in channels) for name,paths in physical_paths(route).items() if paths};assert len(target)==1074;netcids=defaultdict(set)
  for q in ep['connections']:netcids[q['net_id']].add(q['connection_id'])
  def support(records):return frozenset(dest[e] for q in records for e in q['answer']['physical_edge_ids'] if dest[e] in channels)
  for arm in read(Path(c['output'])/'verification.json')['arms']:
   out=Path(arm['output']);proof=read(arm['audit']);assert all(sha(p)==h for p,h in proof['bindings'].items());initial=defaultdict(list);final=defaultdict(list)
   for q in read(out/'initial.json')['records']:initial[q['net_id']].append(q)
   for q in read(out/'round15.json')['records']:final[q['net_id']].append(q)
   pools=defaultdict(set);best={};proposals=Counter()
   def offer(net,records,origin):
    assert {q['connection_id'] for q in records}==netcids[net] and len(records)==len(netcids[net]);s=support(records);pools[net].add(s);proposals[net]+=1;error=len(s^target[net])
    if net not in best or error<best[net]['error']:best[net]={'error':error,'origin':origin,'CHANNEL_nodes':sorted(s)}
   for n,rs in initial.items():offer(n,rs,{'stage':'initial'})
   for rnd in read(out/'receipt.json')['rounds']:
    for i,event in enumerate(rnd['events']):
     records=event.get('records',event.get('rejected_records'))
     if records is not None:offer(event['net_id'],records,{'round':rnd['round_index'],'event_index':i,'status':event['status']})
   payload=[]
   for net in sorted(target):
    a=len(support(initial[net])^target[net]);b=len(support(final[net])^target[net]);minimum=best[net]['error'];assert minimum<=a and minimum<=b;payload.append({'net_id':net,'candidate_observations':proposals[net],'unique_CHANNEL_supports':len(pools[net]),'initial_error':a,'final16_error':b,'minimum_stored_support_error':minimum,'selection_gap_at16':b-minimum,'best':best[net]})
   d=D/c['case']/arm['initializer']/arm['timing_policy'];d.mkdir(parents=True);p=d/'NETs.json';p.write_text(json.dumps(payload)+'\n');summary={'case':c['case'],'initializer':arm['initializer'],'timing_policy':arm['timing_policy'],'output':str(out),'payload':str(p),'NETs':1074,'initial_support_error_sum':sum(x['initial_error'] for x in payload),'final16_support_error_sum':sum(x['final16_error'] for x in payload),'finite_pool_min_support_error_sum':sum(x['minimum_stored_support_error'] for x in payload),'selection_gap_sum':sum(x['selection_gap_at16'] for x in payload),'NETs_with_exact_target_support_in_pool':sum(x['minimum_stored_support_error']==0 for x in payload),'NETs_with_pool_better_than_final16':sum(x['selection_gap_at16']>0 for x in payload),'target_route':str(route),'resources':str(resources),'endpoint':spec['endpoint']};rows.append(summary);bindings[str(p)]=sha(p);bindings[arm['audit']]=sha(arm['audit']);print(c['case'],arm['initializer'],arm['timing_policy'],summary['final16_support_error_sum'],summary['finite_pool_min_support_error_sum'],flush=True)
  for p in [route,resources,Path(spec['endpoint'])]:bindings[str(p)]=sha(p)
 assert len(rows)==36
 (D/'verification.json').write_text(json.dumps({'status':'ALL36_FINITE_RECORDED_CANDIDATE_POOLS_MINIMUM_NET_CHANNEL_ERRORS_COMPUTED','rows':rows,'bindings':bindings,'scope':'Exact perNET minimum support symmetric difference within recorded warm/committed/rejected complete candidates only. Unrecorded primary/fallback alternatives excluded. Label-directed selections are not executable forecasts, global resource/spatial ranking optimum, joint guard-feasible solutions, routing necessity or promotion evidence. No new paths/search/gate changes.'},indent=2)+'\n')
if __name__=='__main__':main()
