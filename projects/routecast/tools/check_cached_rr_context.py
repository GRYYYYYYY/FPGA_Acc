"""Actual graph cache authentication/read-only and mutable-context isolation."""
import json,tempfile
from pathlib import Path
from dataclasses import FrozenInstanceError
from cached_rr_endpoint_context import clear_cache,STATS,load_endpoints
from owner_union_wire_rc_context_cached import OwnerUnionWireRCContext
from fractions import Fraction
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];p=json.loads((ROOT/'experiments/owner50_serial_2026-10-07_predictor/protocol.json').read_text());case=next(x for x in p['cases'] if x['width']==8);clear_cache();a=OwnerUnionWireRCContext(case['old'],weight_ns=Fraction(1,20));b=OwnerUnionWireRCContext(case['old'],weight_ns=Fraction(1,20));assert STATS=={'builds':1,'hits':1,'evictions':0};assert a.rc is b.rc and a.context[2] is b.context[2];assert a.native.arrays[3] is not b.native.arrays[3] and a.native.other is not b.native.other
before=b.native.arrays[3].tobytes();node=next(n for n in a.destination_slots if a.wire_lengths[n]>0);a.set_history({node:1});a.set_wire_owner_union({node});a.native.set_other({node:1});assert b.native.arrays[3].tobytes()==before and not b.history and not b.wire_owner_union and not b.native.previous
old=b.context[5][0]['source'];a.context[5][0]['source']=-1;assert b.context[5][0]['source']==old
mutations=[lambda:a.rc.fields['costs'].__setitem__(0,0),lambda:a.rc.fields.__setitem__('costs',()),lambda:a.context[2][0].attrib.__setitem__('type','BAD'),lambda:setattr(a.rc,'scale',0),lambda:a.rc.rc.cache.__setitem__((0,0),Fraction(0))]
for mutate in mutations:
 try:mutate()
 except (TypeError,AttributeError,FrozenInstanceError):pass
 else:raise AssertionError('shared snapshot mutable')
with tempfile.TemporaryDirectory(prefix='routecast-cache-contract-') as directory:
 for field in ('graph_sha256','place_sha256'):
  ep=json.loads(Path(case['old']).read_text())
  if field=='graph_sha256':ep[field]='0'*64
  else:ep['inputs']['place']['sha256']='0'*64
  f=Path(directory)/'bad.json';f.write_text(json.dumps(ep));stats=dict(STATS)
  try:load_endpoints(f)
  except ValueError:pass
  else:raise AssertionError('unauthenticated cache hit')
  assert STATS==stats
out=ROOT/'experiments/cached_rr_context_contract_2026-10-07';out.mkdir();(out/'verification.json').write_text(json.dumps(dict(loader_sha256=sha(ROOT/'tools/cached_rr_endpoint_context.py'),checker_sha256=sha(Path(__file__)),stats=STATS,scope='Actual width8 sharedread-only arrays/RC/electrical/XML metadata, isolated native cost/history/owner/demand/endpointqueries, corrupt graph/placement hash rejected before cache access. Three-entry eviction policy inspected but not exercised; graph-file mutation race/concurrent use not guaranteed. Wholecohort physical behavior proof separate.'),indent=2)+'\n');print('Actual cached graph authentication/isolation contract passed')
