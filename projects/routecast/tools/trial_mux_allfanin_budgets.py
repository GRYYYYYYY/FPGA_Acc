"""All-fanin budget allocation, fixed retained RR, all twelve frozen moves."""
import json,time,xml.etree.ElementTree as ET
from fractions import Fraction
from collections import defaultdict,deque
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/mux_budget_move_cohort_2026-10-06';out=ROOT/'experiments/mux_allfanin_budgets_2026-10-06';out.mkdir();cases=json.loads((parent/'protocol.json').read_text())['cases'];(out/'protocol.json').write_text(json.dumps(dict(cases=cases,source_sha256=sha(Path(__file__)),policy='All12 fixed moves, full oldtiminggraph/oldlocals, retainedactualRR fixed. Relaxedaffected floors, diagnostic100000labels/hugebudget, integeralignedcost. Target oldCPD+0.001ns echo guard; affected cap1ns. Uniform floor-to-cap interpolation with24 rational bisection steps, allfaninCPDconstraint. Floor/cache/context work measured, no nativeoracle. Not nativeSTA guarantee or infeasibility proof without independent minima.'),indent=2)+'\n');rows=[];last=None
for case in cases:
 w,i=case['width'],case['index'];begin=time.perf_counter()
 if w!=last:
  ctx=PersistentRCContext(case['old']);state=import_native_ledger(ctx,ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128/design.route');old={cid:Fraction(r['answer']['delay'],ctx.rc.scale)for cid,r in state.records.items()};cache={};tgfile=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';tg=json.loads(tgfile.read_text());mp=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';mapping=json.loads(mp.read_text());ep=json.loads(Path(case['old']).read_text());rrnodes={int(n.get('id')):n.find('loc').attrib for n in ET.parse(ep['inputs']['graph']['path']).getroot().find('rr_nodes')};qmap={}
  for q in ctx.context[5]:
   l=rrnodes[q['sink']];key=(ep['net_names'][str(q['net_id'])],*(int(l.get(k,'0'))for k in('xlow','ylow','layer','ptc')));assert key not in qmap;qmap[key]=q['connection_id']
  edge_cid={}
  for eid,m in mapping['external_edges'].items():
   l=rrnodes[m['branch']['sink']];key=(m['atom_net'],*(int(l.get(k,'0'))for k in('xlow','ylow','layer','ptc')));cid=qmap[key];assert old[cid]==Fraction(m['branch']['rr_delay_seconds']);edge_cid[eid]=cid
  assert set(edge_cid.values())==set(old);adj=defaultdict(list);indeg={int(n):0 for n in tg['nodes']}
  for eid,e in tg['edges'].items():
   if not e['disabled']:adj[e['source']].append((e['sink'],eid));indeg[e['sink']]+=1
  queue=deque(n for n in indeg if not indeg[n]);order=[]
  while queue:
   u=queue.popleft();order.append(u)
   for v,eid in adj[u]:
    indeg[v]-=1
    if not indeg[v]:queue.append(v)
  assert len(order)==len(indeg);sinks=[int(n)for n,k in tg['nodes'].items()if k=='SINK'];nativeold=json.loads((ROOT/'experiments/mux_old_full_timing_graph_2026-10-06/receipt.json').read_text());cpd=next(r['cpd_ns']for r in nativeold['rows']if r['width']==w);target=(Fraction(str(cpd))+Fraction(1,1000))/10**9;last=w
 def evaluate(b):
  a={n:Fraction(0)for n in order}
  for u in order:
   for v,eid in adj[u]:
    delay=b[edge_cid[eid]]+Fraction(mapping['external_edges'][eid]['old_local_offset_seconds'])if eid in edge_cid else Fraction(tg['edges'][eid]['max_delay_seconds']);a[v]=max(a[v],a[u]+delay)
  return max(a[n]for n in sinks)
 context=ctx.context;metadata=ctx.endpoint_metadata
 try:
  affected=ctx.bind_endpoints(case['target']);cohort=set(affected['affected_complete_net_connection_ids']);floor=dict(old);witnesses={}
  for q in ctx.context[5]:
   cid=q['connection_id']
   if cid not in cohort:continue
   key=(q['source'],q['sink'])
   if key not in cache:
    answer=ctx.query(*key,1<<127,{},max_labels=100000);assert answer['status']=='FOUND';cache[key]=answer
   answer=cache[key];floor[cid]=Fraction(answer['delay'],ctx.rc.scale);witnesses[cid]=dict(query=q,answer=answer)
  mincpd=evaluate(floor);cap=Fraction(1,10**9);valid=mincpd<=target and all(floor[cid]<=cap for cid in cohort);budget=dict(floor);low=Fraction(0);high=Fraction(1)
  if valid:
   for _ in range(24):
    mid=(low+high)/2;trial={cid:(floor[cid]+mid*(cap-floor[cid])if cid in cohort else floor[cid])for cid in floor}
    if evaluate(trial)<=target:low=mid;budget=trial
    else:high=mid
   assert evaluate(budget)<=target
  status='ALLFANIN_VECTOR_CONSTRUCTED'if valid else'NO_ALLFANIN_VECTOR_FROM_DIAGNOSTIC';file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(status=status,scale=ctx.rc.scale,affected=affected,relaxed_witnesses=witnesses,budgets_ns={str(cid):str(b*10**9)for cid,b in budget.items()}if valid else{},floor_ns={str(cid):str(b*10**9)for cid,b in floor.items()},edge_connection_ids=edge_cid,model_floor_cpd_ns=str(mincpd*10**9),model_budget_cpd_ns=str(evaluate(budget)*10**9),target_cpd_ns=str(target*10**9),interpolation=str(low),graph_sha256=sha(tgfile),mapping_sha256=sha(mp)),indent=2)+'\n');rows.append(dict(width=w,index=i,status=status,affected_connections=len(cohort),floor_cpd_ns=float(mincpd*10**9),target_cpd_ns=float(target*10**9),seconds_including_setup_first_move=time.perf_counter()-begin,sha256=sha(file)));print(rows[-1],flush=True)
 finally:ctx.context=context;ctx.endpoint_metadata=metadata;ctx.native.set_other({})
 assert all(sha(p)==h for p,h in case['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
