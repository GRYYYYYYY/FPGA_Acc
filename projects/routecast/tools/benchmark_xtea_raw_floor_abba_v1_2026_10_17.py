"""Fresh initial-engine states, real XTEA base, ABBA all connection floors."""
import json,hashlib,struct,time
from collections import defaultdict
from pathlib import Path
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compiled_quotient_model_factory_v2 import create,BINARY
from compiled_quotient_raw_floor_v1_2026_10_17 import tree
from lazy_compact_wide_sparse_structural_objective_search_v2 import Search
from immutable_xml_prediction_audit import ImmutableXMLAudit
from buffered_rc_node_classes import read,arc_delay
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_raw_floor_abba_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(n,d):
 with (D/n).open('x') as f:json.dump(d,f,indent=2);f.write('\n')
prep=time.perf_counter();ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';baseproof=R/'experiments/xtea_node_base_wide_v1_2026-10-13/verification.json';payload=baseproof.parent/'node_base.u128le';old=R/'experiments/xtea_proxy_budget_audit_fixture_v1_2026-10-17/model';legacy=R/'experiments/wide_cost_backend_build_v1_2026-10-13/search.so'
contract=R/'experiments/quotient_raw_floor_contract_v1_2026-10-17/verification.json';pilot=R/'experiments/xtea_quotient_raw_floor_pilot_v1_2026-10-17/verification.json'
assert json.loads(contract.read_text())['all_pass'] and json.loads(pilot.read_text())['all2450_exact_archived_floors_original_XML_Fraction_RC_and_singleparents_pass']
from source_binding_v2 import closure
bindings=closure([Path(__file__).resolve()])
for p in [ep,baseproof,payload,old/'floors.json',old/'initial.json',contract,pilot,BINARY,legacy]:bindings[str(p)]=sha(p)
bp=json.loads(baseproof.read_text());assert bp['bindings'][str(payload)]==sha(payload) and bp['bindings'][str(ep)]==sha(ep)
graph,digest,nodes,f,rc,queries=load_endpoints(ep);bindings[str(graph)]=digest;assert len(queries)==2450 and all(c>0 for c in f['capacities'])
assert bp['nodes']==len(nodes) and bp['scale']==rc.scale and bp['payload_format']=='unsigned128_little_endian'
base=tuple(lo+(hi<<64) for lo,hi in struct.iter_unpack('<QQ',payload.read_bytes()));assert len(base)==len(nodes)
groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((old/'floors.json').read_text())};oldpaths={r['connection_id']:r['answer']['physical_edge_ids'] for r in json.loads((old/'initial.json').read_text())['records']}
common_seconds=time.perf_counter()-prep
write('protocol.json',dict(bindings=bindings,order=['hybrid','raw_astar','raw_astar','hybrid'],domain='All2450connections/1448NETs, original graph and actual initialized native node-base payload. Current pitch4/targetLRU512 quotient factory, current lazy-wide hybrid engine.',paid_scope='Both arms create/destroy fresh quotient graph because current producer already pays it before floors. Hybrid additionally creates/prepares/closes its current floor engine. A* pays fresh cold potential tables with actual node-base+span floor. Include every expansion, reconstruction, floor/path checks and output serialization. Shared graph/base loading/authentication reported separately. Independent XML audits occur outside each component clock and are paid/reported separately.',gate='Only both order-reversed component pairs faster and full correctness permits considering a larger pilot. No full-model or stable/end-to-end gain assertion; changed initial tie paths require complete new model validation.',timing_limits='One process, n2/mode, no warmup or host/cache isolation. Same immutable graph reused across arms, fresh native search/table states every arm.'))
results=[];all_records=[]
for index,mode in enumerate(['hybrid','raw_astar','raw_astar','hybrid']):
 begin=time.perf_counter();engine=None
 if mode=='hybrid':engine=Search(f,rc,legacy,base);engine.prepare({},0,structural=False)
 g=create(f,engine.raw_inc if engine else rc.increments,[rc.initial(i) for i in range(len(nodes))],nodes,base,rc.scale//(20*10**9))
 setup_done=time.perf_counter();records=[];query_seconds=0
 for net,qs in sorted(groups.items()):
  source=qs[0]['source'];assert all(q['source']==source for q in qs)
  if mode=='hybrid':
   tick=time.perf_counter();raw,parents,found=engine.search(source,{q['sink'] for q in qs});query_seconds+=time.perf_counter()-tick
  else:t=tree(g,source)
  for q in sorted(qs,key=lambda q:q['connection_id']):
   if mode=='hybrid':
    assert q['sink'] in found;delay=raw[q['sink']];u=q['sink'];path=[];seen={u}
    while u!=source:
     u,slot=parents[u];assert u not in seen;seen.add(u);path.append(f['edge_ids'][slot])
    path.reverse()
   else:
    tick=time.perf_counter();a=t.expand(q['sink']);query_seconds+=time.perf_counter()-tick;assert a['status']=='COMMITTED';delay=a['raw'];path=[f['edge_ids'][slot] for slot in a['path_slots']]
   assert delay==floors[source,q['sink']] and rc.path(source,q['sink'],path)==delay
   records.append(dict(q,minimum_integer=delay,physical_edge_ids=path))
 search_done=time.perf_counter();cache=g.cache_report();g.close()
 if engine:engine.close()
 write(f'{index}_{mode}_paths.json',records)
 elapsed=time.perf_counter()-begin
 changed=sum(r['physical_edge_ids']!=oldpaths[r['connection_id']] for r in records)
 if mode=='hybrid':assert changed==0
 results.append(dict(index=index,mode=mode,component_seconds=elapsed,setup_seconds=setup_done-begin,query_calls_seconds=query_seconds,search_and_reconstruction_seconds=search_done-setup_done,cache_teardown_and_serialization_seconds=elapsed-(search_done-begin),connections=len(records),changed_equal_cost_paths=changed,cold_tables_built=cache['reverse_table_builds']))
 all_records.append(records);print(json.dumps(results[-1]),flush=True)
# Independent original XML RC/topology and same NET parent audit for all arms.
audit_begin=time.perf_counter();xml=ImmutableXMLAudit(graph,digest);ids,classes,switches,checked=read(graph);assert checked==digest
for records in all_records:
 parents=defaultdict(dict)
 for r in records:
  u=r['source'];seen={u};res,cap=classes[ids[u]];delay=res*cap/2
  for eid in r['physical_edge_ids']:
   e=xml.graph.edges[eid];assert e.source==u and e.sink not in seen and xml.graph.nodes[e.sink].capacity>0;v=e.sink
   assert v not in parents[r['net_id']] or parents[r['net_id']][v]==(u,eid);parents[r['net_id']][v]=(u,eid)
   seen.add(v);delay+=arc_delay(classes,switches,ids[v],e.switch_id);u=v
  assert u==r['sink'] and delay*rc.scale==r['minimum_integer']
 assert {r['connection_id'] for r in records}=={q['connection_id'] for q in queries}
audit_seconds=time.perf_counter()-audit_begin
assert all_records[0]==all_records[3] and all_records[1]==all_records[2]
pairs=[]
for a,b in [(0,1),(3,2)]:
 x=results[a]['component_seconds'];y=results[b]['component_seconds'];pairs.append(dict(hybrid_index=a,astar_index=b,hybrid_seconds=x,astar_seconds=y,saved_seconds=x-y,fractional_saving=(x-y)/x))
write('rows.json',results);assert all(sha(k)==h for k,h in bindings.items())
outputs={str(p):sha(p) for p in D.glob('*_paths.json')}
write('verification.json',dict(bindings=bindings,outputs=outputs,rows_sha256=sha(D/'rows.json'),all_four_complete_floors_paths_fraction_RC_and_singleparents_pass=True,within_mode_all_paths_identical=True,common_loading_and_auth_seconds=common_seconds,shared_full_independent_audit_seconds=audit_seconds,pairs=pairs,both_orders_astar_component_faster=all(p['saved_seconds']>0 for p in pairs),scope='Initial-floor component only. Actual static node-base+span tables paid cold in A* arms. Four fresh engine/quotient states, reused immutable graph, n2/mode uncontrolled host/cache. This does not include full feedback/budget ledger, native routing, paired continuous workflow or quality/hardware evidence.'))
print(json.dumps(dict(pairs=pairs,both_orders_astar_component_faster=all(p['saved_seconds']>0 for p in pairs))),flush=True)
