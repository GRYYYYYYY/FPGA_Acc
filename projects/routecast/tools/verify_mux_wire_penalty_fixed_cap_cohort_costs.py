"""Recompute every found repair query cost/delay under archived raw history."""
import json
from pathlib import Path
from collections import Counter
from nonzero_rc_endpoint_context import load_endpoints
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_wire_penalty_fixed_cap_cohort_2026-10-07';p=json.loads((out/'protocol.json').read_text());last=None
from fractions import Fraction as F
assert p['wire_penalty_weight_ns']=='1/100'
for case in p['cases']:
 w,i=case['width'],case['index'];file=out/f'w{w}_m{i}/result.json'
 if not file.exists():continue
 if w!=last:
  ctx=load_endpoints(case['old']);rc=ctx[4];unit=F(p['wire_penalty_weight_ns'])*rc.scale/10**9;assert unit.denominator==1
  lengths=[]
  for node in ctx[2]:
   loc=node.find('loc');kind=node.get('type');length=(int(loc.get('xhigh'))-int(loc.get('xlow'))+1) if kind=='CHANX' else ((int(loc.get('yhigh'))-int(loc.get('ylow'))+1) if kind=='CHANY' else 0);lengths.append(length)
  slots={eid:s for s,eid in enumerate(rc.fields['edge_ids'])};last=w
 d=json.loads(file.read_text());rows=[]
 for j,attempt in enumerate(d['attempts']):
  initial=attempt['update']['incremental'];final=attempt['update']['repair'];history=Counter({int(k):v for k,v in initial['history'].items()});found=0;releases=0
  events=[dict(e,type='QUERY') for e in initial['events']]+(final['events'] if final else [])
  for e in events:
   if e['type'] in ('QUERY','BUDGET_WITNESS') and e['answer']['status']=='FOUND':
    q=e['query'];a=e['answer'];cost=delay=0
    for eid in a['physical_edge_ids']:
     slot=slots[eid];increment=rc.increments[slot];count=history[rc.fields['dest_ranks'][slot]];cost+=increment*(1+count)**2+int(unit)*lengths[rc.fields['dest_ranks'][slot]];delay+=increment
    assert cost==a['cost'] and delay==a['delay']==rc.path(q['source'],q['sink'],a['physical_edge_ids']);found+=1
   elif e['type']=='RELEASE':
    history.update(e['frontier']);assert dict(history)=={int(k):v for k,v in e['history_after'].items()};assert {k:v*(v+2) for k,v in history.items()}=={int(k):v for k,v in e['effective_history_after'].items()};releases+=1
  snapshot=final or initial
  assert dict(history)=={int(k):v for k,v in snapshot['history'].items()};assert releases==(final['repairs'] if final else 0);rows.append(dict(attempt=j,found_queries=found,releases=releases))
 (file.parent/'history_cost_verification.json').write_text(json.dumps(dict(result_sha256=sha(file),verifier_sha256=sha(Path(__file__)),rows=rows,scope='Every FOUND staging/repair QUERY/BUDGET_WITNESS exact integer path cost equals sum original increments*(1+raw visits)^2 plus fixed10ps destination channel-span units, independently derived from original XML loc/type and unchanged path delay; raw/effective history recurrence and final equality. Shared authenticated integer context; original XML/Fraction physical auditor remains separate. Failed queries have no returned path to audit.'),indent=2)+'\n');print(w,i,'verified history cost',sum(r['found_queries'] for r in rows),flush=True)
