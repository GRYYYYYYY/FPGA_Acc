"""Independent XML budget/tree/owner replay of every sequential batch event."""
import json,sys,hashlib,xml.etree.ElementTree as ET
from pathlib import Path
from collections import defaultdict,Counter
from fractions import Fraction
from array import array

def read(p):return json.loads(Path(p).read_text())
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(state):return hashlib.sha256(json.dumps(state,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def main():
 out=Path(sys.argv[1]).resolve();p=read(out/'protocol.json');receipt=read(out/'receipt.json');assert p['bindings']==receipt['bindings'] and p['max_labels_per_query']==10000;bindings={**p['bindings'],**receipt['files'],str(out/'receipt.json'):sha(out/'receipt.json'),str(Path(__file__).resolve()):sha(__file__)};assert all(sha(k)==h for k,h in bindings.items());initial=read(out/'initial_round.json');baseline=Path(p['baseline']);assert initial==read(baseline/'round1.json');assert read(baseline/'complete_event_audit.json')['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'];ep=read(p['endpoint']);graph=Path(ep['inputs']['graph']['path']);schedule=read(p['schedule']);needed=set()
 for q in initial['records']:needed.update(q['answer']['physical_edge_ids'])
 for line in (out/'events.jsonl').open():
  event=json.loads(line)
  for recs in event.get('candidate',{}).values():
   for q in recs:needed.update(q['answer']['physical_edge_ids'])
 caps={};spans={};edges={};weights={};eid=0;stack=[]
 for kind,e in ET.iterparse(graph,events=('start','end')):
  if kind=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   n=int(e.get('id'));caps[n]=int(e.get('capacity'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
   if e.get('type') in ('CHANX','CHANY'):
    loc=e.find('loc');spans[n]=1+max(int(loc.get('xhigh'))-int(loc.get('xlow')),int(loc.get('yhigh'))-int(loc.get('ylow')))
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert Fraction(t.get('R','0'))==0;w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;weights[int(e.get('id'))]=w.numerator
  elif e.tag=='edge' and parent=='rr_edges':
   if eid in needed:edges[eid]=int(e.get('src_node')),int(e.get('sink_node')),int(e.get('switch_id'))
   eid+=1
  if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert set(edges)==needed;initial_ids=[q['connection_id'] for q in initial['records']];records={q['connection_id']:q for q in initial['records']};assert len(records)==len(initial_ids)==len(ep['connections'])==15616;queries={q['connection_id']:q for q in ep['connections']};netcids=defaultdict(set)
 for cid,q in records.items():assert all(q[k]==v for k,v in queries[cid].items());netcids[q['net_id']].add(cid)
 def physical(recs):
  owned=set();parents={}
  for q in recs:
   u=q['source'];seen={u};value=0;owned.add(u)
   for eid in q['answer']['physical_edge_ids']:
    a,b,s=edges[eid];assert a==u and b not in seen and caps[b]>0;assert b not in parents or parents[b]==(a,eid);parents[b]=a,eid;seen.add(b);owned.add(b);value+=weights[s];u=b
   assert u==q['sink'] and q['answer']['status']=='FOUND' and value==q['answer']['delay']<=q['budget_integer']
  return owned
 owners={n:physical([records[cid] for cid in cids]) for n,cids in netcids.items()};ledger=Counter(u for ns in owners.values() for u in ns);assert dict(ledger)=={int(n):v for n,v in initial['ledger'].items()};epochs={int(n):v for n,v in initial['epochs'].items()};assert set(epochs)==set(netcids);history={int(n):v-spans.get(int(n),0) for n,v in initial['prices'].items()};assert all(v>=0 for v in history.values());crit={q['connection_id']:Fraction(q['criticality_numerator'],q['criticality_denominator']) for q in read(baseline/'timing_round1.json')['criticalities']};base=array('Q');base.frombytes((Path(p['node_base_proof']).parent/'node_base.u64').read_bytes());assert len(base)==len(caps);counts=Counter();checked=checkpoint_count=changed_connections=0
 def frame():return dict(records=[records[cid] for cid in initial_ids],ledger={str(n):v for n,v in ledger.items()},epochs={str(n):v for n,v in epochs.items()},prices=initial['prices'])
 for index,line in enumerate((out/'events.jsonl').open()):
  e=json.loads(line);assert index<len(schedule) and e['index']==index and e['members']==schedule[index]['members'];members=e['members'];assert members==sorted(set(members)) and len(members)==2;expected={int(n):v for n,v in e['expected_epochs'].items()};assert expected=={n:epochs[n] for n in members}
  if not p['enabled']:assert e['status']=='DISABLED' and 'search' not in e and 'candidate' not in e
  else:
   search=e['search'];assert [item['net_id'] for item in search['events']]==members[:len(search['events'])]
   for item in search['events']:
    for q in item['queries']:assert 0<=q['expanded']<=q['labels_created']<=10000
   if e['status']=='NO_COMPLETE_GROUP_PROPOSAL':assert 'candidate' not in e and not search['events'][-1]['complete'] and search['status']=='NO_COMPLETE_GROUP_PROPOSAL'
   else:
    assert search['status']=='COMPLETE_GROUP_PROPOSAL' and all(q['complete'] for q in search['events']);candidate={int(n):recs for n,recs in e['candidate'].items()};assert set(candidate)==set(members);newowners={}
    for n,recs in candidate.items():
     assert len(recs)==len(netcids[n]) and {q['connection_id'] for q in recs}==netcids[n]
     for q in recs:assert {k:v for k,v in q.items() if k!='answer'}=={k:v for k,v in records[q['connection_id']].items() if k!='answer'}
     newowners[n]=physical(recs)
    oldcount=Counter(u for n in members for u in owners[n]);newcount=Counter(u for n in members for u in newowners[n]);outside=Counter(ledger);outside.subtract(oldcount);assert min(outside.values())>=0;scratch=Counter(outside)
    for n in members:
     source=candidate[n][0]['source'];scratch[source]+=1;assert all(scratch[u]<caps[u] for u in newowners[n]-{source});scratch.update(newowners[n]-{source})
    def score(recs):
     value=sum((crit[q['connection_id']]*q['answer']['delay'] for q in recs),Fraction(0));users=defaultdict(list)
     for q in recs:
      for eid in q['answer']['physical_edge_ids']:users[edges[eid][1]].append(crit[q['connection_id']])
     for u,cs in users.items():value+=(1-max(cs))*(base[u]*(1+history.get(u,0))*(1+max(0,outside[u]-caps[u]+1))+(10**18//20000000000)*spans.get(u,0))
     return value
    before=sum((score([records[cid] for cid in netcids[n]]) for n in members),Fraction(0));after=sum((score(candidate[n]) for n in members),Fraction(0));updates={u:ledger[u]-oldcount[u]+newcount[u] for u in oldcount.keys()|newcount.keys() if oldcount[u]!=newcount[u]};assert all(v>=0 for v in updates.values());delta=sum(max(0,v-caps[u])-max(0,ledger[u]-caps[u]) for u,v in updates.items());plan=e['plan'];accepted=delta<=0 and after<=before;assert plan['members']==members;assert plan['status']==('ADMIT_GROUP_PROPOSAL' if accepted else 'RETAIN_GROUP_OBJECTIVE_INCREASE' if after>before else 'RETAIN_GROUP_OVERFLOW_INCREASE');assert plan['accepted']==accepted and plan['prospective_overflow_delta']==delta and {int(n):v for n,v in plan['updates'].items()}==updates;assert Fraction(plan['old_score'])==before and Fraction(plan['candidate_score'])==after and Fraction(plan['objective_delta'])==after-before;same=all({q['connection_id']:q for q in candidate[n]}=={cid:records[cid] for cid in netcids[n]} for n in members);expected_status='RETAIN_GROUP_OBJECTIVE_INCREASE' if after>before else 'RETAIN_GROUP_OVERFLOW_INCREASE' if delta>0 else 'RETAIN_IDENTICAL_PROPOSAL' if same else 'GROUP_DRAFT_MATERIALIZED';assert e['status']==expected_status
    if e['status']=='GROUP_DRAFT_MATERIALIZED':
     assert {int(n):v for n,v in e['result_epochs'].items()}=={n:epochs[n]+1 for n in members}
     for n in members:
      changed_connections+=sum(records[q['connection_id']]['answer']['physical_edge_ids']!=q['answer']['physical_edge_ids'] for q in candidate[n]);records.update({q['connection_id']:q for q in candidate[n]});owners[n]=newowners[n];epochs[n]+=1
     for u,v in updates.items():
      if v:ledger[u]=v
      else:ledger.pop(u,None)
    else:assert 'result_epochs' not in e
  counts[e['status']]+=1;checked+=1
  if (index+1)%256==0 or index+1==len(schedule):
   assert ledger==Counter(u for ns in owners.values() for u in ns);assert e['state_digest_after']==digest(frame());checkpoint_count+=1
  else:assert 'state_digest_after' not in e
 assert checked==len(schedule);assert read(out/'final_round.json')==frame();summary=read(out/'component_summary.json');assert summary['counts']==dict(counts) and summary['initial_digest']==digest(initial) and summary['final_digest']==digest(frame());sketch=read(out/'sketch.json');assert sketch['records']==frame()['records'] and sketch['ledger']==frame()['ledger'] and sketch['epochs']==frame()['epochs'];assert sketch['completed_connections']==sketch['required_connections']==15616 and not sketch['eligible_for_legal_route_commit'];assert sketch['overflow_units']==sum(max(0,v-caps[u]) for u,v in ledger.items()) and sketch['overflow_nodes']==sum(v>caps[u] for u,v in ledger.items());independent=Counter()
 for q in records.values():independent.update({q['source']}|{edges[eid][1] for eid in q['answer']['physical_edge_ids']})
 assert dict(independent)=={int(n):v for n,v in sketch['independent_connection_ledger'].items()}
 if not p['enabled']:assert frame()==initial and sketch==read(baseline/'sketch.json')
 assert all(sha(k)==h for k,h in bindings.items());result=dict(bindings=bindings,case=p['case'],enabled=p['enabled'],all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass=True,complete_group_schedule_expected_epochs_records_and_noop_replay_pass=True,complete_group_vacancy_mask_common_snapshot_objective_and_fullgraph_pressure_pass=True,complete_periodic_actual_state_digest_and_final_frame_rebuild_pass=True,real_search_weighted_optimality_and_failure_infeasibility_not_claimed=True,groups=checked,checkpoints=checkpoint_count,counts=dict(counts),changed_connection_events=changed_connections,completed=15616,overflow_units=sketch['overflow_units'],scope='Every supplied complete candidate and accepted group independently audited. UNKNOWN remains unknown. Periodic runtime state digests and complete final frame checked; no external concurrent publication or latest timing equivalence claim.');Path(sys.argv[2]).write_text(json.dumps(result,indent=2)+'\n');print('ALL_GROUP_REFINEMENT_EVENTS_AUDITED',p['case'],p['enabled'],checked,dict(counts),flush=True)
if __name__=='__main__':main()
