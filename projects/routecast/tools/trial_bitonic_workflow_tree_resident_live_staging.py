"""Prospective allcase ABBA staging and live state rollback audit, no native gate."""
import json,re,time,hashlib
import xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import extract,placements,physical_maps,sha
from native_place_serialization import canonical_place
from owner_union_wire_rc_context_cached_tree import OwnerUnionWireRCContext
from capacity_local_demand import CapacityAbsoluteDemand
from native_route_ledger_import_compact import import_native_ledger
from owned_reverse_graph import OwnedReverseGraph
import bitonic_baseline_staged_reroute as baseline
import resident_staged_placement_reroute as resident
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/bitonic_workflow_tree_resident_live_staging_2026-10-07';out.mkdir();cases=[]
for n in [4,8,16]:
 src=ROOT/f'work/bitonic_native_reference_2026-10-07/n{n}';net,place,graph=[src/name for name in ['design.net','design.place','rr_graph.xml']];rows=placements(place,sha(net));types,grid,_=physical_maps(graph);pair=[];signature=None
 for block in ET.parse(net).getroot().findall('block'):
  name=block.get('name');logical=re.sub(r'\[\d+\]$','',block.get('instance'))
  if logical!='clb':continue
  x,y,z,layer,_=rows[name];sig=(logical,z,layer,grid[x,y,layer])
  if not pair:pair=[name];signature=sig
  elif sig==signature:pair.append(name);break
 assert len(pair)==2;work=out/f'n{n}';work.mkdir();lines=[]
 for line in place.read_text().splitlines():
  fields=line.split()
  if fields and fields[0] in pair:
   name=fields[0];other=pair[1] if name==pair[0] else pair[0];x,y,z,layer,_=rows[other];line=f'{name}\t{x}\t{y}\t{z}\t{layer}\t#{rows[name][4]}'
  lines.append(line)
 swapped=work/'swapped.place';swapped.write_text('\n'.join(lines)+'\n');swapped.write_text(canonical_place(swapped,net));ep,mapping=extract(net,swapped,graph);(work/'target.json').write_text(json.dumps(ep,indent=2)+'\n');(work/'mapping.json').write_text(json.dumps(mapping,indent=2)+'\n');old=ROOT/f'experiments/bitonic_physical_endpoints_2026-10-07/n{n}/endpoints.json';cases.append(dict(count=n,old=str(old),target=str(work/'target.json'),source=str(src),pair=pair,bindings={str(p):sha(p) for p in [old,work/'target.json',swapped,net,place,graph,src/'design.route']}))
modules=['capacity_local_demand.py','native_capacity_rc_diff_demand.py','resident_staged_placement_reroute.py','bitonic_baseline_staged_reroute.py','resident_four_repair_engine.py','bitonic_owner_wire_four_repair_engine.py','owned_reverse_graph.py','owner_union_wire_rc_context_cached_tree.py','native_route_ledger_import_compact.py'];binary=ROOT/'experiments/mux_owned_bound_cache_2026-10-06/search.so';sources={str(ROOT/'tools'/n):sha(ROOT/'tools'/n) for n in modules};sources[str(Path(__file__))]=sha(Path(__file__));protocol=dict(cases=cases,sources=sources,binary_sha256=sha(binary),order=['resident'],budget_ns=1,max_labels=10000,repair_cap=4,weight_ns='1/20',scope='Allcase firstcompatible CLB pair frozen beforestaging; one resident staging attempt per case. Fresh ownedreversegraph/cache eachrun, build included stageclock; cachedRR/context/seedimport/targetfrontend measured separately. Digest logging inside residentstage. Candidate staging/restoration only, not newnativeacceptance/finalQoR/rawinputnetgain or strictholdout.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');results=[]
def live_digest(state):
 value=dict(records=state.records,ledger=dict(state.ledger),unions={k:sorted(v) for k,v in state.unions.items()},parents={k:dict(v) for k,v in state.parents.items()});return hashlib.sha256(json.dumps(value,sort_keys=True).encode()).hexdigest()
for case in cases:
 n=case['count'];work=out/f'n{n}';tick=time.perf_counter();ctx=OwnerUnionWireRCContext(case['old'],weight_ns=Fraction(1,20));ctx.native.__class__=CapacityAbsoluteDemand;ctx.native.demand_epoch=ctx.native.delta_calls=ctx.native.delta_writes=ctx.native.publication_calls=ctx.native.publication_writes=0;state=import_native_ledger(ctx,Path(case['source'])/'design.route');setup=time.perf_counter()-tick;original_context=ctx.context;metadata=ctx.endpoint_metadata;saved=live_digest(state);history=dict(ctx.history);owner=ctx.wire_owner_union;other=ctx.native.other.tobytes();costs=ctx.native.arrays[3].tobytes();runs=[]
 for index,model in enumerate(protocol['order']):
  ctx.demand_journal=[];ctx.demand_stats=dict(calls=0,writes=0,visited=0,seconds=0.0);tick=time.perf_counter();owned=OwnedReverseGraph(ctx.native.n,len(ctx.rc.fields['edge_ids']),ctx.native.ptrs[0],ctx.native.ptrs[1],ctx.native.ptrs[2],ctx.native.ptrs[5],binary);ctx.native.lib.rc_query=owned.bridge;original_query=ctx.query
  def full_query(*args,**kwargs):
   answer=original_query(*args,**kwargs);ctx.demand_journal.append(dict(source=args[0],sink=args[1],mode='full',epoch=ctx.native.demand_epoch,digest=hashlib.sha256(ctx.native.other.tobytes()).hexdigest()));return answer
  ctx.query=full_query
  try:update=(baseline if model=='baseline' else resident).stage_reroute_with_repair(state,case['target'])
  finally:ctx.query=original_query;owned.close()
  seconds=time.perf_counter()-tick;assert ctx.context is original_context and ctx.endpoint_metadata is metadata and ctx.history==history and ctx.wire_owner_union==owner and ctx.native.other.tobytes()==other and ctx.native.arrays[3].tobytes()==costs and live_digest(state)==saved
  file=work/f'run{index}_{model}.json';file.write_text(json.dumps(update,indent=2)+'\n');(work/f'run{index}_demands.json').write_text(json.dumps(ctx.demand_journal,indent=2)+'\n');chosen=update['repair'] or update['incremental'];runs.append(dict(model=model,seconds=seconds,status=chosen['status'],completed=chosen['completed_connections'],required=chosen['required_connections'],failure=chosen['failure'],update_sha256=sha(file),demands_sha256=sha(work/f'run{index}_demands.json'),rollback_verified=True));print(n,index,model,seconds,chosen['status'],flush=True)
 assert all(sha(f)==h for f,h in case['bindings'].items());results.append(dict(count=n,setup_seconds=setup,initial_live_digest=saved,runs=runs));(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=results,complete=len(results)==3),indent=2)+'\n')
assert all(sha(f)==h for f,h in sources.items())
