"""All-case initial owner-union predictor, no native routes or labels read by search."""
import json,time,ctypes
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from owner_union_wire_rc_context_cached import OwnerUnionWireRCContext
from owner_union_initial_prediction_engine import predict_joint
from owned_reverse_graph import OwnedReverseGraph
from bitonic_owner_wire_four_repair_engine import repair_moved_history
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/bitonic_physical_endpoints_2026-10-07';out=ROOT/'experiments/bitonic_four_repair_profile_2026-10-07';r=json.loads((base/'receipt.json').read_text());out.mkdir();names=['bitonic_owner_wire_four_repair_engine.py','single_scan_residual_frontier.py','owned_reverse_graph.py','owner_union_initial_prediction_engine.py','owner_union_wire_rc_context_cached.py','wire_penalty_rc_context_cached.py','persistent_rc_context_cached.py','cached_rr_endpoint_context.py','integer_rc_context_memo.py','native_capacity_rc_search.py','nonzero_rc_endpoint_context_memo.py'];sources={str(ROOT/'tools'/n):sha(ROOT/'tools'/n) for n in names};sources[str(Path(__file__))]=sha(Path(__file__));binary=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so';sources[str(binary)]=sha(binary);sources[str(binary.with_suffix('.cpp'))]=sha(binary.with_suffix('.cpp'))
inputs={str(base/f'n{n}/endpoints.json'):sha(base/f'n{n}/endpoints.json') for n in [4,8,16]};protocol=dict(sources=sources,inputs=inputs,cohort=[4,8,16],weight_ns='1/20',max_labels=10000,connection_cap_ns=1,fallback_limit=0,order='ascending NET and CID',max_whole_net_releases=4,history='unchanged quadratic raw-count cost',scope='Instrumentation-only reproduction of frozen50ps four-release algorithm; require initial/final candidate byteparity before using cost diagnosis. NEW four-release bounded repair on UNREACHABLE only; budget-connected relaxedwitness ownerblocker release inherited, label-limit not repaired. Allcases actualinitial rerun; prospective development, not heldout. NEW development comparison uses unchanged exact reverse-delay sink bound with native dynamiccost>=baseRC; 128MiB boundvectorpayload cache, not totalRSS. Following observed failedcase, not heldout. Same1ns/50ps/10000labels/no fallback/NET order. Frozen before initial predictions, owner cost already frozen before native capture. New initial orchestration freezes AFTER native reference availability: not fully prospective source-complete heldout proof. No native route/delay/occupancy read by driver or search; pre-route endpoints only. No repair/minimum-delay fallback, all failures retained, not incremental move acceptance. Fixed1ns/50ps inherited, no tuning.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for n in protocol['cohort']:
 ep=base/f'n{n}/endpoints.json';assert sha(ep)==inputs[str(ep)];start=time.perf_counter();ctx=OwnerUnionWireRCContext(ep,weight_ns=Fraction(1,20));owned=OwnedReverseGraph(ctx.native.n,len(ctx.rc.fields['edge_ids']),ctx.native.ptrs[0],ctx.native.ptrs[1],ctx.native.ptrs[2],ctx.native.ptrs[5],binary);ctx.native.lib.rc_query=owned.bridge;setup=time.perf_counter()-start
 phases={}
 def instrument(obj,name,label):
  callback=getattr(obj,name);values={'calls':0,'seconds':0.0};phases[label]=values
  def wrapper(*args,**kwargs):
   tick=time.perf_counter()
   try:return callback(*args,**kwargs)
   finally:values['calls']+=1;values['seconds']+=time.perf_counter()-tick
  setattr(obj,name,wrapper)
 for obj,name,label in [(ctx,'query','query_total'),(ctx.native,'set_other','other_publish'),(ctx.native,'query','native_query'),(ctx,'set_wire_owner_union','owner_cost_update'),(ctx,'set_history','history_cost_update')]:instrument(obj,name,label)
 start=time.perf_counter();candidate=predict_joint(ctx,max_labels=10000,fallback_limit=0);seconds=time.perf_counter()-start;candidate['history']={};initial_file=out/f'n{n}_initial.json';initial_file.write_text(json.dumps(candidate,indent=2)+'\n');initial_hash=sha(initial_file);repair_seconds=0
 if candidate['failure'] is not None and candidate['failure']['status']=='UNREACHABLE':
  repair_start=time.perf_counter();candidate=repair_moved_history(ctx,candidate);repair_seconds=time.perf_counter()-repair_start
 cache_stats=(ctypes.c_uint64*6)();owned.lib.rc_graph_cache_stats.argtypes=[ctypes.c_uint64,ctypes.POINTER(ctypes.c_uint64)];owned.lib.rc_graph_cache_stats.restype=ctypes.c_int;assert owned.lib.rc_graph_cache_stats(owned.handle,cache_stats)==0
 (out/f'n{n}_profile.json').write_text(json.dumps({'phases':phases,'reverse_cache':dict(zip(['hits','misses','invalidations','evictions','payload_bytes','payload_limit_bytes'],map(int,cache_stats))),'scope':'Actual samecase instrumentation; query_total nests other_publish and native_query; never add nested clocks. Initial plus repair stages combined. Single new run, measured overhead not theoretical minimum or stable speedup.'},indent=2)+'\n')
 owned.close();file=out/f'n{n}.json';file.write_text(json.dumps(candidate,indent=2)+'\n');rows.append(dict(count=n,status=candidate['status'],completed=candidate['completed_connections'],required=candidate['required_connections'],failure=candidate['failure'],setup_seconds=setup,search_seconds=seconds,repair_seconds=repair_seconds,repairs=candidate.get('repairs',0),initial_sha256=initial_hash,candidate_sha256=sha(file)));print(rows[-1],flush=True)
assert all(sha(f)==h for f,h in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=True),indent=2)+'\n')
