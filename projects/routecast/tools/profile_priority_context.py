"""Cold/hot context cProfile diagnosis; output binding, no optimization yet."""
import cProfile,pstats,json,time
from pathlib import Path
from pre_route_endpoints import sha
from cached_rr_endpoint_context import clear_cache,STATS
from owner_union_wire_rc_context_cached import OwnerUnionWireRCContext
from freeze_priority_family import closure
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/priority_context_profile_2026-10-07';out.mkdir();ep=ROOT/'experiments/priority_frozen_evaluation_2026-10-07/n128/endpoints.json';endpoint=json.loads(ep.read_text());sources=closure([Path(__file__)]);inputs={str(ep):sha(ep),**{x['path']:x['sha256'] for x in endpoint['inputs'].values()}};assert all(sha(f)==d for f,d in inputs.items());p=dict(sources=sources,inputs=inputs,scope='Cold then hot same128 context profiling; profile instrumentation overhead included, cumulative clocks nested/nonadditive. Context only, no search/quality/fullgain claim. RR cache cleared once then reused, OS caches not reset.');(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');clear_cache();rows=[]
for label in ['cold','hot']:
 profiler=cProfile.Profile();tick=time.perf_counter();profiler.enable();ctx=OwnerUnionWireRCContext(ep);profiler.disable();seconds=time.perf_counter()-tick;profiler.dump_stats(str(out/(label+'.prof')))
 with (out/(label+'.txt')).open('w') as f:pstats.Stats(profiler,stream=f).strip_dirs().sort_stats('cumulative').print_stats(40)
 fields=ctx.rc.fields;vector=dict(scale=ctx.rc.scale,nodes=len(fields['node_ids']),edges=len(fields['edge_ids']),native_cost_sha256=__import__('hashlib').sha256(ctx.native.arrays[3].tobytes()).hexdigest(),native_increment_sha256=__import__('hashlib').sha256(ctx.native.arrays[5].tobytes()).hexdigest());rows.append(dict(label=label,profiled_seconds=seconds,cache_stats=dict(STATS),state=vector));print(label,seconds,flush=True)
assert rows[0]['state']==rows[1]['state'];assert all(sha(f)==d for f,d in sources.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,files={str(f):sha(f) for f in out.iterdir() if f.is_file() and f.name!='receipt.json'},complete=True),indent=2)+'\n')
