"""Actual frozen seed import, no query search: component cost attribution."""
import sys,json,time,cProfile,pstats,io
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from tree_floor_pareto_constraints_predictor_v7 import predict
base=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip';ep=base/'endpoints.json';eventfile=R/'experiments/mcnc_prefix_wire04_v11_2026-10-07/dsip/batch7.json';out=R/'experiments/seed_import_profile_v1_2026-10-07';out.mkdir();bindings={str(p):sha(p) for p in (ep,eventfile)};bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()});bindings.update(closure([Path(__file__)]));(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,repeats=5,profiled_repeat=6,scope='Frozen real seed import with no queries, not full sequence timing or incremental equivalence. Same graph reused; no cold claim.'))+'\n');graph,digest,nodes,f,rc,queries=load_endpoints(ep);event=json.loads(eventfile.read_text());seed=event['before_records'];spans=[0]*len(nodes);rows=[]
for i in range(5):
 t=time.perf_counter();state=predict(f,rc,[],{},seed_records=seed,spans=spans);elapsed=time.perf_counter()-t;assert state['records']==sorted(seed,key=lambda r:r['connection_id']) and {str(n):c for n,c in state['ledger'].items()}=={str(n):c for n,c in event['before_ledger'].items()} and state['failure'] is None;rows.append(elapsed)
prof=cProfile.Profile();prof.enable();state=predict(f,rc,[],{},seed_records=seed,spans=spans);prof.disable();prof.dump_stats(str(out/'seed_import.prof'));stream=io.StringIO();pstats.Stats(prof,stream=stream).strip_dirs().sort_stats('cumulative').print_stats(25);(out/'profile.txt').write_text(stream.getvalue());assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,seed_records=len(seed),seed_edges=sum(len(r['answer']['physical_edge_ids']) for r in seed),unprofiled_seconds=rows,mean_seconds=sum(rows)/len(rows),scope='No-query seed reconstruction only. Profiling overhead separate; no attribution of all full-sequence cost or speed claim.'),indent=2)+'\n');print('PASS seed import',len(seed),rows,flush=True)
