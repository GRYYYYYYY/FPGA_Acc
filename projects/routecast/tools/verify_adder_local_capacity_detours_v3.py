"""Independent physical/Fraction and partial-state replay of joint NET rerouting."""
import json,hashlib
from collections import defaultdict
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from unified_rr_audit_inventory_v2 import read
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';B=E/'adder_local_capacity_detours_v3_2026-10-09';D=E/'adder_local_capacity_detours_verification_v3_2026-10-09';D.mkdir(exist_ok=False);rp=B/'verification.json';report=json.loads(rp.read_text());bindings={**report['bindings'],str(rp):sha(rp),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());dp=B/'step_3.json';data=json.loads(dp.read_text());ep=E/'adder_tree_2L032_move_sequence_2026-10-06/step_3_endpoints.json';meta=json.loads(ep.read_text());q={x['connection_id']:x for x in meta['connections']};bp=E/'adder_legal_route_budget_fixture_v1_2026-10-09/step_3_budgets.json';budgets={x['connection_id']:F(*x['exact_delay_s']) for x in json.loads(bp.read_text())};inv=read(meta['inputs']['graph']['path'],meta['graph_sha256']);bank={int(c):opts for c,opts in data['bank'].items()};assert set(bank)==set(q)
for cid,options in bank.items():
 assert options
 for option in options:
  path=option['path'];assert path[0]==[q[cid]['source'],None] and path[-1][0]==q[cid]['sink'] and len({n for n,s in path})==len(path);r,c=inv.classes[inv.node_classes[q[cid]['source']]];delay=r*c/2
  for (u,_),(v,s) in zip(path,path[1:]):
   assert inv.arc_multiplicities.get((u,v,s))==1;r,c=inv.classes[inv.node_classes[v]];sr,td=inv.electrical_switches[s];delay+=(sr+r/2)*c+td
  assert delay==F(*option['exact_delay_s']) and delay<=budgets[cid]
from class_cached_rc_endpoint_context_v1 import load_endpoints
_,_,_,_,rc,_=load_endpoints(ep);found=0
for event in data['events']:
 cid=event['connection_id'];scaled=budgets[cid]*rc.scale;assert event['integer_budget']==scaled.numerator//scaled.denominator
 if event['status']=='FOUND':
  path=event['path'];assert any(o['path']==path for o in bank[cid]);assert not set(event['blocked_nodes'])&{n for n,s in path};assert [inv.physical.arcs[u,v,s] for (u,_),(v,s) in zip(path,path[1:])]==event['physical_edge_ids'];assert rc.path(q[cid]['source'],q[cid]['sink'],event['physical_edge_ids'])==event['delay'];found+=1
 else:assert event['status'] in ('NO_STRICT_IMPROVEMENT','LABEL_LIMIT') and event['physical_edge_ids'] is None
assert len(data['events'])==report['queries']
for p in (dp,ep,bp):bindings[str(p)]=sha(p)
assert all(sha(p)==h for p,h in bindings.items());out=dict(bindings=bindings,candidates=sum(map(len,bank.values())),found_events=found,queries=len(data['events']),scope='All candidate paths original physical arcs/Fraction budget; successful searches avoid declared nodes and exact integer delay matches. Negative search outcomes are not independently certified graph infeasibility. No complete route claim.');(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'})
