"""Independent streaming replay; measured non-NET occupancy is not assumed zero."""
from collections import Counter,defaultdict
from native_overflow_transition_bounds_v1 import bounds

def replay(path,capacities,work):
 state={};owners={};total=Counter();external={};phase='start';iteration=0
 qseq=eseq=0;unused_q=None;pending=None;successful=0;stats=[];checkpoints=[]
 reasons=Counter();reason_nets=defaultdict(set);edges=Counter();residuals=Counter();incomplete=0
 transition_counts=Counter();transition_iterations=defaultdict(Counter);transition_witnesses=[]
 def tree(words):
  assert words[0]=='T' and len(words)>=6
  net,ignored,present,remaining,count=map(int,words[1:6]);nodes=tuple(map(int,words[6:]))
  assert net>=0 and ignored in [0,1] and present in [0,1] and remaining>=0 and count==len(nodes)
  assert nodes==tuple(sorted(nodes)) and (not nodes or 0<=nodes[0]<=nodes[-1]<len(capacities))
  assert (present and nodes) or (not present and not nodes and remaining==0)
  return net,(ignored,present,remaining,nodes)
 def assign(net,value):
  old=Counter(state[net][3]) if net in state else Counter();new=Counter(value[3])
  for node in old.keys()|new.keys():
   delta=new[node]-old[node]
   if not delta:continue
   group=owners.setdefault(node,{})
   count=group.get(net,0)+delta;assert count>=0
   if count:group[net]=count
   else:group.pop(net)
   total[node]+=delta;assert total[node]>=0
   if not total[node]:del total[node];assert not group;del owners[node]
  state[net]=value
 def observe(node,occ,cap,overused=False):
  assert 0<=node<len(capacities) and cap==capacities[node] and occ>=0
  if overused:assert occ>cap
  residue=occ-total.get(node,0);assert residue>=0,('native_occ_below_tree_counts',iteration,node,occ,total.get(node,0))
  if node in external:assert external[node]==residue,('external_changed_inside_boundary',iteration,node,external[node],residue)
  external[node]=residue;residuals['positive' if residue else 'zero']+=1
 def values(words):
  assert len(words)==4 and words[0]=='V'
  return tuple(map(int,words[1:]))
 with open(path) as stream:
  assert stream.readline()=='TRACE 1\n'
  def line():
   value=stream.readline();assert value,'truncated trace'
   words=value.split();assert words,'empty trace record'
   return words
  while True:
   w=line();kind=w[0]
   if kind=='CP':
    assert len(w)==3 and pending is None and unused_q is None
    tag=w[1];it=int(w[2]);incoming={};observed={};seen_values=False
    while True:
     z=line()
     if z==['CE']:break
     if z[0]=='T':
      assert not seen_values;net,value=tree(z);assert net not in incoming;incoming[net]=value
     else:
      seen_values=True;node,occ,cap=values(z);assert node not in observed;observed[node]=(occ,cap)
    assert incoming
    changed=[]
    if tag=='initial':
     assert phase=='start' and it==0 and not state
     for net,value in incoming.items():assign(net,value)
     phase='initial';external={}
    else:
     assert incoming.keys()==state.keys()
     changed=[net for net in incoming if incoming[net]!=state[net]]
     if tag=='iteration_begin':
      assert phase in ['initial','iteration_end'] and it==iteration+1 and not changed
      iteration=it;successful=0;phase='routing';external={}
     elif tag=='routed_before_local_opins':
      assert phase=='routing' and it==iteration and not changed;phase='routed'
     elif tag=='iteration_end_after_local_opins':
      assert phase=='stats' and it==iteration and not changed
      external={};phase='iteration_end'
      assert len(observed)==work[iteration-1]['overused_RR_nodes']
     elif tag=='final_after_best_restore':
      assert phase=='iteration_end' and it==iteration==len(work)
      for net in changed:assign(net,incoming[net])
      external={};phase='final'
     else:raise AssertionError(('unknown checkpoint',tag))
    for node,(occ,cap) in observed.items():observe(node,occ,cap,True)
    assert {n for n,c in total.items() if c>capacities[n]}<=observed.keys()
    checkpoints.append(dict(phase=tag,iteration=it,NETs=len(incoming),overused_RR_nodes=len(observed),boundary_changed_NETs=changed))
   elif kind=='Q':
    assert phase=='routing' and pending is None and unused_q is None and len(w)==8
    seq,it,net=map(int,w[1:4]);reason=w[4];node,occ,cap=map(int,w[5:])
    assert seq==qseq+1 and it==iteration and net in state and not state[net][0]
    value=state[net]
    if reason=='missing_tree':assert not value[1]
    elif reason=='remaining_sinks':assert value[1] and value[2]>0
    elif reason=='hold_force':assert value[1]
    elif reason in ['overuse','forced_connection']:
     assert value[1] and node in value[3];observe(node,occ,cap,reason=='overuse')
     if reason=='overuse':
      for other,count in owners.get(node,{}).items():
       if other!=net:edges[(other,net)]+=1
    else:raise AssertionError(('unknown native guard',reason))
    if reason not in ['overuse','forced_connection']:assert (node,occ,cap)==(-1,-1,-1)
    qseq=seq;unused_q=(seq,net);reasons[reason]+=1;reason_nets[reason].add(net)
   elif kind=='B':
    assert phase=='routing' and pending is None and len(w)==7
    event,it,net,preserve,hold,decision=map(int,w[1:])
    assert event==eseq+1 and it==iteration and preserve in [0,1] and hold in [0,1]
    assert unused_q==(decision,net)
    if preserve:assert iteration==1
    n,value=tree(line());assert n==net and value==state[net]
    observed={}
    while True:
     z=line()
     if z==['BE']:break
     node,occ,cap=values(z);assert node in value[3] and node not in observed
     observed[node]=(occ,cap);observe(node,occ,cap,True)
    assert {n for n in set(value[3]) if total.get(n,0)>capacities[n]}<=observed.keys()
    pending=(event,it,net);pending_nonoverused=set(value[3])-observed.keys();eseq=event;unused_q=None
   elif kind=='E':
    assert phase=='routing' and len(w)==4 and pending==tuple(map(int,w[1:]))
    net,value=tree(line());assert net==pending[2] and line()==['EE']
    old_counts=Counter(state[net][3]);new_counts=Counter(value[3]);lower=upper=0;facts=[]
    for node in old_counts.keys()|new_counts.keys():
     delta=new_counts[node]-old_counts[node]
     if not delta:continue
     lo,hi=bounds(total.get(node,0),delta,capacities[node],external.get(node),node in pending_nonoverused);lower+=lo;upper+=hi
     if len(transition_witnesses)<8:facts.append(dict(node=node,total_tree_occupancy=total.get(node,0),delta=delta,capacity=capacities[node],known_external=external.get(node),known_native_nonoverused=node in pending_nonoverused,lower=lo,upper=hi))
    assert lower<=upper
    category='definitely_positive' if lower>0 else 'definitely_negative' if upper<0 else 'exact_zero' if lower==upper==0 else 'nonpositive' if upper==0 else 'nonnegative' if lower==0 else 'sign_undetermined'
    transition_counts[category]+=1;transition_iterations[iteration][category]+=1
    if lower>0 and len(transition_witnesses)<8:transition_witnesses.append(dict(event=pending[0],iteration=iteration,NET=net,lower=lower,upper=upper,remaining=value[2],facts=facts))
    assign(net,value)
    if value[1] and value[2]==0:successful+=1
    else:incomplete+=1
    pending=None
   elif kind=='S':
    assert phase=='routed' and len(w)==6
    it,nets,conns,pushes,pops=map(int,w[1:]);assert it==iteration and pops<=pushes
    expected=work[it-1]
    assert (nets,conns,pushes)==(expected['rerouted_NET_operations'],expected['rerouted_connection_operations'],expected['heap_pushes'])
    assert nets==successful,('successful_NET_attempt_count',it,nets,successful)
    stats.append(dict(iteration=it,NET_operations=nets,connection_operations=conns,heap_pushes=pushes,heap_pops=pops));phase='stats'
   elif kind=='END':
    assert phase=='final' and pending is None and unused_q is None and len(w)==4
    assert tuple(map(int,w[1:]))==(1,qseq,eseq) and len(stats)==len(work)
    assert stream.read()==''
    break
   else:raise AssertionError(('unexpected record',kind))
 result=dict(decisions=qseq,setup_attempts=eseq,incomplete_attempts=incomplete,first_true_native_guards=dict(reasons),
             NETs_by_guard={k:sorted(v) for k,v in reason_nets.items()},iteration_stats=stats,checkpoints=checkpoints,
             co_owner_guard_witness_edges=[dict(owner=a,selected_NET=b,observations=count) for (a,b),count in sorted(edges.items())],
             measured_external_residual_observations=dict(residuals))
 result['native_NET_overflow_transition_bounds']=dict(counts=dict(transition_counts),by_iteration={str(k):dict(v) for k,v in transition_iterations.items()},first8_definite_positive_witnesses=transition_witnesses)
 return result,state
