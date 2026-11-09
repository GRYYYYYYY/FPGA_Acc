"""MMC A-B-A frozen-frame cache trial, charged setup and full byte parity."""
import ast,json,time,sys
from pathlib import Path
from collections import defaultdict,Counter
from pre_route_endpoints import sha
from compact_stream_rc_endpoint_context_v1 import load_endpoints
from model_inventory_snapshot_v2 import capture
from serialize_whole_net_subset_pin_index_v2 import serialize_subset
from net_fragment_serializer_v1 import Session
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_net_fragment_cache_v1_2026-10-21';D.mkdir()
M=R/'experiments/mmc_native_cached_feedback_pilot_v1_2026-10-18/model';epf=R/'experiments/mmc_native_state_swap_inputs_v1_2026-10-18/demand/endpoints.json';selector=R/'tools/select_resident_native_seed_subset_v1.py'
files=[Path(__file__),epf,selector,M/'receipt.json',M/'round0.json',M/'round1.json',R/'tools/net_fragment_serializer_v1.py',R/'tests/test_net_fragment_serializer_v1.py',R/'tools/model_inventory_snapshot_v1.py',R/'tools/model_inventory_snapshot_v2.py',R/'tools/compact_stream_rc_endpoint_context_v1.py',R/'tools/serialize_whole_net_subset_pin_index_v2.py']
bindings={str(f):sha(f) for f in files}
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'order':['round0','round1','round0'],'scope':'Prepared exposed MMC states only; no model or native execution. Setup graph/RC loading, immutable snapshot and cache cold build charged. Every call retains endpoint/pin/whole graph guards and complete output; compare full reference bytes/pins. A-B-A is correctness/invalidation evidence, not independent placements or paired end-to-end speedup.','cache_text_payload_budget':64*1024*1024,'max_entries':100000,'native_calls':0},indent=2)+'\n')
start=time.perf_counter();t=start;ep=json.loads(epf.read_text());before=json.loads((M/'receipt.json').read_text());assert all(sha(k)==h for k,h in before['bindings'].items())
for f in [M/'round0.json',M/'round1.json']:assert sha(f)==before['files'][str(f)]
graph,digest,nodes,fields,rc,queries=load_endpoints(epf);snapshot=capture(graph,digest,nodes,fields);setup=time.perf_counter()-t;print('SETUP',setup,flush=True)
tree=ast.parse(selector.read_text());loop=next(n for n in tree.body if isinstance(n,ast.For));begin=next(i for i,n in enumerate(loop.body) if isinstance(n,ast.For) and ast.unparse(n.target)=='rec');end=next(i for i,n in enumerate(loop.body) if i>begin and isinstance(n,ast.Assert));code=compile(ast.Module(body=loop.body[begin:end],type_ignores=[]),str(selector),'exec')
session=Session();rows=[];previous={}
for index,frame in enumerate(['round0','round1','round0']):
 tick=time.perf_counter();c=json.loads((M/(frame+'.json')).read_text())
 for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256']
 scope=dict(c=c,ep=ep,xml=snapshot,groups=defaultdict(list),Counter=Counter);exec(code,scope)
 records=scope['records'];pending=scope['pending'];ids={r['connection_id'] for r in records};allids={q['connection_id'] for q in ep['connections']};assert len(ids)==len(records) and not ids.intersection(pending) and ids|set(pending)==allids
 ledger=Counter(n for net in scope['kept'] for n in scope['owners'][net]);assert ledger==scope['ledger'] and all(v<=snapshot.graph.nodes[n].capacity for n,v in ledger.items())
 candidate={'records':records};selection=time.perf_counter()-tick;args=(epf,Path(ep['inputs']['native_identity']['path']),Path(ep['inputs']['place']['path']),snapshot)
 tick=time.perf_counter();reference,pins=serialize_subset(candidate,*args);reference_seconds=time.perf_counter()-tick
 oldstats=dict(session.stats);tick=time.perf_counter();actual,actualpins=session.serialize(candidate,*args);cached_seconds=time.perf_counter()-tick
 assert actual==reference and actualpins==pins
 if frame in previous:assert sha(M/(frame+'.json'))==previous[frame]['input_sha256'] and actual==previous[frame]['output']
 else:previous[frame]={'input_sha256':sha(M/(frame+'.json')),'output':actual}
 tick=time.perf_counter();out=D/f'{index}_{frame}.route';out.write_text(actual);write_seconds=time.perf_counter()-tick
 stats={k:session.stats[k]-oldstats[k] for k in session.stats};rows.append({'index':index,'frame':frame,'selection_and_reauthentication_seconds':selection,'reference_complete_serializer_seconds':reference_seconds,'cached_complete_serializer_seconds':cached_seconds,'complete_output_write_seconds':write_seconds,'cache_delta':stats,'cache_entries':len(session._entries),'cache_text_bytes':session._bytes,'selected_NETs':len(scope['kept']),'selected_connections':len(records),'seed_bytes_exact':True,'pins_exact':True,'output_sha256':sha(out)})
 assert session._bytes<=session.max_text_bytes and len(session._entries)<=session.max_entries
 print(json.dumps(rows[-1]),flush=True)
assert rows[1]['cache_delta']['hits']>0 and rows[2]['cache_delta']['hits']>0
assert all(sha(k)==h for k,h in bindings.items())
for spec in ep['inputs'].values():assert sha(spec['path'])==spec['sha256']
receipt={'setup_graph_RC_snapshot_seconds':setup,'rows':rows,'total_with_reference_verification_seconds':time.perf_counter()-start,'all_reference_bytes_and_pins_exact':True,'bindings':bindings,'scope':'Prepared A-B-A component trial, setup/cold cache/output/guards measured, full reference audit additionally paid. No model/native execution or end-to-end/unseen gain.'}
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('MMC CACHE A-B-A EXACT PARITY PASS',flush=True)
