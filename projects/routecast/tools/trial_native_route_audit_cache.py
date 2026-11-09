"""Real route original/firstcached/warmcached audit output parity and clocks."""
import json,time
from pathlib import Path
from pre_route_endpoints import sha
from freeze_priority_family import closure
from stream_native_route_audit import audit as original
from stream_native_route_audit_cached import audit as cached
from native_route_audit_cache import clear_cache,STATS
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/native_route_audit_cache_real_2026-10-07';out.mkdir();cases=[]
for n in [4,8,16]:
 graph=ROOT/f'work/bitonic_native_reference_2026-10-07/n{n}/rr_graph.xml';raw=ROOT/f'experiments/bitonic_screened4_baseline_swapped_cold_2026-10-07/n{n}/design.route';canonical=ROOT/f'work/bitonic_screened4_baseline_swapped_cold_n{n}_canonical_2026-10-07/0/reload/design.route'
 for label,route in [('raw_cold',raw),('canonical_cold',canonical)]:cases.append(dict(count=n,label=label,graph=str(graph),route=str(route),graph_sha256=sha(graph),route_sha256=sha(route)))
graph=ROOT/'work/bitonic_native_reference_2026-10-07/n16/rr_graph.xml';route=ROOT/'experiments/bitonic_workflow_screened4_selected_state_2026-10-07/n16/design.route';cases.append(dict(count=16,label='accepted_candidate',graph=str(graph),route=str(route),graph_sha256=sha(graph),route_sha256=sha(route)))
sources=closure([Path(__file__)]);p=dict(cases=cases,sources=sources,scope='Independent originalXML inventory cache; serial original then cached then cached call each archived physical route. First3 builds and all hash validation included. Exact audit dictionary/bytes parity; single observed timings, not full workflow gain or RSS/concurrency claim.');(out/'protocol.json').write_text(json.dumps(p,indent=2)+'\n');clear_cache();rows=[]
for k,case in enumerate(cases):
 tick=time.perf_counter();a=original(case['graph'],case['route']);ot=time.perf_counter()-tick;tick=time.perf_counter();b=cached(case['graph'],case['route']);ct=time.perf_counter()-tick;tick=time.perf_counter();c=cached(case['graph'],case['route']);wt=time.perf_counter()-tick;assert a==b==c
 file=out/f'case{k}.json';file.write_text(json.dumps(a,indent=2)+'\n');rows.append(dict(count=case['count'],label=case['label'],connections=len(a['connections']),original_seconds=ot,cached_seconds=ct,warm_cached_seconds=wt,cache_stats=dict(STATS),output_sha256=sha(file)));print(rows[-1],flush=True);(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,complete=len(rows)==len(cases)),indent=2)+'\n')
assert all(sha(f)==d for f,d in sources.items());assert all(sha(c['graph'])==c['graph_sha256'] and sha(c['route'])==c['route_sha256'] for c in cases)
