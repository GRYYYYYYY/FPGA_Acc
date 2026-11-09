"""Wait for audited full host prediction, then diagnose five over-budget updates."""
import json,time,shutil
from pathlib import Path
from collections import defaultdict
from prepared_csr import read
from pre_route_endpoints import sha
from stereo_host_completion_chain import identity

def run():
 b=Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'global_minimum_bypass_impact';out.mkdir();(out/'source').mkdir()
 parent=b/'ordinary_additive_class_cache_prediction_undriven_v2_authenticated_host';physical=b/(parent.name+'_physical_audit');evaluation=b/'ordinary_additive_undriven_v2_authenticated_host_evaluation'
 matches=[]
 for p in Path('/proc').iterdir():
  if p.name.isdigit():
   d=identity(int(p.name))
   if d and 'tools/stereo_host_completion_chain.py' in d['argv']:matches.append(d)
 if len(matches)!=1:raise ValueError('expected one live original completion chain')
 process=matches[0];names=['stereo_global_bypass_impact.py','stereo_host_completion_chain.py','prepared_csr.py','pre_route_endpoints.py'];sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 waiting={'observed_chain':process,'sources':sources,'parent_protocol_sha256':sha(parent/'protocol.json'),'scope':'global occupancy impact diagnostic after full physical audit/evaluation; five paths exceed budgets, no commit'}
 (out/'waiting_protocol.json').write_text(json.dumps(waiting,indent=2)+'\n');print(json.dumps({'stage':'waiting_for_audited_full_evaluation','chain':process}),flush=True)
 while not (evaluation/'receipt.json').exists():
  if identity(process['pid'])!=process:raise RuntimeError('original chain terminal without full evaluation receipt; no restart')
  time.sleep(10)
 assert sha(parent/'protocol.json')==waiting['parent_protocol_sha256'];p=json.loads((parent/'protocol.json').read_text());r=json.loads((parent/'receipt.json').read_text());ar=json.loads((physical/'receipt.json').read_text());er=json.loads((evaluation/'receipt.json').read_text())
 assert r['connections']==81610 and ar['result']['all_physical_and_union_checks_passed'] and ar['prediction_receipt_sha256']==sha(parent/'receipt.json') and er['exact_full_cohort_match']
 assert r['prediction_sha256']==sha(parent/'prediction.json') and ar['protocol_sha256']==sha(physical/'protocol.json') and er['protocol_sha256']==sha(evaluation/'protocol.json')
 bypass=b/'conflict_minimum_bypass_delay';br=json.loads((bypass/'receipt.json').read_text());assert br['results_sha256']==sha(bypass/'results.json')
 changes=json.loads((bypass/'results.json').read_text());assert len(changes)==5 and all(x['status']=='FOUND' and not x['fits_original_budget'] for x in changes)
 audit=b/'minimum_bypass_physical_audit_v2';assert json.loads((audit/'receipt.json').read_text())['physical_audit']['all_physical_and_union_checks_passed']
 files=[parent/'prediction.json',parent/'receipt.json',physical/'receipt.json',physical/'protocol.json',evaluation/'receipt.json',evaluation/'protocol.json',bypass/'results.json',bypass/'receipt.json',audit/'receipt.json',b/'streaming_csr_class_cache_v3/csr/manifest.json']
 inputs={str(x):sha(x) for x in files};graph=p['inputs']['graph']['sha256'];protocol={'inputs':inputs,'sources':sources,'graph_sha256':graph,'waiting_protocol_sha256':sha(out/'waiting_protocol.json'),'scope':waiting['scope']};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
 _,f=read(b/'streaming_csr_class_cache_v3/csr',graph);pred=json.loads((parent/'prediction.json').read_text());assert len(pred['connections'])==81610
 affected={x['net_id'] for x in changes};bycid={x['connection_id']:x for x in changes};rows=[x for x in pred['connections'] if x['net_id'] in affected];assert len(rows)==429 and set(bycid)<=set(x['connection_id'] for x in rows)
 def touched(source,path):
  if path is None:raise ValueError('incomplete affected original network')
  node=source;seen={node}
  for eid in path:
   matches=[i for i in range(f['row_offsets'][node],f['row_offsets'][node+1]) if f['edge_ids'][i]==eid];assert len(matches)==1;node=f['dest_ranks'][matches[0]];assert node not in seen;seen.add(node)
  return seen,node
 old=defaultdict(set);new=defaultdict(set)
 for x in rows:
  nodes,sink=touched(x['source'],x['physical_edge_ids']);assert sink==x['sink'];old[x['net_id']].update(nodes)
  path=bycid[x['connection_id']]['physical_edge_ids'] if x['connection_id'] in bycid else x['physical_edge_ids'];nodes,sink=touched(x['source'],path);assert sink==x['sink'];new[x['net_id']].update(nodes)
 delta=defaultdict(int)
 for net in affected:
  for n in old[net]-new[net]:delta[n]-=1
  for n in new[net]-old[net]:delta[n]+=1
 pv=pred['node_occupancy'];before=sum(max(0,v-f['capacities'][int(k)]) for k,v in pv.items());assert before==ar['result']['all_type_overuse_units']==er['reports']['prediction_overflow_units']
 after=before;effects=[]
 for n,d in sorted(delta.items()):
  previous=pv.get(str(n),0);now=previous+d;cap=f['capacities'][n];assert now>=0
  after+=max(0,now-cap)-max(0,previous-cap);effects.append({'rr_node':n,'capacity':cap,'before':previous,'after':now,'delta':d,'introduced_or_increased_overflow':max(0,now-cap)>max(0,previous-cap)})
 assert all(sha(k)==h for k,h in inputs.items()) and all(sha(Path('tools')/n)==h for n,h in sources.items())
 receipt={'full_connections':81610,'affected_network_connections':429,'replaced':5,'unchanged_full_connections':81605,'baseline_global_overflow_units':before,'diagnostic_global_overflow_units':after,'changed_resource_effects':effects,'budget_gate_passed':False,'committed':False,'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'scope':protocol['scope'],'limits':'occupancy delta only; full equivalent-pin ownership, native timing/reassignment and complete modified XML audit not certified'}
 (out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
