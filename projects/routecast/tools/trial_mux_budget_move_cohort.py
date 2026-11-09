"""Prospective fixed disjoint CLB swaps; retain all feasibility outcomes."""
import json,re,time,xml.etree.ElementTree as ET
from fractions import Fraction
from pathlib import Path
from pre_route_endpoints import placements,physical_maps,extract,sha
from native_place_serialization import canonical_place
from persistent_rc_context import PersistentRCContext
from moved_budget_preflight import check
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_budget_move_cohort_2026-10-06';out.mkdir();cases=[]
for w in (8,16,32):
 source=ROOT/f'work/mux_crossbar_channel_pressure_2026-10-06/mux_w{w}_c128';net=source/'design.net';place=source/'design.place';graph=source/'rr_graph.xml';pos=placements(place,sha(net));_,grid,_=physical_maps(graph);clbs=[];signature=None
 for block in ET.parse(net).getroot().findall('block'):
  if re.sub(r'\[\d+\]$','',block.get('instance'))!='clb':continue
  name=block.get('name');x,y,z,layer,_=pos[name];sig=(z,layer,grid[x,y,layer])
  if signature is None:signature=sig
  if sig==signature:clbs.append(name)
 assert len(clbs)>=8
 for index in range(4):
  pair=clbs[2*index:2*index+2];work=out/f'w{w}_m{index}';work.mkdir();lines=[]
  for line in place.read_text().splitlines():
   fields=line.split()
   if fields and fields[0]in pair:
    name=fields[0];other=pair[1]if name==pair[0]else pair[0];x,y,z,layer,_=pos[other];line=f'{name}\t{x}\t{y}\t{z}\t{layer}\t#{pos[name][4]}'
   lines.append(line)
  target=work/'target.place';target.write_text('\n'.join(lines)+'\n');target.write_text(canonical_place(target,net));ep,_=extract(net,target,graph);epfile=work/'target_endpoints.json';epfile.write_text(json.dumps(ep,indent=2)+'\n');budget=ROOT/f'experiments/mux_connection_budgets_2026-10-06/w{w}.json';old=ROOT/f'experiments/mux_live_placement_updates_2026-10-06/w{w}/original_endpoints.json';cases.append(dict(width=w,index=index,pair=pair,target=str(epfile),old=str(old),budget=str(budget),inputs={str(p):sha(p)for p in(net,place,graph,target,epfile,budget,old)}))
(out/'protocol.json').write_text(json.dumps(dict(cases=cases,sources={str(p):sha(p)for p in(Path(__file__),ROOT/'tools/moved_budget_preflight.py')},policy='All12 deterministic first4 disjoint compatible packedorder CLB pairs frozen before any feasibility result; no success-based selection. Same old perconnection budgets, reuse one original context perwidth. Necessary relaxed graph feasibility only; not routing/nativequality.'),indent=2)+'\n');rows=[];ctx=None;last=None
for case in cases:
 w=case['width']
 if w!=last:
  ctx=PersistentRCContext(case['old']);last=w;spec=json.loads(Path(case['budget']).read_text());budgets={int(c):int(Fraction(ns)*ctx.rc.scale/10**9)for c,ns in spec['budgets_ns'].items()}
 context=ctx.context;metadata=ctx.endpoint_metadata;begin=time.perf_counter();result=check(ctx,case['target'],budgets);seconds=time.perf_counter()-begin;assert ctx.context is context and ctx.endpoint_metadata is metadata;file=out/f'w{w}_m{case["index"]}/preflight.json';file.write_text(json.dumps(result,indent=2)+'\n');rows.append(dict(width=w,index=case['index'],pair=case['pair'],status=result['status'],budgeted_affected_connections=result['budgeted_affected_connections'],checked_connections=len(result['observations']),probe_seconds=seconds,sha256=sha(file)));assert all(sha(p)==h for p,h in case['inputs'].items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n');print(rows[-1],flush=True)
