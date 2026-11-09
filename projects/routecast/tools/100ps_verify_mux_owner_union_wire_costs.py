"""Replay real NET unions and verify each owner-aware query wire increment."""
import json
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction as F
from persistent_rc_context import PersistentRCContext
from native_route_ledger_import import import_native_ledger
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_owner_wire_100ps_development_2026-10-07';p=json.loads((out/'protocol.json').read_text());last=None
for case in p['cases']:
 w,i=case['width'],case['index'];file=out/f'w{w}_m{i}/result.json'
 if not file.exists():continue
 if w!=last:
  ctx=PersistentRCContext(case['old']);ep=ctx.endpoint_metadata;oldroute=Path(ep['inputs']['net']['path']).parent/'design.route';state=import_native_ledger(ctx,oldroute);f=ctx.rc.fields;rc=ctx.rc;slots={eid:s for s,eid in enumerate(f['edge_ids'])};lengths=[]
  for node in ctx.context[2]:
   loc=node.find('loc');kind=node.get('type');length=(int(loc.get('xhigh'))-int(loc.get('xlow'))+1) if kind=='CHANX' else ((int(loc.get('yhigh'))-int(loc.get('ylow'))+1) if kind=='CHANY' else 0);lengths.append(length)
  unit=F(p['wire_penalty_weight_ns'])*rc.scale/10**9;assert unit.denominator==1;last=w
 target=json.loads(Path(case['target']).read_text());queries={q['connection_id']:q for q in target['connections']};d=json.loads(file.read_text());rows=[]
 def used(q,answer):
  node=q['source'];nodes={node}
  for eid in answer['physical_edge_ids']:
   slot=slots[eid];edge_source=slot_sources[slot];assert edge_source==node;node=f['dest_ranks'][slot];assert node not in nodes;nodes.add(node)
  assert node==q['sink'];return nodes
 slot_sources={s:u for u in range(ctx.native.n) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])}
 for j,attempt in enumerate(d['attempts']):
  initial=attempt['update']['incremental'];final=attempt['update']['repair'];expanded=set(d['allocations'][attempt['allocation_index']]['expanded']);nets={queries[c]['net_id'] for c in expanded};unions=defaultdict(set,{n:set(v) for n,v in state.unions.items() if n not in nets});records={cid:r for cid,r in state.records.items() if r['net_id'] not in nets};history=Counter({int(k):v for k,v in initial['history'].items()});assert not history;found=0;releases=0;wire_units=0
  def verify_query(e,commit):
   q=e['query'];assert q==queries[q['connection_id']];owner=unions[q['net_id']];assert e['wire_owner_union']==sorted(owner);answer=e['answer']
   if answer['status']!='FOUND':assert not commit;return 0,0
   path=used(q,answer);delay=cost=0
   for eid in answer['physical_edge_ids']:
    slot=slots[eid];n=f['dest_ranks'][slot];inc=rc.increments[slot];delay+=inc;cost+=inc*(1+history[n])**2+(0 if n in owner else int(unit)*lengths[n])
   added=sum(lengths[n] for n in path-owner);basecost=sum(rc.increments[slots[eid]]*(1+history[f['dest_ranks'][slots[eid]]])**2 for eid in answer['physical_edge_ids']);assert cost-basecost==int(unit)*added;assert cost==answer['cost'] and delay==answer['delay']==rc.path(q['source'],q['sink'],answer['physical_edge_ids'])
   if commit:
    assert q['connection_id'] not in records;before=sum(lengths[n] for n in owner);owner.update(path);assert sum(lengths[n] for n in owner)-before==added;records[q['connection_id']]={**q,'answer':answer}
   return 1,added
  for e in initial['events']:
   n,added=verify_query(e,e['committed']);found+=n;wire_units+=added
  assert set(records)=={r['connection_id'] for r in initial['records']}
  if final:
   for e in final['events']:
    if e['type'] in ('QUERY','BUDGET_WITNESS'):
     n,added=verify_query(e,e.get('committed',False));found+=n;wire_units+=added
    elif e['type']=='RELEASE':
     assert e['removed_connection_ids']==sorted(cid for cid,r in records.items() if r['net_id'] in e['blocker_NETs'])
     for net in e['blocker_NETs']:assert e['released_unions'][str(net)]==sorted(unions[net]);del unions[net]
     for cid in e['removed_connection_ids']:del records[cid]
     history.update(e['frontier']);assert dict(history)=={int(k):v for k,v in e['history_after'].items()};assert {n:c*(c+2) for n,c in history.items()}=={int(k):v for k,v in e['effective_history_after'].items()};releases+=1
  snapshot=final or initial;assert set(records)=={r['connection_id'] for r in snapshot['records']};assert dict(history)=={int(k):v for k,v in snapshot['history'].items()};assert releases==(final['repairs'] if final else 0)
  expected=defaultdict(set)
  for r in snapshot['records']:expected[r['net_id']].update(used(r,r['answer']))
  assert {n:v for n,v in unions.items() if v}==dict(expected)
  rows.append(dict(attempt=j,found_queries=found,releases=releases,witness_new_wire_units=wire_units))
 (file.parent/'history_cost_verification.json').write_text(json.dumps(dict(result_sha256=sha(file),verifier_sha256=sha(Path(__file__)),old_route_sha256=sha(oldroute),rows=rows,scope='Every staging/repair query owner hint equals independently replayed actual NET union; every FOUND exact RC/history/new-channel-wire cost, committed wire delta and release-history/final-union recurrence checked. Original XML geometry via shared authenticated loader, physical audit separate. Witness wire units include uncommitted paths, not final route wirelength/time.'),indent=2)+'\n');print(w,i,'owner costs verified',sum(x['found_queries'] for x in rows),flush=True)
