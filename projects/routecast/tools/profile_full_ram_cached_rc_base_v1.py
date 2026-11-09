"""Full-graph cached preparation equality, no search or speedup inference."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from cached_bound_rc_base_v1 import CachedBoundRCBase
from prepared_csr import write,read
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_cached_rc_base_profile_v1_2026-10-09';D.mkdir(exist_ok=False)
B=E/'full_ram_native_node_binding_v1_2026-10-09';P=E/'full_ram_bound_rc_base_prediction_v1_2026-10-09';proof=E/'full_ram_bound_rc_base_csr_verification_v1_2026-10-09/verification.json'
v=json.loads(proof.read_text());assert v['passed']
for p,h in v['bindings'].items():assert sha(p)==h
binding=E/'full_ram_native_node_binding_verification_v1_2026-10-09/verification.json';bv=json.loads(binding.read_text());assert bv['passed']
paths=[Path(__file__),R/'tools/cached_bound_rc_base_v1.py',R/'tools/bound_indexed_cost.py',R/'tools/path_rc.py',R/'tools/rr_graph.py',R/'tools/prepared_csr.py',proof,binding,B/'rr_indexed_data.echo',B/'routecast_node_cost_indices.csv',E/'full_ram_comb_only_route_v1_2026-10-09/rr_graph.xml']
bindings={str(p):sha(p) for p in paths}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,scope='Exact all-field/all-arc equality versus independently XML-verified original CSR. Instrumented construction profile with full-field equality. Profiling overhead precludes runtime speedup inference.'),indent=2)+'\n')
t=time.perf_counter();g=read_rr_graph(paths[-1]);graph_s=time.perf_counter()-t;t=time.perf_counter()
import cProfile,pstats
profiler=cProfile.Profile();profiler.enable()
engine=CachedBoundRCBase(g,(B/'rr_indexed_data.echo').read_text(),(B/'routecast_node_cost_indices.csv').read_text(),bv['identity']);classes=engine.cost_classes
profiler.disable();profiler.dump_stats(str(D/'construction.prof'))
with (D/'construction_profile.txt').open('w') as report:pstats.Stats(profiler,stream=report).sort_stats('cumulative').print_stats(35)
construction_s=time.perf_counter()-t;t=time.perf_counter();write(engine,D/'csr');serialization_s=time.perf_counter()-t
ma,a=read(P/'csr',g.sha256);mb,b=read(D/'csr',g.sha256)
assert a.keys()==b.keys()
for field in a:assert a[field]==b[field],field
assert ma['context_sha256']==mb['context_sha256']
assert all(sha(p)==h for p,h in bindings.items())
out=dict(passed=True,nodes=ma['nodes'],arcs=ma['edges'],cost_classes=classes,graph_read_s=graph_s,construction_s=construction_s,serialization_s=serialization_s,context_sha256=mb['context_sha256'],bindings=bindings,scope='All fields including raw edge/node/switch mapping, disabled sentinel and exact integer costs equal. No new search, HDL/HLS, native float parity or net-benefit evidence.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
