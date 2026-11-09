"""Complete neuron raw-floor A* pilot; no new model/budget/quality claim."""
import json,hashlib,time,struct,gc
from pathlib import Path
from collections import defaultdict
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compiled_quotient_model_factory_v2 import create,BINARY
from compiled_quotient_raw_floor_v1_2026_10_17 import tree
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
R=Path(__file__).resolve().parents[1];D=R/'experiments/neuron_quotient_raw_floor_pilot_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(n,d):
 with (D/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
start=time.perf_counter();contract=R/'experiments/quotient_raw_floor_contract_v1_2026-10-17/verification.json';v=json.loads(contract.read_text());assert v['all_pass'] and all(sha(k)==h for k,h in v['bindings'].items())
ep=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json';old=R/'experiments/neuron_proxy_budget_trial_v2_2026-10-17/model';admission=json.loads((old/'initial_physical_verification.json').read_text());assert admission['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass']
files=[Path(__file__).resolve(),R/'tools/compiled_quotient_raw_floor_v1_2026_10_17.py',contract,ep,old/'floors.json',old/'initial.json',old/'initial_physical_verification.json',BINARY]
baseproof=R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json';payload=baseproof.parent/'node_base.u128le'
benchmark=R/'experiments/xtea_raw_floor_abba_v3_2026-10-17/verification.json'
gate=json.loads(benchmark.read_text());assert gate['both_orders_astar_component_faster'] and gate['all_four_complete_floors_paths_fraction_RC_and_singleparents_pass']
files += [baseproof,payload,benchmark]
bindings={str(p):sha(p) for p in files}
for p in [ep,old/'floors.json',old/'initial.json']:assert sha(p)==admission['bindings'][str(p)]
write('protocol.json',dict(bindings=bindings,domain='All77106neuron connection IDs. NET order ascending, per-NET CID ascending, raw-only exact retained-prefix A*; no budget cap beyond proven simple-path raw bound.',floor_policy='Same directed quotient groups as factoryv2; actual authenticated node-base+span floor used. Actual authenticated node-base+span floor tables paid cold, same factory as current model; objective price weight remains0 so raw values are unaffected.',tie_policy='Equal-cost paths may differ. Compare every exact floor and independently audit physical paths/FractionRC/single parents. No initial-path equality or full-model equivalence claim.',scope='Correctness-first real-design pilot; one timing observation only, not a matched benchmark.'))
print('NEURON RAW FLOOR load start',flush=True)
graph,digest,nodes,f,rc,queries=load_endpoints(ep);assert len(queries)==77106 and all(c>0 for c in f['capacities']);bindings[str(graph)]=digest
baseproof=R/'experiments/titan23_neuron_node_base_wide_v1_2026-10-13/verification.json';bp=json.loads(baseproof.read_text());payload=baseproof.parent/'node_base.u128le'
assert bp['nodes']==len(nodes) and bp['scale']==rc.scale and bp['payload_format']=='unsigned128_little_endian'
assert sha(payload)==bp['bindings'][str(payload)] and sha(ep)==bp['bindings'][str(ep)]
bindings[str(baseproof)]=sha(baseproof);bindings[str(payload)]=sha(payload)
base=tuple(lo+(hi<<64) for lo,hi in struct.iter_unpack('<QQ',payload.read_bytes()));assert len(base)==len(nodes)
print('NEURON RAW FLOOR loaded',len(nodes),'nodes',len(f['edge_ids']),'edges',flush=True)
load_done=time.perf_counter();g=create(f,rc.increments,[rc.initial(i) for i in range(len(nodes))],nodes,base,rc.scale//(20*10**9))
print('NEURON RAW FLOOR quotient ready',flush=True)
setup_done=time.perf_counter();groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((old/'floors.json').read_text())};oldrecords={r['connection_id']:r for r in json.loads((old/'initial.json').read_text())['records']};records=[];search_seconds=0;path_changes=0
for net,qs in sorted(groups.items()):
 assert len({q['source'] for q in qs})==1;t=tree(g,qs[0]['source'])
 for q in sorted(qs,key=lambda q:q['connection_id']):
  tick=time.perf_counter();a=t.expand(q['sink']);search_seconds+=time.perf_counter()-tick
  assert a['status']=='COMMITTED' and a['raw']==floors[q['source'],q['sink']]
  path=[f['edge_ids'][slot] for slot in a['path_slots']];assert rc.path(q['source'],q['sink'],path)==a['raw']
  records.append(dict(q,physical_edge_ids=path,minimum_integer=a['raw']));path_changes+=path!=oldrecords[q['connection_id']]['answer']['physical_edge_ids']
  if len(records)%10000==0:print('NEURON RAW FLOOR progress',len(records),flush=True)
search_done=time.perf_counter();stats=g.total_stats[:];cache=g.cache_report();g.close()
del t,g,nodes
gc.collect()
print('NEURON RAW FLOOR all floors done; independent XML audit starts',flush=True)
xml=ImmutableXMLAudit(graph,digest);ids,classes,switches,checked=read(graph);assert checked==digest;parents=defaultdict(dict)
for r in records:
 u=r['source'];used={u};res,cap=classes[ids[u]];delay=res*cap/2
 for eid in r['physical_edge_ids']:
  e=xml.graph.edges[eid];assert e.source==u and e.sink not in used and xml.graph.nodes[e.sink].capacity>0;v=e.sink
  incoming=(u,eid);assert v not in parents[r['net_id']] or parents[r['net_id']][v]==incoming;parents[r['net_id']][v]=incoming
  used.add(v);delay+=arc_delay(classes,switches,ids[v],e.switch_id);u=v
 assert u==r['sink'] and delay*rc.scale==r['minimum_integer']
assert {r['connection_id'] for r in records}=={q['connection_id'] for q in queries}
assert all(sha(k)==h for k,h in bindings.items())
write('paths.json',records);write('verification.json',dict(bindings=bindings,paths_sha256=sha(D/'paths.json'),all77106_exact_archived_floors_original_XML_Fraction_RC_and_singleparents_pass=True,connections=len(records),NETs=len(groups),changed_equal_cost_initial_paths=path_changes,load_and_authentication_seconds=load_done-start,quotient_graph_setup_seconds=setup_done-load_done,all_expand_calls_seconds=search_seconds,search_reconstruction_validation_seconds=search_done-setup_done,independent_XML_audit_and_final_auth_seconds=time.perf_counter()-search_done,total_seconds=time.perf_counter()-start,native_work_totals=stats,cache_report=cache,scope='One raw-only initial-floor pilot on exposed neuron, every connection included; no old equal-path parity, full feedback/metrics, paired speedup, native utility or hardware result. Setup/auth/audits and nested clocks are reported separately.'))
print(json.dumps(dict(connections=len(records),NETs=len(groups),changed_equal_cost_initial_paths=path_changes,all_expand_calls_seconds=search_seconds,total_seconds=time.perf_counter()-start),indent=2),flush=True)
