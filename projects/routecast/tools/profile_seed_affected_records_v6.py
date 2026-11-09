"""Actual frozen seed import, no query search: component cost attribution."""
import sys,json,time,cProfile,pstats,io
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_floor_pareto_affected_seed_v11 import predict,EdgeSlotContext,SeedContext
from tree_floor_pareto_edge_context_v8 import predict as reference
from remaining_delay_session_cache_v5 import RemainingDelayCache
base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';ep=base/'endpoints.json';eventfile=R/'experiments/mcnc_prefix_wire04_v11_2026-10-07/dsip/batch7.json';out=R/'experiments/seed_affected_records_v6_2026-10-07';out.mkdir();bindings={str(p):sha(p) for p in (ep,eventfile)};bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});bindings[str(eventfile.parent/'floors.json')]=sha(eventfile.parent/'floors.json');bindings.update(closure([Path(__file__)]));(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,repeats=5,profiled_repeat=6,scope='Frozen real seed import with no queries, not full sequence timing or incremental equivalence. Actual immutable cache field/RC snapshots reused, factory/finalize costs excluded from component timings; no cold claim.'))+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);cache=RemainingDelayCache(graph,digest,f,rc,out/'bounds',max_entries=256);f=cache.fields;rc=cache.rc;event=json.loads(eventfile.read_text());seed=event['before_records'];spans=[0]*len(nodes);t=time.perf_counter();context=EdgeSlotContext(f);prepared_seed=SeedContext(f,rc,seed,context);preparation=time.perf_counter()-t;rows=[]
for i in range(5):
 t=time.perf_counter();state=predict(f,rc,[],{},seed_context=prepared_seed,spans=spans,edge_context=context);elapsed=time.perf_counter()-t;assert state['records']==sorted(seed,key=lambda r:r['connection_id']) and {str(n):c for n,c in state['ledger'].items()}=={str(n):c for n,c in event['before_ledger'].items()} and state['failure'] is None;rows.append(elapsed)
plain=reference(f,rc,[],{},seed_records=seed,spans=spans,edge_context=context);assert state==plain
state['records'].clear();assert predict(f,rc,[],{},seed_context=prepared_seed,spans=spans,edge_context=context)==plain
try:prepared_seed.fork(dict(f),rc,set())
except ValueError:pass
else:raise AssertionError('replaced graph accepted')
pending=[q for q in queries if q['connection_id'] not in {r['connection_id'] for r in seed}][:1];floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads((eventfile.parent/'floors.json').read_text())};assert predict(f,rc,pending,floors,seed_context=prepared_seed,spans=spans,edge_context=context,remaining_cache=cache)==reference(f,rc,pending,floors,seed_records=seed,spans=spans,edge_context=context,remaining_cache=cache)
prof=cProfile.Profile();prof.enable();state=predict(f,rc,[],{},seed_context=prepared_seed,spans=spans,edge_context=context);prof.disable();prof.dump_stats(str(out/'seed_import.prof'));stream=io.StringIO();pstats.Stats(prof,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(25);(out/'profile.txt').write_text(stream.getvalue());cache.finalize();(out/'cache_receipt.json').write_text(json.dumps(cache.summary())+'\n');assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,seed_records=len(seed),seed_edges=sum(len(r['answer']['physical_edge_ids']) for r in seed),unprofiled_seconds=rows,mean_seconds=sum(rows)/len(rows),edge_context_preparation_seconds=preparation,scope='No-query seed reconstruction only. Profiling overhead separate; no attribution of all full-sequence cost or speed claim.'),indent=2)+'\n');print('PASS seed import',len(seed),rows,flush=True)
