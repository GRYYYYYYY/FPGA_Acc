"""NET targets from already grammar/physics-admitted TRACE1 streams.

Q labels first-true observed guards; successful E labels whole-NET operations.
No per-NET heap/connection work or counterfactual causality is inferred.
"""
from collections import Counter

def extract(path,NET_ids,expected_stats):
 known=set(NET_ids);first=set();over=Counter();operations=Counter();per_iteration=Counter();stats=[];initial=set();inside_initial=False;pending_q=None;pending_event=None;qseq=eseq=0;ended=False;incomplete=0
 with open(path) as f:
  assert f.readline()=='TRACE 1\n'
  for line in f:
   if line.startswith('CP '):
    words=line.split();inside_initial=words==['CP','initial','0'];continue
   if line.startswith('T ') and inside_initial:
    words=line.split(maxsplit=6);net,ignored=map(int,words[1:3])
    if net in known:assert not ignored and net not in initial;initial.add(net)
    continue
   if line.strip()=='CE' and inside_initial:assert initial==known;inside_initial=False;continue
   if line.startswith('Q '):
    w=line.split();assert len(w)==8 and pending_q is None and pending_event is None
    seq,it,net=map(int,w[1:4]);reason=w[4];assert seq==qseq+1 and net in known and it>=1 and reason in ['missing_tree','remaining_sinks','hold_force','overuse','forced_connection']
    qseq=seq;pending_q=(seq,it,net)
    if reason=='overuse':
     assert int(w[6])>int(w[7]);over[net]+=1
     if it==1:first.add(net)
   elif line.startswith('B '):
    w=line.split();assert len(w)==7 and pending_event is None
    event,it,net,preserve,hold,decision=map(int,w[1:]);assert event==eseq+1 and pending_q==(decision,it,net) and preserve in [0,1] and hold in [0,1]
    eseq=event;pending_event=(event,it,net);pending_q=None
   elif line.startswith('E '):
    w=line.split();assert len(w)==4 and pending_event==tuple(map(int,w[1:]));event,it,net=pending_event
    t=f.readline().split();assert len(t)>=6 and t[0]=='T';n,ignored,present,remaining,count=map(int,t[1:6]);assert n==net and ignored==0 and len(t)==6+count and f.readline()=='EE\n'
    if present and remaining==0:operations[net]+=1;per_iteration[it]+=1
    else:incomplete+=1
    pending_event=None
   elif line.startswith('S '):
    w=line.split();assert len(w)==6 and pending_event is None and pending_q is None;it,nets,conns,pushes,pops=map(int,w[1:]);assert nets==per_iteration[it]
    stats.append(dict(iteration=it,NET_operations=nets,connection_operations=conns,heap_pushes=pushes,heap_pops=pops))
   elif line.startswith('END '):
    assert list(map(int,line.split()[1:]))==[1,qseq,eseq] and pending_event is None and pending_q is None and f.read()=='';ended=True;break
 assert ended and initial==known and not incomplete and stats==expected_stats and qseq==eseq==sum(operations.values())
 rows={net:dict(first_iteration_overuse_guard=int(net in first),total_overuse_guard_decisions=over[net],total_successful_NET_route_operations=operations[net]) for net in NET_ids}
 return rows,dict(decisions=qseq,attempts=eseq,incomplete_attempts=incomplete,first_iteration_overuse_NETs=len(first),total_overuse_decisions=sum(over.values()),successful_NET_operations=sum(operations.values()),iteration_stats=stats)
