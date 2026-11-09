"""Two ABBA blocks, exact raw128/256 compatibility and all paid component work."""
import gc,json,hashlib,struct,time,resource
from collections import defaultdict
from pathlib import Path
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from compiled_quotient_model_factory_v2 import create as create256,BINARY as BINARY256
from compiled_quotient_adaptive128_factory_v1_2026_10_18 import create as create128,BINARY as BINARY128
from compiled_quotient_raw_floor_v1_2026_10_17 import tree as tree256
from compiled_quotient_adaptive128_v1_2026_10_18 import raw_tree as tree128
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_adaptive128_raw_abba_v1_2026-10-18';D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def write(n,v):
 with (D/n).open('x') as f:json.dump(v,f,indent=2);f.write('\n')
limit=2*2**30;free=int(Path('/sys/fs/cgroup/memory.max').read_text())-int(Path('/sys/fs/cgroup/memory.current').read_text());assert free>=limit+8*2**30;resource.setrlimit(resource.RLIMIT_AS,(limit,limit))
ep=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';bp=R/'experiments/xtea_node_base_wide_v1_2026-10-13/verification.json';payload=bp.parent/'node_base.u128le';ref=R/'experiments/xtea_raw_floor_proxy_budget_fixture_v1_2026-10-17/model';contract=R/'experiments/quotient_adaptive128_direct_contract_v1_2026-10-18/verification.json';v=json.loads(contract.read_text());assert v['all_pass'] and all(sha(k)==h for k,h in v['bindings'].items())
import sys
sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
bindings=closure([Path(__file__).resolve()])
for p in [ep,bp,payload,ref/'initial.json',ref/'initial_physical_verification.json',contract,BINARY256,BINARY128]:bindings[str(p)]=sha(p)
physical=json.loads((ref/'initial_physical_verification.json').read_text());assert physical['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and physical['bindings'][str(ref/'initial.json')]==sha(ref/'initial.json')
order=['wide256','adaptive128','adaptive128','wide256']*2
write('protocol.json',dict(bindings=bindings,order=order,arm_count=8,complete_connections_per_arm=2450,gate='All4order-reversed adjacent pairs must save at least5percent component wall time, all2450paths/values and per-query first3native counters identical. No default/fullmodel/large-design promotion.',paid_scope='Fresh quotient graph/native context per arm, actual node-base/span tables cold, lazy fast workspace allocation, all expansions/conversions/path checks/per-query-counter comparison/serialization, close/owner release/GC included. Common graph/auth/loading separate. Same-process n4/mode, no host/cache control, original neuron audit may run concurrently; no general speed claim.'))
prep=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(ep);assert len(queries)==2450 and all(c>0 for c in f['capacities']);bindings[str(graph)]=digest
proof=json.loads(bp.read_text());assert proof['bindings'][str(payload)]==sha(payload) and proof['scale']==rc.scale and proof['nodes']==len(nodes)
base=tuple(lo+(hi<<64) for lo,hi in struct.iter_unpack('<QQ',payload.read_bytes()));groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
reference={r['connection_id']:r for r in json.loads((ref/'initial.json').read_text())['records']};prep_seconds=time.perf_counter()-prep
reference_stats=None

def arm(index,mode,reference_stats):
 begin=time.perf_counter();factory,make_tree=(create256,tree256) if mode=='wide256' else (create128,tree128)
 g=factory(f,rc.increments,[rc.initial(n) for n in range(len(nodes))],nodes,base,rc.scale//(20*10**9));setup_done=time.perf_counter();records=[];stats=[]
 for net,qs in sorted(groups.items()):
  t=make_tree(g,qs[0]['source'])
  for q in sorted(qs,key=lambda q:q['connection_id']):
   a=t.expand(q['sink']);assert a['status']=='COMMITTED';path=[f['edge_ids'][s] for s in a['path_slots']];old=reference[q['connection_id']]
   assert path==old['answer']['physical_edge_ids'] and a['raw']==old['floor_integer']==rc.path(q['source'],q['sink'],path)
   row=tuple(g.last_stats[:3]);assert row==(reference_stats[len(stats)] if reference_stats is not None else row);stats.append(row)
   records.append(dict(connection_id=q['connection_id'],floor=a['raw'],path=path))
 counts=dict(fast128=getattr(g,'fast_calls',0),fallback256=getattr(g,'fallback_calls',0));cache=g.cache_report();g.close();del t,g
 if mode=='adaptive128':assert counts==dict(fast128=2450,fallback256=0)
 write(f'{index}_{mode}.json',dict(records=records,native_work_per_query=stats))
 del records;gc.collect();elapsed=time.perf_counter()-begin
 return dict(index=index,mode=mode,component_seconds=elapsed,setup_seconds=setup_done-begin,lane_calls=counts),stats
rows=[]
for i,mode in enumerate(order):
 r,stats=arm(i,mode,reference_stats)
 if reference_stats is None:reference_stats=stats
 rows.append(r);print(json.dumps(r),flush=True)
pairs=[]
for a,b in [(0,1),(3,2),(4,5),(7,6)]:
 x,y=rows[a]['component_seconds'],rows[b]['component_seconds'];pairs.append(dict(wide_index=a,adaptive_index=b,wide_seconds=x,adaptive_seconds=y,saved_seconds=x-y,fractional_saving=(x-y)/x))
write('rows.json',rows);assert all(sha(k)==h for k,h in bindings.items())
outputs={str(p):sha(p) for p in D.glob('*_wide256.json')};outputs.update({str(p):sha(p) for p in D.glob('*_adaptive128.json')})
write('verification.json',dict(bindings=bindings,outputs=outputs,rows_sha256=sha(D/'rows.json'),all8arms_complete_paths_floors_and_per_query_work_identical=True,common_loading_seconds=prep_seconds,pairs=pairs,all4pairs_save_at_least5percent=all(p['fractional_saving']>=.05 for p in pairs),scope='Small exposed XTEA raw-initial component only. Reference paths are identical to separately physically audited initial paths; no fresh independent XML rerun is claimed here. No full-feedback, large-design, native QoR, end-to-end, heldout or hardware result.'))
print(json.dumps(dict(pairs=pairs,all4pairs_save_at_least5percent=all(p['fractional_saving']>=.05 for p in pairs))),flush=True)
