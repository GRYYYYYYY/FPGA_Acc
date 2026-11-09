"""Paid old/new/old RR-template reuse, exact context parity and isolation."""
import json,time,hashlib
from pathlib import Path
from class_cached_rc_endpoint_session_v2 import load_endpoints,clear_cache,STATS
from class_cached_rc_endpoint_context_v1 import load_endpoints as direct
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_state_cross_placement_context_v1_2026-10-18';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=R/'experiments/freecores_native_demand_v1_2026-10-08/xtea/endpoints.json';new=R/'experiments/xtea_native_state_new_swap_v1_2026-10-18/demand/endpoints.json';bindings={str(p):sha(p) for p in [Path(__file__),old,new]}
with (D/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,order=[str(old),str(new),str(old)],policy='Existing serial authenticated RR template loader; count cold initialization and all new endpoint input hashes/version checks/copies. Compare complete actual new placement context with fresh direct loader. Mutate returned copies and reject stale graph epoch. No native/estimator speed claim.'),f,indent=2);f.write('\n')
clear_cache();rows=[];start=time.perf_counter();contexts=[]
for path in [old,new,old]:
 tick=time.perf_counter();ctx=load_endpoints(path);seconds=time.perf_counter()-tick;meta=json.loads(path.read_text());assert ctx[-1]==meta['connections'];rows.append(dict(endpoint=str(path),seconds=seconds,cache_stats=dict(STATS)));contexts.append(ctx)
common_seconds=time.perf_counter()-start;assert STATS['builds']==1 and STATS['hits']==2
reference=direct(new);candidate=contexts[1];assert reference[1]==candidate[1]
for key in reference[3]:assert reference[3][key]==candidate[3][key],key
assert reference[4].scale==candidate[4].scale and reference[4].increments==candidate[4].increments
assert all(reference[4].initial(n)==candidate[4].initial(n) for n in range(len(reference[2])))
assert contexts[0][-1]!=contexts[1][-1] and contexts[0][-1]==contexts[2][-1]
# Mutations confined to the caller's arrays and RC increments.
saved=candidate[3]['capacities'][0];candidate[3]['capacities'][0]=saved+1;savedinc=candidate[4].increments[0];candidate[4].increments[0]=savedinc+1
fresh=load_endpoints(new);assert fresh[3]['capacities'][0]==saved and fresh[4].increments[0]==savedinc
bad=json.loads(new.read_text());bad['graph_sha256']='0'*64;badpath=D/'bad_graph_endpoint.json'
with badpath.open('x') as f:json.dump(bad,f)
try:load_endpoints(badpath)
except ValueError as e:assert str(e)=='Changed graph hash'
else:raise AssertionError('Wrong graph epoch accepted')
for name in ['class_cached_rc_endpoint_session_v2.py','class_cached_rc_endpoint_context_v1.py','class_cached_integer_rc_v1.py','csr_exact_buffered_rc.py','path_rc.py','cached_rr_endpoint_context_classes.py','buffered_rc_node_classes.py','integer_rc_context.py','pre_route_endpoints.py']:
 p=R/'tools'/name;bindings[str(p)]=sha(p)
for path in [old,new]:
 for spec in json.loads(path.read_text())['inputs'].values():bindings[spec['path']]=spec['sha256']
assert all(sha(p)==h for p,h in bindings.items())
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,cold_and_two_updates_seconds=common_seconds,one_template_build=True,new_placement_endpoints_exact=True,all_new_CSR_rawRC_and_initial_values_equal_fresh_direct=True,caller_mutation_isolated=True,stale_graph_epoch_rejected=True,scope='Existing RR-template reuse correctness on real old/new placements. It still hashes inputs and copies mutable arrays per call; no persistent estimator/native state, full admission or end-to-end timing.'),f,indent=2);f.write('\n')
print('PASS cross-placement context',rows,flush=True)
