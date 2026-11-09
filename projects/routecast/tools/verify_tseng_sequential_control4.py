"""Authenticate fresh sequential lifecycle and independent accepted state snapshots."""
import json,re,math
from pathlib import Path
from collections import Counter,defaultdict
from fractions import Fraction
from pre_route_endpoints import sha
from audit_native_route import NODE
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
root=Path(__file__).resolve().parents[1];out=root/'experiments/tseng_sequential_control4_2026-10-06';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['completed'] and len(r['rounds'])==len(p['rounds'])==4 and r['protocol_sha256']==sha(out/'protocol.json')
assert all(sha(root/'tools'/n)==h for n,h in p['live_sources_sha256'].items()) and all(sha(path)==h for path,h in p['endpoint_sha256'].items())
def check(snapshot,endpoints):
 queries={q['connection_id']:q for q in endpoints['connections']};ledger=Counter();unions=defaultdict(set);parents=defaultdict(dict);physical=defaultdict(list)
 assert len(snapshot['records'])==len(queries)==1234 and {q['connection_id'] for q in snapshot['records']}==set(queries)
 for record in snapshot['records']:
  q=queries[record['connection_id']];assert all(record[k]==v for k,v in q.items());node=q['source'];used={node};path=[(node,None)];res,cap=classes[ids[node]];delay=res*cap/2;net=q['net_id']
  for eid in record['answer']['physical_edge_ids']:
   e=xml.graph.edges[eid];assert e.source==node and e.sink not in used;node=e.sink;used.add(node);delay+=arc_delay(classes,switches,ids[node],e.switch_id);path.append((node,e.switch_id));parent=(e.source,eid)
   assert node not in parents[net] or parents[net][node]==parent;parents[net][node]=parent
  assert node==q['sink'] and delay==Fraction(record['answer']['delay'],snapshot['scale'])
  ledger.update(used-unions[net]);unions[net].update(used);physical[endpoints['net_names'][str(net)]].append(tuple(path))
 assert dict(ledger)=={int(n):c for n,c in snapshot['ledger'].items()} and all(c<=xml.caps[n] for n,c in ledger.items())
 return {name:sorted(rows) for name,rows in physical.items()},ledger
def physical_by_name(path):
 nets={};name=None;parents={};previous=None;switch=None
 for line in path.read_text().splitlines():
  m=re.match(r'^Net\s+\d+\s+\((.*?)\)',line)
  if m:name=m[1];assert name not in nets;nets[name]=[];parents={};previous=None;continue
  m=NODE.match(line)
  if not m:continue
  node=int(m[1]);kind=m[2]
  if kind=='SOURCE':parents[node]=[(node,None)]
  elif kind=='SINK':nets[name].append(tuple(parents[previous]+[(node,switch)]))
  elif node not in parents:parents[node]=parents[previous]+[(node,switch)]
  previous=node;switch=int(m[3])
 return {name:sorted(paths) for name,paths in nets.items()}
audits=0;native_tail=0;staged=0;advance=0;checked=[]
for i,(row,frozen) in enumerate(zip(r['rounds'],p['rounds'])):
 sandbox=Path(frozen['sandbox']);assert row['round']==i and row['revision']==i+1 and row['endpoint_path']==frozen['endpoint_path']
 assert len(row['acceptance_and_audit'])==11 and [a['tool'] for a in row['acceptance_and_audit']]==list(frozen['source_sha256'])
 for stage in row['acceptance_and_audit']:
  name=stage['tool'];assert stage['exit_code']==0 and math.isfinite(stage['wall_s']) and stage['wall_s']>0
  assert sha(sandbox/'tools'/name)==frozen['source_sha256'][name] and sha(out/f'round{i}_{name}.log')==stage['log_sha256']
  if name.startswith(('verify_','audit_')):audits+=stage['wall_s']
  else:native_tail+=stage['wall_s']
 staged+=row['stage_s'];advance+=row['prepare_advance_s'];assert sum(s['wall_s'] for s in row['acceptance_and_audit'])+row['stage_s']+row['prepare_advance_s']<=row['round_wall_s']
 statefile=out/f'accepted{i}.json';assert sha(statefile)==row['accepted_state_sha256'];ep=json.loads(Path(row['endpoint_path']).read_text());graph=ep['inputs']['graph']['path'];xml=ImmutableXMLAudit(graph,ep['graph_sha256']);ids,classes,switches,_=read(graph);paths,ledger=check(json.loads(statefile.read_text()),ep)
 gate=sandbox/'experiments/tseng_swapped_quality_gate_2026-10-06';selection=json.loads((gate/'selection.json').read_text());v=json.loads((gate/'verification.json').read_text());assert sha(gate/'selection.json')==row['selection_sha256']==v['selection_sha256'] and v['FULL_reload_success']
 assert selection['selected']==row['selected']==('predicted' if row['candidate_cpd_ns']<=row['reference_cpd_ns'] else 'reference')
 assert selection['reference_cpd_ns']==row['reference_cpd_ns'] and selection['predicted_cpd_ns']==row['candidate_cpd_ns']
 routes=[Path(path) for path in selection['files_sha256'] if Path(path).name=='design.route'];assert len(routes)==1 and all(sha(path)==h for path,h in selection['files_sha256'].items())
 native=physical_by_name(routes[0]);excluded={x['net'] for x in ep['excluded_nets']};assert all(not native.get(n,[]) for n in excluded);assert paths=={n:rows for n,rows in native.items() if n not in excluded}
 cold=json.loads((sandbox/'experiments/tseng_swapped_place_cold_2026-10-06/receipt.json').read_text());assert cold['native_success'] and cold['cpd_ns']==selection['reference_cpd_ns']
 checked.append({'round':i,'revision':i+1,'accepted_paths':1234,'selected':row['selected'],'candidate_cpd_ns':row['candidate_cpd_ns'],'reference_cpd_ns':row['reference_cpd_ns'],'fresh_cold_native_process_s':cold['native_process_wall_s'],'physical_paths_exact':True})
assert r['context_and_initial_import_s']+sum(row['round_wall_s'] for row in r['rounds'])<=r['total_wall_s']
result={'receipt_sha256':sha(out/'receipt.json'),'rounds':checked,'total_wall_s':r['total_wall_s'],'one_context_setup_and_initial_import_s':r['context_and_initial_import_s'],'staged_update_s':staged,'native_tail_including_fresh_cold_s':native_tail,'independent_audit_s':audits,'accepted_state_prepare_advance_s':advance,'scope':p['scope']+' Endpoint/frontend preparation uses frozen archived inputs and is not included; aggregate verifier cost is outside measured window. No speedup or independent family claim.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
