"""Nonzero live scratch state restored after injected query failures and badbinding."""
import json
from pathlib import Path
from fractions import Fraction
from pre_route_endpoints import sha
from owner_union_wire_rc_context_cached import OwnerUnionWireRCContext
from capacity_local_demand import CapacityAbsoluteDemand
from native_route_ledger_import_compact import import_native_ledger
import bitonic_baseline_staged_reroute as baseline
import resident_staged_placement_reroute as resident
ROOT=Path(__file__).resolve().parents[1];parent=ROOT/'experiments/bitonic_resident_live_staging_2026-10-07';p=json.loads((parent/'protocol.json').read_text());out=ROOT/'experiments/resident_staging_rollback_contract_2026-10-07';out.mkdir();rows=[]
for case in p['cases']:
 ctx=OwnerUnionWireRCContext(case['old'],weight_ns=Fraction(1,20));ctx.native.__class__=CapacityAbsoluteDemand;ctx.native.demand_epoch=ctx.native.delta_calls=ctx.native.delta_writes=ctx.native.publication_calls=ctx.native.publication_writes=0;state=import_native_ledger(ctx,Path(case['source'])/'design.route');node=next(i for i,n in enumerate(ctx.context[2]) if n.get('type')=='CHANX');ctx.set_history({node:1});ctx.set_wire_owner_union({node});ctx.native.set_other({node:1});context=ctx.context;metadata=ctx.endpoint_metadata;records=json.dumps(state.records,sort_keys=True);unions={k:set(v) for k,v in state.unions.items()};ledger=dict(state.ledger);parents={k:dict(v) for k,v in state.parents.items()};query=ctx.native.query
 def snapshot():return (dict(ctx.history),ctx.wire_owner_union,ctx.native.other.tobytes(),ctx.native.previous.copy(),ctx.native.arrays[3].tobytes())
 expected=snapshot();count=0
 def fail(*args,**kwargs):raise RuntimeError('injected query failure after demand publication')
 for stage in (baseline,resident):
  ctx.demand_stats=dict(calls=0,writes=0,visited=0,seconds=0.0);ctx.demand_journal=[];ctx.native.query=fail
  try:stage.stage_reroute_with_repair(state,case['target'])
  except RuntimeError as ex:assert str(ex)=='injected query failure after demand publication'
  else:raise AssertionError('injected error swallowed')
  finally:ctx.native.query=query
  assert snapshot()==expected and ctx.context is context and ctx.endpoint_metadata is metadata;assert json.dumps(state.records,sort_keys=True)==records and state.unions==unions and dict(state.ledger)==ledger and state.parents==parents;count+=1
 bad=json.loads(Path(case['target']).read_text());bad['inputs']['place']['sha256']='0'*64;file=out/f"n{case['count']}_invalid_binding.json";file.write_text(json.dumps(bad))
 try:resident.stage_reroute_with_repair(state,file)
 except ValueError:pass
 else:raise AssertionError('badbinding accepted')
 assert snapshot()==expected and ctx.context is context and ctx.endpoint_metadata is metadata;rows.append(dict(count=case['count'],query_failure_rollbacks=count,badbinding_rollback=True,nonzero_history_owner_other_state=True));print(rows[-1],flush=True)
(out/'verification.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),parent_protocol_sha256=sha(parent/'protocol.json'),implementation_sha256={str(ROOT/'tools'/n):sha(ROOT/'tools'/n) for n in ['resident_staged_placement_reroute.py','bitonic_baseline_staged_reroute.py','capacity_local_demand.py']},rows=rows,scope='All3 baseline/resident exceptionalquery and badinput failure paths restore nonzerohistory/owner/nativearray/active-set/costarray/context/metadata/live records/ledger/parents/unions. Epochmonotone remainsadvanced, intentionally invalidates stale demandclients. Serialstaging, not durable transaction/concurrentpublication.'),indent=2)+'\n')
