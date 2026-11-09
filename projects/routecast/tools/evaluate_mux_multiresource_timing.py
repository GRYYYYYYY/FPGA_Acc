"""Full old-DAG floor feasibility for every two-resource detour option."""
import json
from functools import lru_cache
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_multiresource_options_2026-10-06';r=json.loads((out/'receipt.json').read_text());v=json.loads((out/'verification.json').read_text());assert v['receipt_sha256']==sha(out/'receipt.json');rows=[]
for row in r['rows']:
 if row.get('status')=='ALLOCATION_NOT_SUBMITTED':rows.append(row);continue
 w,i=row['width'],row['index'];d=json.loads((out/f'w{w}_m{i}.json').read_text());af=ROOT/f'experiments/mux_allfanin_budgets_2026-10-06/w{w}_m{i}.json';a=json.loads(af.read_text());tgf=ROOT/f'experiments/mux_old_full_timing_graph_2026-10-06/w{w}_timing_graph.json';mf=ROOT/f'experiments/mux_full_timing_rr_2026-10-06/w{w}.json';assert sha(tgf)==a['graph_sha256'] and sha(mf)==a['mapping_sha256'];tg=json.loads(tgf.read_text());mp=json.loads(mf.read_text());incoming={int(n):[] for n in tg['nodes']}
 for eid,e in tg['edges'].items():
  if not e['disabled']:incoming[e['sink']].append((e['source'],eid))
 options=[]
 for option in d['options']:
  floor={cid:F(x) for cid,x in a['floor_ns'].items()};supported=True;cap_ok=True
  for ans in option['answers']:
   cid=str(ans['query']['connection_id'])
   if ans['minimum'] is None:supported=False;continue
   floor[cid]=max(floor[cid],F(ans['minimum']*10**9,d['scale']));cap_ok=cap_ok and floor[cid]<=1
  @lru_cache(None)
  def arrival(n):
   return max([F(0)]+[arrival(u)+(floor[str(a['edge_connection_ids'][eid])]+F(mp['external_edges'][eid]['old_local_offset_seconds'])*10**9 if eid in a['edge_connection_ids'] else F(tg['edges'][eid]['max_delay_seconds'])*10**9) for u,eid in incoming[n]])
  cpd=max(arrival(int(n)) for n,kind in tg['nodes'].items() if kind=='SINK');target=F(a['target_cpd_ns']);options.append(dict(chosen_net=option['chosen_net'],restrictions=option['restrictions'],model_floor_cpd_ns=str(cpd),target_cpd_ns=str(target),cap_ok=cap_ok,feasible=supported and cap_ok and cpd<=target))
 rows.append(dict(width=w,index=i,options=options,any_feasible=any(o['feasible'] for o in options)))
(out/'timing_options.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),verification_sha256=sha(out/'verification.json'),source_sha256=sha(Path(__file__)),rows=rows,scope='Retrospective full old-DAG floor feasibility; relaxed minima from certificates, old local offsets and saved floors; newly restricted NETs require release/reroute. No capacity realization/nativeSTA proof; rejection is only of these options under these saved floors.'),indent=2)+'\n');print([(x['width'],x['index'],x.get('any_feasible')) for x in rows])
