"""Independent localized mask, full owner and per-attempt shortest exchange replay."""
import json,sys,re,heapq
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[2];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
seq=R/'experiments/native_resume_postroute_batch_integrated_adder_2026-10-07';results=[];bindings={str(Path(__file__)):sha(__file__)}
for index in (1,2,3):
 b=R/f'experiments/native_resume_postroute_batch_integrated_adder_step{index}_workflow_2026-10-07/first/live.search';r=json.loads((b/'exchange/receipt.json').read_text());raw=list(map(json.loads,(b/'exchange/output.jsonl').read_text().splitlines()));ep=R/f'experiments/adder_tree_2L032_move_sequence_2026-10-06/step_{index}_endpoints.json';meta=json.loads(ep.read_text());graph,digest,nodes,f,rc,qs=load_endpoints(ep);paths=physical_paths(b/'design.route');xml_nodes={int(n.get('id')):n for n in nodes};span={n:1+int(e.find('loc').get('xhigh'))-int(e.find('loc').get('xlow'))+int(e.find('loc').get('yhigh'))-int(e.find('loc').get('ylow')) for n,e in xml_nodes.items() if e.get('type') in ('CHANX','CHANY')};lookup={(u,f['dest_ranks'][s],f['switch_ids'][s]):s for u in range(len(nodes)) for s in range(f['row_offsets'][u],f['row_offsets'][u+1])};slot_source=[0]*len(f['edge_ids'])
 for u in range(len(nodes)):
  for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):slot_source[s]=u
 groups={};queries={}
 for q in qs:
  name=meta['net_names'][str(q['net_id'])];ps=[p for p in paths[name] if p[0][0]==q['source'] and p[-1][0]==q['sink']];assert len(ps)==1;groups.setdefault(name,{})[q['connection_id']]=[lookup[u,v,sw] for (u,_),(v,sw) in zip(ps[0],ps[0][1:])];queries[q['connection_id']]=q
 def tree(name,records):
  source=queries[next(iter(groups[name]))]['source'];dist={source:rc.initial(source)};parent={}
  for slots in records.values():
   u=source;cost=rc.initial(source)
   for slot in slots:
    assert slot_source[slot]==u;v=f['dest_ranks'][slot];cost+=rc.increments[slot];assert v not in parent or parent[v]==slot;assert v not in dist or dist[v]==cost;parent[v]=slot;dist[v]=cost;u=v
  return dist,parent,sum(span.get(n,0) for n in dist)
 owners={name:set(tree(name,records)[0]) for name,records in groups.items()};occ=Counter(n for owner in owners.values() for n in owner);rank=sorted(groups,key=lambda name:(-tree(name,groups[name])[2],name));critical=[];report=(b/'report_timing.setup.rpt').read_text().split('#Path 2')[0]
 for name,port in re.findall(r'^(\S+)\.(inpad|out|Q)\[\d+\]\s+\(',report,re.M):
  if name in groups and name not in critical:critical.append(name)
 active=set(critical+rank[:8]);assert set(r['active_net_names'])==active and r['critical_net_names']==critical and r['top_wire_net_names']==rank[:8];attempts=0;unchanged=0;penalty=rc.scale//10**11
 for name,answer in zip(r['selected_net_names'],raw):
  current=groups[name];oldwire=tree(name,current)[2];assert answer['old_wire']==oldwire;other=Counter(occ);other.subtract(owners[name]);order=sorted(current,key=lambda cid:(-rc.path(queries[cid]['source'],queries[cid]['sink'],[f['edge_ids'][s] for s in current[cid]]),cid));assert [q['connection_id'] for q in answer['records']]==order
  if name not in active:assert not answer['attempts'];unchanged+=1
  else:
   assert len(answer['attempts'])==len(order)
   for cid,attempt in zip(order,answer['attempts']):
    q=queries[cid];source=q['source'];sink=q['sink'];retained,parent,wire=tree(name,{c:p for c,p in current.items() if c!=cid});dist=dict(retained);pred={};heap=[(d,u) for u,d in retained.items()];heapq.heapify(heap)
    while heap:
     val,u=heapq.heappop(heap)
     if val!=dist[u]:continue
     if u==sink:break
     for s in range(f['row_offsets'][u],f['row_offsets'][u+1]):
      v=f['dest_ranks'][s]
      if other.get(v,0)>=f['capacities'][v] or v in retained:continue
      value=val+rc.increments[s]+penalty*span.get(v,0)
      if value<dist.get(v,value+1):dist[v]=value;pred[v]=s;heapq.heappush(heap,(value,v))
    assert sink in dist;suffix=[];u=sink
    while u not in retained:s=pred[u];suffix.append(s);u=slot_source[s]
    prefix=[]
    while u!=source:s=parent[u];prefix.append(s);u=slot_source[s]
    trial=list(reversed(prefix))+list(reversed(suffix));old_delay=rc.initial(source)+sum(rc.increments[s] for s in current[cid]);trial_delay=rc.initial(source)+sum(rc.increments[s] for s in trial);present=tree(name,current)[2];trial_records={**current,cid:trial};trialwire=tree(name,trial_records)[2];accepted=trial_delay<=old_delay and trialwire<=present and (trial_delay<old_delay or trialwire<present);assert attempt==dict(connection_id=cid,old_delay=old_delay,trial_delay=trial_delay,trial_wire=trialwire,accepted=accepted)
    if accepted:current[cid]=trial
    attempts+=1
  final,parent,newwire=tree(name,current);assert answer['new_wire']==newwire
  for record in answer['records']:assert record['slots']==current[record['connection_id']] and record['delay']==final[queries[record['connection_id']]['sink']]
  occ=other;owners[name]=set(final);occ.update(final.keys());assert all(v<=f['capacities'][n] for n,v in occ.items())
 assert attempts==r['attempted_connections'];bindings.update(r['bindings']);bindings[str(b/'exchange/output.jsonl')]=sha(b/'exchange/output.jsonl');bindings[str(b/'exchange/receipt.json')]=sha(b/'exchange/receipt.json');results.append(dict(index=index,active_nets=len(active),independent_attempts=attempts,unchanged_nets=unchanged,full_owner_capacity_valid=True));print(results[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items());(seq/'exchange_replay_verification.json').write_text(json.dumps(dict(rows=results,bindings=bindings,scope='Independent own-report/wire mask plus exact greedy Dijkstra/decision and full owner replay. Inactive NET paths never changed. Shares authentic electrical loader, not kernel implementation.'),indent=2)+'\n')
