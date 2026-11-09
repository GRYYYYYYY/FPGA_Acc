"""Alternating paired real-graph capped bound byte parity and paid request cost."""
import json,sys,time,re,statistics
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from remaining_delay_session_cache_v5 import RemainingDelayCache as Old
from remaining_delay_worker_cache_v7 import RemainingDelayCache as New
reference=R/'experiments/dsip_joint_profile_batch4_v3_2026-10-07';ep=R/'experiments/mcnc_prospective_v1_2026-10-07/dsip/endpoints.json';out=R/'experiments/worker_cache_cost_v7_2026-10-07';out.mkdir()
rp=reference/'receipt.json';rr=json.loads(rp.read_text());files=sorted((reference/'bounds').glob('miss*_sink*.bin'),key=lambda p:int(re.match(r'miss(\d+)',p.name)[1]));assert files
binary=R/'build/capped_bound_worker_cpp_v2_2026-10-07/compute';cpp=R/'tools/capped_bound_worker_cpp_v2/main.cpp';bindings={**closure([Path(__file__)]),str(binary):sha(binary),str(cpp):sha(cpp),str(rp):sha(rp),str(ep):sha(ep)};bindings.update({v['path']:v['sha256'] for v in json.loads(ep.read_text())['inputs'].values()})
for p in files:assert sha(p)==rr['files'][str(p)];bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());sinks=[int(re.search(r'_sink(\d+)',p.name)[1]) for p in files];assert len(set(sinks))==len(sinks)
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy=dict(repeats=4,order='old/new,new/old,old/new,new/old',max_entries=256,queries='Each authenticated publication sink once plus an immediate hit; construction separately timed; get archive/hash and closing finalize included in request_seconds'),scope='Post-outcome real dsip component benchmark of on-demand C++ worker versus original Python cache. Same request/hit/expired/finalize sequence andFIFO256. New construction includes original freeze/reverse, worker graph conversion/write/hash and child initialization; new closing includes worker asset hashes/child close and original graph SHA. Additional paid_cache_total_seconds covers constructor plus requests/finalize. Not original full lookup order, profile timing, live joint search, full workflow, statistical population or unseen-family gain.'),indent=2)+'\n')
graph,digest,nodes,f,rc,queries=load_endpoints(ep);rows=[]
for repeat in range(4):
 for name,cls in ([('old',Old),('new',New)] if repeat%2==0 else [('new',New),('old',Old)]):
  work=out/f'{repeat}_{name}';cache=cls(graph,digest,f,rc,work,max_entries=256);start=time.perf_counter()
  for sink in sinks:
   v=cache.get(sink);assert cache.get(sink) is v
  try:cache.get(sinks[0],deadline=time.perf_counter()-1)
  except TimeoutError:pass
  else:raise AssertionError('expired request accepted')
  cache.finalize();elapsed=time.perf_counter()-start;summary=cache.summary();assert summary['misses']==len(sinks) and summary['hits']==len(sinks) and summary['evictions']==0 and summary['aborted']==1 and summary['closed'] and not summary['invalid']
  for expected,event in zip(files,summary['events']):assert expected.read_bytes()==Path(event['path']).read_bytes()
  (out/f'{repeat}_{name}_cache.json').write_text(json.dumps(summary,indent=2)+'\n');rows.append(dict(repeat=repeat,version=name,request_seconds=elapsed,construction_seconds=summary['construction_seconds'],paid_cache_total_seconds=summary['construction_seconds']+elapsed,build_and_archive_seconds=summary['build_and_archive_seconds'],all_reference_bytes_equal=True,publications=len(sinks)));print(rows[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items());medians={n:statistics.median(r['request_seconds'] for r in rows if r['version']==n) for n in ('old','new')};(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows,median_request_seconds=medians,relative_new_over_old=medians['new']/medians['old'],median_paid_cache_total_seconds={n:statistics.median(r['paid_cache_total_seconds'] for r in rows if r['version']==n) for n in ('old','new')},bindings=bindings),indent=2)+'\n');print('PASS',medians,flush=True)
