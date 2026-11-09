#!/usr/bin/python3
"""Compute a new candidate from serial native live export, not archived candidate."""
import sys,os,json,time,shutil
from pathlib import Path
R=Path(__file__).resolve().parents[2]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from reusable_rr_floor_context import ReusableRRFloors
from shared_rr_inventory import SharedRRInventory
from shared_inventory_exchange_binary import exchange
from current_global_budget_buffered import repair
from serialize_shared_inventory import serialize
from native_route_ledger_import_compact import physical_paths
from source_binding_v2 import closure
from indexed_integer_rc import IndexedIntegerRC
from live_endpoint_binding_v3 import validate as validate_live_endpoints

def produce(stem_value,config,ctx=None,inventory=None):
 start=time.perf_counter();stem=Path(stem_value);binding=json.loads(Path(str(stem)+'.binding.json').read_text());route=Path(str(stem)+'.route');identity=Path(str(stem)+'.identity.jsonl');ep=Path(config['ROUTECAST_SEARCH_ENDPOINT']);report=Path(config['ROUTECAST_SEARCH_REPORT']);place=Path(config['place']);out=Path(str(stem)+'.search');out.mkdir()
 inputs={str(p):sha(p) for p in (route,identity,ep,report,place,Path(str(stem)+'.binding.json'))};sources=closure([Path(__file__)])
 def digest(p):return 'SHA256:'+sha(p)
 assert digest(route)==binding['export_route'] and digest(identity)==binding['identity'] and digest(place)==binding['placement']
 reused=ctx is not None
 if ctx is None:
  ctx=ReusableRRFloors(ep,R/'build/native_resume_rr_floor_cpp_2026-10-07/rr_floor',out/'context');inventory=SharedRRInventory(ctx)
 else:
  ctx._validate(ep);inventory.validate(ctx.graph,ctx.digest)
 if not isinstance(ctx.rc,IndexedIntegerRC):
  ctx.rc=IndexedIntegerRC(ctx.rc,ctx.fields,ctx.initial,inventory)
  ctx.bindings[str(R/'tools/native_resume_prototype/indexed_integer_rc.py')]=sha(R/'tools/native_resume_prototype/indexed_integer_rc.py')
 assert 'SHA256:'+ctx.digest==binding['graph']
 validate_live_endpoints(ep,identity,inventory,route)
 spans={n:1+int(loc['xhigh'])-int(loc['xlow'])+int(loc['yhigh'])-int(loc['ylow']) for n,(kind,loc) in inventory.nodes.items() if kind in ('CHANX','CHANY')}
 budget=sum(sum(spans.get(n,0) for n in {n for path in paths for n,_ in path}) for paths in physical_paths(route).values())
 # Exchange expects own initial timing report next to input route; preserve all live data.
 search_route=out/'design.route';shutil.copyfile(route,search_route);shutil.copyfile(report,out/'report_timing.setup.rpt');prepared=time.perf_counter()
 ex=exchange(ctx,ep,search_route,out/'exchange',inventory);gb=repair(ctx,inventory,ep,ex['records'],report,budget,out/'budget')
 text,pins=serialize(dict(records=gb['records']),ep,identity,place,inventory);candidate=Path(config['ROUTECAST_TX_CANDIDATE']);candidate.write_text(text)
 assert all(sha(p)==h for p,h in inputs.items()) and all(sha(p)==h for p,h in sources.items())
 fields={'epoch':str(binding['epoch']),'next_epoch':str(binding['epoch']+1),**{k:binding[k] for k in ('graph','net','placement','architecture','parent_route')},'candidate':digest(candidate)}
 Path(config['ROUTECAST_TX_REQUEST']).write_text('ROUTECAST_NATIVE_TX_V1\n'+'\n'.join(k+' '+v for k,v in fields.items())+'\nEND\n')
 (out/'receipt.json').write_text(json.dumps(dict(context_reused=reused,inputs=inputs,sources=sources,initial_wire_budget=budget,final_wire=gb['final_wire'],context_and_preparation_seconds=prepared-start,exchange_seconds=ex['total_seconds'],repair_seconds=gb['total_seconds'],producer_seconds=time.perf_counter()-start,accepted_repair_nets=[r['net'] for r in gb['rows'] if r['accepted']],candidate_sha256=sha(candidate),scope='Fresh search from current live export. Prepared endpoint cohort and own pre-existing initial report; report not generated inside this sync hook. Context construction and conversion paid. Serial fixed source; no feedback speed claim.'),indent=2)+'\n')
 return ctx,inventory
