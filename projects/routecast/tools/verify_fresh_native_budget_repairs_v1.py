"""Independent complete raw-route and per-event original XML/Fraction replay."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
from pre_route_endpoints import sha
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1];D=R/'experiments/fresh_native_budget_repairs_v1_2026-10-08';rp=D/'receipt.json';r=json.loads(rp.read_text());p=json.loads((D/'protocol.json').read_text());assert sha(D/'protocol.json')==r['protocol_sha256'] and all(sha(f)==h for f,h in r['bindings'].items())
case=next(c for c in json.loads((R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2);meta=json.loads(Path(case['target']).read_text());queries={q['connection_id']:q for q in meta['connections']};graph=Path(meta['inputs']['graph']['path']);xml=ImmutableXMLAudit(graph,meta['graph_sha256']);ids,classes,switches,digest=read(graph);assert digest==xml.digest;budget=json.loads(Path(case['budget']).read_text())
route=R/'experiments/native_resume_branch_partial_v8_2026-10-08/resume/output.route';observed={}
for name,paths in physical_paths(route).items():
 for path in paths:
  key=name,path[0][0],path[-1][0];assert key not in observed;observed[key]=path
expected={(meta['net_names'][str(q['net_id'])],q['source'],q['sink']):cid for cid,q in queries.items()};assert set(expected)==set(observed) and len(expected)==len(queries)==1929
state={cid:observed[key] for key,cid in expected.items()};initial_state=dict(state);arcs=defaultdict(list)
for eid in range(len(xml.graph.edges)):
 edge=xml.graph.edges[eid];arcs[edge.source,edge.sink,edge.switch_id].append(eid)
def physical(cid,path):
 q=queries[cid];assert path[0]==(q['source'],None) and path[-1][0]==q['sink'] and len({n for n,s in path})==len(path)
 assert xml.graph.nodes[q['source']].type=='SOURCE' and xml.graph.nodes[q['sink']].type=='SINK' and all(xml.graph.nodes[n].capacity>0 for n,s in path)
 nr,nc=classes[ids[q['source']]];value=nr*nc/2;used=[]
 for (u,_),(v,s) in zip(path,path[1:]):
  assert len(arcs[u,v,s])==1;used.append(arcs[u,v,s][0]);nr,nc=classes[ids[v]];sr,td=switches[s];value+=(sr+nr/2)*nc+td
 return value,used
def ledger():
 unions=defaultdict(set);parents=defaultdict(dict)
 for cid,path in state.items():
  net=queries[cid]['net_id'];unions[net].update(n for n,s in path)
  for (u,_),(v,s) in zip(path,path[1:]):assert v not in parents[net] or parents[net][v]==(u,s);parents[net][v]=(u,s)
 demand=Counter(n for ns in unions.values() for n in ns);assert all(v<=xml.graph.nodes[n].capacity for n,v in demand.items());return unions,demand
delay={};initial_rows={x['connection_id']:x for x in r['initial_rows']};assert set(initial_rows)==set(queries)
limits={cid:F(budget['budgets_ns'].get(str(cid),budget['default_budget_ns']))/10**9 for cid in queries}
for cid,path in state.items():
 value,edges=physical(cid,path);delay[cid]=value;assert value*r['scale']==initial_rows[cid]['delay_integer'] and edges==initial_rows[cid]['physical_edge_ids']
initial_delay=dict(delay);violations=sorted(cid for cid in queries if delay[cid]>limits[cid]);assert violations==r['initial_budget_violation_ids']==p['attempt_order']==[e['connection_id'] for e in r['events']];ledger();commits=[]
for e in r['events']:
 cid=e['connection_id'];q=queries[cid];net=q['net_id'];assert q==e['query'] and e['old_path']==[list(x) for x in state[cid]] and delay[cid]*r['scale']==e['old_delay_integer']
 ceiling=limits[cid]*r['scale'];assert e['budget_integer_ceiling']==ceiling.numerator//ceiling.denominator
 answer=e['search'];assert answer['labels_created']<=p['max_labels']
 if answer['status']!='FOUND':assert e['status']=='RETAIN_'+answer['status'] and answer['physical_edge_ids'] is None;continue
 union,demand=ledger();outside=demand.copy();outside.subtract(union[net]);fixed={}
 for other,path in state.items():
  if other!=cid and queries[other]['net_id']==net:
   for (u,_),(v,s) in zip(path,path[1:]):assert v not in fixed or fixed[v]==(u,s);fixed[v]=(u,s)
 path=[(q['source'],None)];u=q['source'];assert outside[u]<xml.graph.nodes[u].capacity
 for eid in answer['physical_edge_ids']:
  edge=xml.graph.edges[eid];assert edge.source==u;v=edge.sink;s=edge.switch_id;assert outside[v]<xml.graph.nodes[v].capacity and (v not in fixed or fixed[v]==(u,s));path.append((v,s));u=v
 value,edges=physical(cid,path);assert edges==answer['physical_edge_ids'] and value*r['scale']==answer['delay']<=e['budget_integer_ceiling'] and answer['cost']==0 and value<=limits[cid]
 assert e['status']=='COMMIT' and e['new_path']==[list(x) for x in path];state[cid]=tuple(path);delay[cid]=value;ledger();commits.append(cid)
assert r['state']=={str(cid):[list(x) for x in path] for cid,path in state.items()}
rows=[]
for cid,path in state.items():
 value,edges=physical(cid,path);assert value==delay[cid]
 if cid not in commits:assert value==initial_delay[cid] and path==initial_state[cid]
 rows.append(dict(connection_id=cid,delay_seconds=str(value),budget_ns=str(limits[cid]*10**9),budget_pass=value<=limits[cid],physical_edge_ids=edges))
final_failed=sorted(cid for cid in queries if delay[cid]>limits[cid]);assert final_failed==r['final_budget_violation_ids']==[785,1637]
bp=R/'experiments/budget_occupied_branch_repair_v1_2026-10-08/complete_frame_verification_v2.json';baseline=json.loads(bp.read_text());assert all(sha(f)==h for f,h in baseline['bindings'].items());br=bp.with_name('receipt.json');old=json.loads(br.read_text());assert old['state']==r['state']
bindings={**r['bindings'],**baseline['bindings'],str(rp):sha(rp),str(D/'protocol.json'):sha(D/'protocol.json'),str(bp):sha(bp),str(br):sha(br),str(Path(__file__)):sha(Path(__file__)),str(R/'tools/immutable_xml_prediction_audit.py'):sha(R/'tools/immutable_xml_prediction_audit.py'),str(R/'tools/buffered_rc_node_classes.py'):sha(R/'tools/buffered_rc_node_classes.py')};assert all(sha(f)==h for f,h in bindings.items())
out=dict(bindings=bindings,all1929_raw_and_final_original_xml_fraction_paths_pass=True,all8_discovered_budget_attempts_replay_pass=True,initial_budget_violation_ids=violations,committed_connection_ids=commits,budget_safe_connections=1927,budget_violation_ids=final_failed,all_historical_final_state_paths_equal=True,rows=rows,component_elapsed_seconds=r['component_elapsed_seconds'],search_seconds=r['search_seconds'],scope='Raw native route -> full discovery -> all failed branches attempted, without historical candidate as production input. All noncommitted demands/paths unchanged, final state equals prior independently accepted model state. Exhaustion not independently certified as unconstrained infeasibility/minimum. Excludes producing input route/endpoints/budgets and owner/wire/VPR/audits; no end-to-end gain or original HDL equivalence.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k not in ('bindings','rows')},flush=True)
