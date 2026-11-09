"""All fixed moves: relaxed perconnection minima versus joint old path constraints."""
import json,time
from collections import defaultdict
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import sha
from persistent_rc_context import PersistentRCContext
ROOT=Path(__file__).resolve().parents[1];base=ROOT/'experiments/mux_budget_move_cohort_2026-10-06';out=ROOT/'experiments/mux_joint_path_floors_2026-10-06';out.mkdir();parent=json.loads((base/'protocol.json').read_text());cases=parent['cases'];sources={str(Path(__file__)):sha(Path(__file__))};(out/'protocol.json').write_text(json.dumps(dict(cases=cases,parent_protocol_sha256=sha(base/'protocol.json'),sources=sources,policy='All12 fixed moves, reportedoldpaths only. Relaxedminimum via aligned integer nativecost/delay,100000allocation diagnosticlimit, huge delay budget; cache source/sink perwidth. Jointsum floor <=sum oldRR +guardedoldpathheadroom. Localtiming held fixed hypothesis, occupancy/treeconstraints ignored; notglobalSTAguarantee. No routingbudget adjustment.'),indent=2)+'\n');rows=[];last=None
for c in cases:
 w=c['width'];i=c['index'];started=time.perf_counter()
 if w!=last:
  ctx=PersistentRCContext(c['old']);spec=json.loads(Path(c['budget']).read_text());cache={};groups=defaultdict(list)
  for x in spec['constraints']:groups[x['rank']].append(x)
  last=w
 original=ctx.context;metadata=ctx.endpoint_metadata
 try:
  ctx.bind_endpoints(c['target']);queries={q['connection_id']:q for q in ctx.context[5]};floors={};answers={}
  for cid in sorted({x['connection_id']for x in spec['constraints']}):
   q=queries[cid];key=(q['source'],q['sink'])
   if key not in cache:
    answer=ctx.query(*key,(1<<127),{},max_labels=100000);assert answer['status']=='FOUND',answer['status'];cache[key]=answer
   answer=cache[key];floors[cid]=Fraction(answer['delay']*10**9,ctx.rc.scale);answers[cid]=dict(query=q,answer=answer)
  paths=[]
  for rank,segments in groups.items():
   headrooms={Fraction(x['guarded_path_headroom_ns'])for x in segments};assert len(headrooms)==1;limit=sum(Fraction(x['old_rr_ns'])for x in segments)+headrooms.pop();minimum=sum(floors[x['connection_id']]for x in segments);paths.append(dict(rank=rank,connection_ids=[x['connection_id']for x in segments],old_rr_plus_headroom_ns=str(limit),relaxed_floor_sum_ns=str(minimum),violated=minimum>limit,shortfall_ns=str(max(Fraction(0),minimum-limit))))
  file=out/f'w{w}_m{i}.json';file.write_text(json.dumps(dict(scale=ctx.rc.scale,answers=answers,paths=paths),indent=2)+'\n');row=dict(width=w,index=i,reported_connections=len(floors),reported_paths=len(paths),violated_paths=sum(p['violated']for p in paths),seconds_including_context_on_first_move=time.perf_counter()-started,sha256=sha(file));rows.append(row);print(row,flush=True)
 finally:
  ctx.context=original;ctx.endpoint_metadata=metadata;ctx.native.set_other({})
 assert all(sha(p)==h for p,h in c['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
