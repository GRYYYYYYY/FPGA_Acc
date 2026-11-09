"""Prospective all-width reverse-delay-bound experiment; includes preprocessing time."""
import ctypes,json,subprocess,time
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from staged_placement_reroute import stage_reroute_with_repair
ROOT=Path(__file__).resolve().parents[1]
out=ROOT/'experiments/mux_target_bound_v2_2026-10-06';out.mkdir()
source=ROOT/'build/rc_capacity_native_2026-10-06/search.cpp';s=source.read_text()
s=s.replace('struct Entry {U cost,delay;uint64_t node,id;};','struct Entry {U cost,delay;uint64_t node,id;U priority=0;};')
s=s.replace('std::tie(a.cost,a.delay,a.node,a.id)>std::tie(b.cost,b.delay,b.node,b.id)','std::tie(a.priority,a.cost,a.delay,a.node,a.id)>std::tie(b.priority,b.cost,b.delay,b.node,b.id)')
needle='std::vector<Label> labels;std::vector<std::vector<uint64_t>>front(n);'
replacement='''// Lower bound ignores capacity and demand. Costs must dominate delay increments.
 std::vector<U> h(n,~U(0));std::vector<std::vector<std::pair<uint64_t,uint64_t>>> reverse(n);
 for(uint64_t u=0;u<n;++u)for(uint64_t i=rows[u];i<rows[u+1];++i){if(dest[i]>=n)return 4;if(costs[i]!=UINT64_MAX){if(costs[i]<increments[i])return 4;reverse[dest[i]].push_back({u,i});}}
 using H=std::pair<U,uint64_t>;std::priority_queue<H,std::vector<H>,std::greater<H>> queue;h[sink]=0;queue.push({0,sink});
 while(!queue.empty()){auto [d,v]=queue.top();queue.pop();if(d!=h[v])continue;for(auto [u,i]:reverse[v]){if(~U(0)-d<increments[i])return 3;U nd=d+increments[i];if(nd<h[u]){h[u]=nd;queue.push({nd,u});}}}
 std::vector<Label> labels;std::vector<std::vector<uint64_t>>front(n);'''
assert s.count(needle)==1;s=s.replace(needle,replacement)
s=s.replace('if(initial>budget||','if(h[source]==~U(0)||initial>budget||h[source]>budget-initial||')
s=s.replace('heap.push({0,initial,source,0});','heap.push({0,initial,source,0,h[source]});')
s=s.replace('if(nd>budget)continue;','if(nd>budget||h[v]==~U(0)||h[v]>budget-nd)continue;if(~U(0)-nc<h[v])return finish(3);')
s=s.replace('heap.push({nc,nd,v,id});','heap.push({nc,nd,v,id,nc+h[v]});')
cpp=out/'search.cpp';cpp.write_text(s);binary=out/'search.so';subprocess.run(['g++','-O2','-std=c++17','-shared','-fPIC',str(cpp),'-o',str(binary)],check=True)
base=ROOT/'experiments/mux_live_placement_updates_2026-10-06';cases=json.loads((base/'protocol.json').read_text())['cases']
(out/'protocol.json').write_text(json.dumps(dict(cases=cases,source_sha256=sha(Path(__file__)),baseline_cpp_sha256=sha(source),cpp_sha256=sha(cpp),binary_sha256=sha(binary),policy='All8/16/32; original 1ns/10000/max4. Reverse exact unconstrained delay per query, cost lower bound valid only costs>=increments; changes ordering/ties and delay pruning. Preprocessing included in measured stage; no cache. Frozen failure retained.'),indent=2)+'\n')
rows=[]
for case in cases:
 width=case['width'];work=out/f'w{width}';work.mkdir();old=base/f'w{width}/original_endpoints.json';target=base/f'w{width}/swapped_endpoints.json'
 ctx=PersistentRCContext(old);state=import_native_ledger(ctx,Path(case['source'])/'design.route');signature=ctx.native.lib.rc_query.argtypes;ctx.native.lib=ctypes.CDLL(str(binary));ctx.native.lib.rc_query.argtypes=signature;ctx.native.lib.rc_query.restype=ctypes.c_int
 started=time.perf_counter();update=stage_reroute_with_repair(state,target);elapsed=time.perf_counter()-started;candidate=update['repair'] or update['incremental'];(work/'prediction.json').write_text(json.dumps(candidate,indent=2)+'\n')
 (work/'update.json').write_text(json.dumps(update,indent=2)+'\n')
 row=dict(width=width,seconds_including_bounds=elapsed,completed=candidate['completed_connections'],required=candidate['required_connections'],failure=candidate['failure'],queries=len(candidate['events']),labels=sum(e.get('answer',{}).get('labels_created',0) for e in candidate['events']),expanded=sum(e.get('answer',{}).get('labels_expanded',0) for e in candidate['events']),prediction_sha256=sha(work/'prediction.json'));rows.append(row)
 assert all(sha(p)==h for p,h in case['inputs'].items())
 (out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(row,flush=True)
