"""Verify newly raised floors using mechanically checked shortest certificates."""
import json,sys
from fractions import Fraction as F
from pathlib import Path
from online_conflict_core import shortest_delay
from persistent_rc_context import PersistentRCContext
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];w,i=map(int,sys.argv[1:]);out=ROOT/'experiments/mux_owner_union_wire_fixed_cap_cohort_2026-10-07';file=out/f'w{w}_m{i}/result.json';d=json.loads(file.read_text());p=json.loads((out/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(w,i));ctx=PersistentRCContext(case['target']);af=ROOT/f'experiments/mux_critical_release_budgets_2026-10-06/w{w}_m{i}.json';a=json.loads(af.read_text());f=ctx.rc.fields;inc=ctx.rc.increments;source_of={s:u for u in range(len(ctx.context[2])) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};certs={};labels=0
for spec in d['allocations']:
 expected={cid:F(v) for cid,v in a['floor_ns'].items()};expanded=set(a['expanded_connection_ids']);supported=True
 for q in ctx.context[5]:
  bans=spec['restrictions'].get(str(q['net_id']))
  if bans is None:continue
  expanded.add(q['connection_id']);key=(q['source'],tuple(bans))
  if key not in certs:
   cert=shortest_delay(ctx,q['source'],q['sink'],set(bans));dist=cert['distances'];pred=cert['predecessor_slots'];source=q['source'];assert not set(bans)&set(dist)
   if source in bans or f['capacities'][source]<=0:assert not dist
   else:assert dist[source]==0 and set(pred)==set(dist)-{source}
   for u,value in dist.items():
    for slot in range(f['row_offsets'][u],f['row_offsets'][u+1]):
     v=f['dest_ranks'][slot]
     if v in bans or f['capacities'][v]<=0:continue
     assert v in dist and dist[v]<=value+inc[slot]
   rooted={source} if source in dist else set()
   for n in pred:
    trail=[];seen=set()
    while n not in rooted:
     assert n not in seen;seen.add(n);trail.append(n);slot=pred[n];u=source_of[slot];assert f['dest_ranks'][slot]==n and dist[n]==dist[u]+inc[slot];n=u
    rooted.update(trail)
   labels+=len(dist);certs[key]=dist
  minimum=certs[key].get(q['sink'])
  if minimum is None:supported=False;continue
  cid=str(q['connection_id']);expected[cid]=max(expected[cid],F(minimum*10**9,ctx.rc.scale))
 assert spec['expanded']==sorted(expanded) and expected=={cid:F(v) for cid,v in spec['floor_ns'].items()}
 assert spec['valid']==(supported and F(spec['floor_cpd_ns'])<=F(a['target_cpd_ns']) and all(expected[str(cid)]<=1 for cid in expanded))
(file.parent/'floor_verification.json').write_text(json.dumps(dict(result_sha256=sha(file),base_sha256=sha(af),verifier_sha256=sha(Path(__file__)),core_sha256=sha(ROOT/'tools/online_conflict_core.py'),allocations=len(d['allocations']),certificates=len(certs),labels=labels,scope='Shortest solver reused to regenerate certificates, independent edge inequalities/reachable closure/acyclic predecessor checks prove integer model optimality. Exact floor/expanded set/acceptance checks, timing CPD independently checked separately. Shared RC loader, not independent Fraction/native STA.'),indent=2)+'\n');print(w,i,'floors verified',len(certs),'certificates',flush=True)
