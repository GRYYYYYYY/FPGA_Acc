"""All required native borrowed-RR floors/path IDs versus original exact forward kernel and original XML RC."""
import json,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from hybrid_bidirectional_search_v1 import Search
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_native_inprocess_hybrid_rr_v1_2026-10-10';p=D/'receipt.json';v=json.loads(p.read_text());assert v['all_native_routes_byte_equal_original'] and all(sha(q)==h for q,h in v['bindings'].items());epfile=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(epfile);observed={}
for line in (D/'on/floors.tsv').read_text().splitlines():
 x=line.split('\t');assert x[0]=='Q';cid,delay,count=map(int,x[1:4]);path=list(map(int,x[4:]));assert count==len(path) and cid not in observed;observed[cid]=(delay,path)
assert len(observed)==len(queries)==6273 and set(observed)=={q['connection_id'] for q in queries};groups=defaultdict(list)
for q in queries:groups[q['net_id']].append(q)
binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';search=Search(f,rc,binary);search.prepare({},0);same_as_hybrid_paths=0;initial=json.loads((R/'experiments/sha_overflow_guard_v1_2026-10-10/second_swap/model/initial.json').read_text());original={q['connection_id']:q for q in initial['records']}
for net,qs in sorted(groups.items()):
 src=qs[0]['source'];d,parents,settled=search.search(src,{q['sink'] for q in qs})
 for q in qs:
  assert q['sink'] in settled;u=q['sink'];path=[];seen={u}
  while u!=src:
   prev,slot=parents[u];path.append(f['edge_ids'][slot]);u=prev;assert u not in seen;seen.add(u)
  path.reverse();delay,nativepath=observed[q['connection_id']];assert nativepath==path and delay==d[q['sink']]==original[q['connection_id']]['floor_integer'] and rc.path(src,q['sink'],nativepath)==delay;same_as_hybrid_paths+=nativepath==original[q['connection_id']]['answer']['physical_edge_ids']
search.close();assert same_as_hybrid_paths==6273;bindings={str(q):sha(q) for q in [Path(__file__).resolve(),p,epfile,graph,D/'on/floors.tsv',binary,R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so',R/'tools/soft_demand_cpp/bidirectional_workspace_v2.cpp',R/'tools/hybrid_bidirectional_search_v1.py',R/'tools/soft_demand_cpp/tree_workspace_radix_v3.cpp',R/'tools/class_cached_rc_endpoint_context_v1.py']};assert all(sha(q)==h for q,h in bindings.items());(D/'independent_verification.json').write_text(json.dumps(dict(bindings=bindings,all6273_native_live_RR_hybrid_costs_and_paths_equal_original_CSR_hybrid=True,all6273_exact_original_XML_RC_floor_values_equal=True,paths_equal_existing_hybrid_initial=same_as_hybrid_paths,scope='Complete hybrid forward+balancedbidi livegraph getter contract; all requested singleton/multitarget costs/path tie choices and actualnative routebytes preserved. No feedback/transaction/fullpredictor pipeline/family or totaltime gain.'),indent=2)+'\n');print('ALL6273 NATIVE LIVE RR HYBRID PATHS+FLOORS PASS',same_as_hybrid_paths)
