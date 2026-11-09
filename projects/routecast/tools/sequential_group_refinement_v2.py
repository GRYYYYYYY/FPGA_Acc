"""Sequential pure-draft refinement over a fixed complete pair schedule.

No shared external state; every accepted candidate replaces only local draft.
"""
import json,hashlib,time
from pathlib import Path
from collections import Counter
from group_vacancy_proposal_v4 import Snapshot,propose
from group_draft_frame_v2 import materialize

def digest(state):return hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def compact(meta):
 return dict(status=meta['status'],failed_NET=meta.get('failed_NET'),events=[dict(net_id=e['net_id'],complete=e['complete'],first_failed_connection_id=e['first_failed_connection_id'],queries=[{k:v for k,v in q.items() if k not in ('initial_arrivals','path_slots')} for q in e['search_events']]) for e in meta['events']])
def plan_fields(plan):return {k:(str(plan[k]) if k in ('old_score','candidate_score','objective_delta') else plan[k]) for k in ['accepted','status','old_score','candidate_score','objective_delta','prospective_overflow_delta','updates','members']}

def refine(fields,rc,slots,original,queries,criticalities,node_base,spans,state,schedule,output,enabled,max_labels=10000):
 if type(enabled) is not bool:raise ValueError('refinement flag')
 output=Path(output);output.mkdir(parents=True,exist_ok=False);initial_digest=digest(state);(output/'initial_round.json').write_text(json.dumps(state)+'\n');history={int(n):v-spans.get(int(n),0) for n,v in state['prices'].items()};assert all(v>=0 for v in history.values());queries_by_net={}
 for q in queries:queries_by_net.setdefault(q['net_id'],[]).append(q)
 base=tuple(node_base);caps=tuple(fields['capacities']);counts=Counter();start=time.perf_counter();initial_order=[q['connection_id'] for q in state['records']]
 with (output/'events.jsonl').open('x') as events:
  for index,item in enumerate(schedule):
   members=item['members'];assert members==sorted(set(members)) and len(members)==2;expected={n:state['epochs'][str(n)] for n in members};event=dict(index=index,members=members,expected_epochs=expected,status='DISABLED');tick=time.perf_counter()
   if enabled:
    groups={n:[] for n in members}
    for q in state['records']:
     if q['net_id'] in groups:groups[q['net_id']].append(q)
    snapshot=Snapshot(fields,rc,slots,{n:queries_by_net[n] for n in members},groups,{int(n):v for n,v in state['ledger'].items()},criticalities,base,history,spans,rc.scale//(20*10**9));candidate,meta=propose(snapshot,original,max_labels);event['search']=compact(meta)
    if candidate is None:event['status']='NO_COMPLETE_GROUP_PROPOSAL'
    else:
     event['candidate']=candidate;event['plan']=plan_fields(meta['plan']);same=all({q['connection_id']:q for q in candidate[n]}=={q['connection_id']:q for q in groups[n]} for n in members)
     if not meta['plan']['accepted']:event['status']=meta['plan']['status']
     elif same:event['status']='RETAIN_IDENTICAL_PROPOSAL'
     else:
      draft,materialized=materialize(snapshot,candidate,state,expected);assert draft is not None and materialized['status']=='GROUP_DRAFT_MATERIALIZED';assert materialized['plan']==meta['plan'];state=draft;event['status']='GROUP_DRAFT_MATERIALIZED';event['result_epochs']=materialized['result_epochs']
   counts[event['status']]+=1;event['seconds']=time.perf_counter()-tick
   if (index+1)%256==0 or index+1==len(schedule):
    assert [q['connection_id'] for q in state['records']]==initial_order;event['state_digest_after']=digest(state);print('GROUP_REFINEMENT',output.name,index+1,len(schedule),dict(counts),flush=True)
   events.write(json.dumps(event)+'\n');events.flush()
 (output/'final_round.json').write_text(json.dumps(state)+'\n');summary=dict(status='ALL_FIXED_GROUPS_PROCESSED',enabled=enabled,groups=len(schedule),counts=dict(counts),initial_digest=initial_digest,final_digest=digest(state),component_seconds=time.perf_counter()-start,policy='Complete fixed schedule; numeric NET order; unchanged current history and criticality;10000 perquery labels in trial; identical proposals are audited no-ops. No external state publication.')
 (output/'component_summary.json').write_text(json.dumps(summary,indent=2)+'\n');return state,summary
