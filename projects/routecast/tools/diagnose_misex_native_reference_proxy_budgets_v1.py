"""Reference-only diagnostic of original scalar proxy budgets; never a predictor."""
import sys,json,time
from pathlib import Path
from collections import defaultdict,Counter
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
from audit_native_route import NET,NODE
from stream_native_route_audit import audit
out=R/'experiments/misex_native_reference_proxy_budgets_v1_2026-10-07';out.mkdir();begin=time.perf_counter();ep=R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json';route=ep.parent/'design.route';log=ep.parent/'native.log';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings={**closure([Path(__file__)]),str(ep):sha(ep),str(route):sha(route),str(log):sha(log),str(fp):sha(fp)};graph,digest,nodes,f,rc,queries=load_endpoints(ep);bindings.update({x['path']:x['sha256'] for x in json.loads(ep.read_text())['inputs'].values()});assert 'VPR succeeded' in log.read_text() and 'Completed routing consistency check successfully.' in log.read_text();physical=audit(graph,route);assert physical['overflow_units']==0;qm=defaultdict(list)
for q in queries:qm[q['net_id'],q['source'],q['sink']].append(q)
floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};arc=defaultdict(list)
for u in range(len(nodes)):
 for e in range(f['row_offsets'][u],f['row_offsets'][u+1]):arc[u,f['dest_ranks'][e],f['switch_ids'][e]].append(f['edge_ids'][e])
(out/'protocol.json').write_text(json.dumps(dict(bindings=bindings,policy='Archived original complete native route is evaluator-only reference, not a candidate or unseen-family evidence. Match ALL original endpoint occurrences by NET/SOURCE/SINK; duplicate endpoints share scalar budgets and are reported as an occurrence multiset, not a pin/CID identity claim. Original budget max(1ns,ceil(1.5*minimum)). No budget retuning or source reference use in predictor.',required_connections=len(queries)),indent=2)+'\n');rows=[];net=None;prefix={};source=None;current=None;outgoing=None;occ=Counter()
for line in route.read_text().splitlines():
 m=NET.match(line)
 if m:net=int(m[1]);prefix={};source=None;current=None;outgoing=None
 m=NODE.match(line)
 if not m:continue
 n=int(m[1]);kind=m[2];sw=int(m[3]);assert nodes[n].get('type')==kind
 if kind=='SOURCE':assert not prefix;source=n;path=[]
 elif n in prefix and kind!='SINK':path=prefix[n]
 else:assert current is not None and arc[current,n,outgoing];path=prefix[current]+[min(arc[current,n,outgoing])]
 prefix[n]=path;current=n;outgoing=sw
 if kind!='SINK' or (net,source,n) not in qm:continue
 key=(net,source,n);index=occ[key];assert index<len(qm[key]);occ[key]+=1;floor=floors[source,n];budget=max(rc.scale//10**9,(3*floor+1)//2);delay=rc.path(source,n,path);rows.append(dict(net_id=net,source=source,sink=n,endpoint_occurrence=index,endpoint_occurrences=len(qm[key]),floor_integer=floor,budget_integer=budget,delay_integer=delay,budget_feasible=delay<=budget,physical_edge_ids=path))
assert occ==Counter({k:len(v) for k,v in qm.items()}) and len(rows)==len(queries);assert all(sha(k)==h for k,h in bindings.items());(out/'reference_rows.json').write_text(json.dumps(rows)+'\n');violations=[x for x in rows if not x['budget_feasible']];core=[26,34,104,108,165,334,462,466];summary=dict(required_connections=len(queries),reference_connections=len(rows),budget_violations=len(violations),violating_net_counts=dict(Counter(x['net_id'] for x in violations)),core_budget_counts={n:dict(total=sum(x['net_id']==n for x in rows),violations=sum(x['net_id']==n and not x['budget_feasible'] for x in rows)) for n in core},max_additive_delay_integer=max(x['delay_integer'] for x in rows),scale=rc.scale)
(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,physical_reference_audit=physical,summary=summary,total_paid_main_seconds=time.perf_counter()-begin,files={str(p):sha(p) for p in out.iterdir() if p.is_file()}),indent=2)+'\n');print('REFERENCE BUDGET DIAGNOSTIC',summary,flush=True)
