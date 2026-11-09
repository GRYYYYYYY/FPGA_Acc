"""All-path parity to original rational model and malformed path contracts."""
import sys,json,time
from pathlib import Path
R=Path(__file__).resolve().parents[2];sys.path[:0]=[str(R/'tools'),str(Path(__file__).resolve().parent)]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from indexed_integer_rc import IndexedIntegerRC
from native_route_ledger_import_compact import physical_paths
out=R/'experiments/native_indexed_integer_rc_v2_2026-10-07';out.mkdir();ep=R/'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_1_endpoints.json';ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');inv=SharedRRInventory(ctx);begin=time.perf_counter();fast=IndexedIntegerRC(ctx.rc,ctx.fields,ctx.initial,inv);build_s=time.perf_counter()-begin;arc={arc:eid for eid,arc in enumerate(inv.edges)};rows=[];bindings={str(p):sha(p) for p in (ep,Path(__file__),R/'tools/native_resume_prototype/indexed_integer_rc.py')};samples=[]
for i in (1,2,3):
 for stage,file in [('initial','first/live.parent.route'),('candidate','first/candidate.route'),('final','canonical/design.route')]:
  path=R/f'experiments/native_resume_postroute_v5_integrated_adder_step{i}_workflow_2026-10-07'/file;bindings[str(path)]=sha(path);records=[]
  for name,ps in physical_paths(path).items():
   for p in ps:records.append((p[0][0],p[-1][0],[arc[u,v,sw] for (u,_),(v,sw) in zip(p,p[1:])]))
  begin=time.perf_counter();reference=[ctx.rc.path(*p) for p in records];reference_s=time.perf_counter()-begin;begin=time.perf_counter();indexed=[fast.path(*p) for p in records];indexed_s=time.perf_counter()-begin;assert indexed==reference and len(records)==516;samples.extend(records);rows.append(dict(index=i,stage=stage,paths=len(records),reference_seconds=reference_s,indexed_seconds=indexed_s))
source,sink,edges=next(p for p in samples if len(p[2])>2);bad=[('negative_edge',source,sink,[-1]),('bool_edge',source,sink,[True]),('edge_overflow',source,sink,[len(inv.edges)]),('discontinuous',source,sink,edges[1:]),('wrong_sink',source,source,edges),('invalid_source',-1,sink,edges),('invalid_sink',source,len(ctx.initial),edges)]
reverse={(u,v):eid for eid,(u,v,sw) in enumerate(inv.edges)}
u,v=next((u,v) for u,v in reverse if u!=v and (v,u) in reverse);bad.append(('cycle',u,u,[reverse[u,v],reverse[v,u]]))
guards=[]
for name,src,dst,path in bad:
 errors=[]
 for model in (ctx.rc,fast):
  try:model.path(src,dst,path);errors.append(None)
  except ValueError as e:errors.append(str(e))
 assert all(errors),(name,errors);guards.append(dict(case=name,both_reject=True,errors=errors))
assert all(sha(p)==h for p,h in bindings.items());(out/'receipt.json').write_text(json.dumps(dict(bindings=bindings,construction_seconds=build_s,rows=rows,guards=guards,scope='4644 genuine paths over initial/candidate/final three known steps exactly equal original rational evaluator; physical-edge direct index, no quantization. Eight malformed paths rejected in both. Local evaluator timings, not full routing speed.'),indent=2)+'\n');print('PASS',sum(r['paths'] for r in rows),build_s,sum(r['reference_seconds'] for r in rows),sum(r['indexed_seconds'] for r in rows))
