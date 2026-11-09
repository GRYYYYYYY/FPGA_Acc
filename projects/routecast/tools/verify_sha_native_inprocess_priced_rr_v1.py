"""All required native borrowed-RR floors/path IDs versus original exact forward kernel and original XML RC."""
import json,sys
from pathlib import Path
from collections import defaultdict
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from class_cached_rc_endpoint_context_v1 import load_endpoints
from hybrid_bidirectional_search_v1 import Search
R=Path(__file__).resolve().parents[1];D=R/'experiments/sha_native_inprocess_priced_rr_v2_2026-10-10';p=D/'receipt.json';v=json.loads(p.read_text());assert v['all_native_routes_byte_equal_original'] and all(sha(q)==h for q,h in v['bindings'].items());epfile=R/'experiments/sha_second_swap_overflow_guard_complete_workflow_v1_2026-10-10/seed/demand/sha1/endpoints.json';graph,digest,nodes,f,rc,queries=load_endpoints(epfile)
results=[]
prep=R/'experiments/native_inprocess_priced_prepare_v1_2026-10-10/receipt.json';pv=json.loads(prep.read_text());assert all(sha(q)==h for q,h in pv['bindings'].items())
for i in range(2):
 mode=f'round{i}';prices={int(a):int(b) for a,b in (line.split() for line in (prep.parent/f'prices{i}.txt').read_text().splitlines())}
 observed={}
 for line in (D/mode/'floors.tsv').read_text().splitlines():
  x=line.split('\t');assert x[0]=='Q';cid,delay,count=map(int,x[1:4]);path=list(map(int,x[4:]));assert count==len(path) and cid not in observed;observed[cid]=(delay,path)
 assert len(observed)==len(queries)==6273 and set(observed)=={q['connection_id'] for q in queries};groups=defaultdict(list)
 for q in queries:groups[q['net_id']].append(q)
 binary=R/'experiments/soft_demand_workspace_radix_build_v3_2026-10-08/search.so';search=Search(f,rc,binary);search.prepare(prices,50000000);same_as_hybrid_paths=0;initial=json.loads((R/'experiments/sha_overflow_guard_v1_2026-10-10/second_swap/model/initial.json').read_text());original={q['connection_id']:q for q in initial['records']}
 for net,qs in sorted(groups.items()):
  src=qs[0]['source'];d,parents,settled=search.search(src,{q['sink'] for q in qs})
  for q in qs:
   assert q['sink'] in settled;u=q['sink'];path=[];seen={u}
   while u!=src:
    prev,slot=parents[u];path.append(f['edge_ids'][slot]);u=prev;assert u not in seen;seen.add(u)
   path.reverse();delay,nativepath=observed[q['connection_id']];assert nativepath==path and delay==d[q['sink']] and rc.path(src,q['sink'],nativepath)==delay;same_as_hybrid_paths+=nativepath==original[q['connection_id']]['answer']['physical_edge_ids']
 search.close();results.append(dict(mode=mode,queries=len(observed),paths_equal_initial=same_as_hybrid_paths))
assert sum(r['queries'] for r in results)==12546
(D/'independent_verification.json').write_text(json.dumps(dict(results=results,all12546_paths_raw_costs_and_exact_XML_RC_equal=True,scope='Frozen archived prices; complete search interface parity only, no feedback or end-to-end gain.'),indent=2)+'\n');print(results)
