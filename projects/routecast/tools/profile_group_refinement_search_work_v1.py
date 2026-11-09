"""All terminal group logs: work/status and graph-only raw-bound reuse domains."""
import json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];E=R/'experiments';I=E/'prospective_external_family_sequential_group_refinement_v1_2026-10-20';D=E/'group_refinement_search_work_profile_v1_2026-10-20'
def read(p):return json.loads(p.read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 decision=read(I/'research_decision_v1.json');assert all(sha(p)==h for p,h in decision['bindings'].items());D.mkdir(exist_ok=False);cases=read(I/'protocol.json')['cases'];bindings={str(I/'research_decision_v1.json'):sha(I/'research_decision_v1.json'),str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for c in cases:
  case=c['case'];out=I/case/'on';audit=read(out/'complete_event_audit.json');eventsfile=out/'events.jsonl';assert sha(eventsfile)==audit['bindings'][str(eventsfile)];summary=read(out/'component_summary.json');ep=read(Path(c['endpoint']));n=read(Path(c['node_base_proof']))['nodes'];schedule=read(E/'prospective_external_family_blocker_root_pair_schedule_v2_2026-10-20'/case/'schedule.json');query_status=Counter();failed_status=Counter();targetqueries=Counter();targetlabels=Counter();targetbudgets=set();status_seconds=Counter();fanout=defaultdict(Counter);labels=expanded=calls=groups=0;seconds=0.;slow=[]
  for line in eventsfile.open():
   event=json.loads(line);groups+=1;elapsed=event['seconds'];seconds+=elapsed;status_seconds[event['status']]+=elapsed;scheduled=schedule[event['index']]['connections'];bucket=fanout[scheduled];bucket['groups']+=1;bucket['seconds']+=elapsed;groupcalls=grouplabels=0
   for net in event['search']['events']:
    for q in net['queries']:
     query_status[q['status']]+=1;calls+=1;groupcalls+=1;labels+=q['labels_created'];grouplabels+=q['labels_created'];expanded+=q['expanded'];targetqueries[q['target']]+=1;targetlabels[q['target']]+=q['labels_created'];targetbudgets.add((q['target'],q['budget']))
   if event['status']=='NO_COMPLETE_GROUP_PROPOSAL':failed_status[event['search']['events'][-1]['queries'][-1]['status']]+=1
   bucket['queries']+=groupcalls;bucket['labels']+=grouplabels;slow.append(dict(index=event['index'],members=event['members'],seconds=elapsed,scheduled_connections=scheduled,query_calls=groupcalls,labels_created=grouplabels,status=event['status']))
  assert groups==summary['groups']==audit['groups'];assert sum(failed_status.values())==summary['counts']['NO_COMPLETE_GROUP_PROPOSAL'];input_targets={q['sink'] for q in ep['connections']};assert set(targetqueries)<=input_targets;memory=dict(nodes=n,actual_queried_targets=len(targetqueries),all_input_targets=len(input_targets),actual_target_budget_pairs=len(targetbudgets),u64_target_only_payload_bytes=n*8*len(targetqueries),u64_all_input_target_payload_bytes=n*8*len(input_targets),u64_target_budget_payload_bytes=n*8*len(targetbudgets),scope='Payload estimate only, excludes reverse CSR, transient Dijkstra, Python objects/cache/view metadata. No measured cache footprint or runtime benefit claim.')
  row=dict(case=case,groups=groups,scheduled_CID_visits=sum(q['connections'] for q in schedule),actual_query_calls=calls,query_status_counts=dict(query_status),NO_COMPLETE_last_query_status_counts=dict(failed_status),labels_created=labels,expanded=expanded,sum_event_seconds=seconds,component_seconds=summary['component_seconds'],seconds_by_group_status=dict(status_seconds),raw_bound_reuse=memory);rows.append(row);dest=D/case;dest.mkdir(parents=True);files=[]
  for name,value in [('fanout_work.json',{str(k):dict(v) for k,v in sorted(fanout.items())}),('slowest_groups.json',sorted(slow,key=lambda q:(-q['seconds'],q['index']))[:20]),('target_work.json',[dict(target=t,queries=targetqueries[t],labels=targetlabels[t]) for t in sorted(targetqueries,key=lambda t:(-targetlabels[t],t))])]:
   p=dest/name;p.write_text(json.dumps(value,indent=2)+'\n');files.append(p)
  for p in [eventsfile,out/'complete_event_audit.json',out/'component_summary.json',Path(c['endpoint']),Path(c['node_base_proof']),*files]:bindings[str(p)]=sha(p)
  print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL24953_TERMINAL_GROUPS_QUERY_WORK_AND_RAW_BOUND_REUSE_PROFILE_COMPLETE',rows=rows,bindings=bindings,scope='No labels, searches or model changes. Work counters are recorded runtime counters, not independent CPU attribution. Bound-memory figures are hypothetical packed payloads only.'),indent=2)+'\n')
if __name__=='__main__':main()
