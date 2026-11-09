"""Pure batch proposal policy, explicitly separate from legacy single-NET admission.

No ledger/epoch/context writes. Common costs release every group owner once per
NET; scratch routing reserves newly built group trees against fixed outsiders.
"""
from collections import Counter
from fractions import Fraction
from criticality_net_admission_v1 import validate
from criticality_objective_admission_v1 import score
from capacity_admissible_tree_v2 import CapacityMask,Graph
from criticality_retained_net_primary_v1 import route
class Snapshot:
 def __init__(self,fields,rc,slots,queries,old,ledger,criticalities,node_base,history,spans,weight):
  if not queries or set(queries)!=set(old) or any(type(n) is not int or n<0 for n in queries):raise ValueError('group member domain')
  self.fields=fields;self.rc=rc;self.slots=slots;self.queries=queries;self.old=old;self.caps=tuple(fields['capacities']);self.n=len(self.caps);self.base=tuple(node_base);self.history=dict(history);self.spans=dict(spans);self.weight=weight;self.ledger=dict(ledger);self.criticalities={cid:dict(q) for cid,q in criticalities.items()}
  if len(self.base)!=self.n or any(type(v) is not int or v<0 for v in self.base+self.caps) or type(weight) is not int or weight<0:raise ValueError('cost/capacity domain')
  for mapping in [self.history,self.spans,self.ledger]:
   if any(type(n) is not int or not 0<=n<self.n or type(v) is not int or v<0 for n,v in mapping.items()):raise ValueError('snapshot count domain')
  if any(v and not self.caps[n] for n,v in self.ledger.items()):raise ValueError('occupied zero capacity')
  self.audits={};self.oldcount=Counter();seen=set()
  for n in sorted(queries):
   if any(q['net_id']!=n or q['connection_id'] in seen for q in queries[n]):raise ValueError('member/CID mismatch')
   for q in queries[n]:
    cid=q['connection_id'];seen.add(cid);c=self.criticalities[cid]
    if (c['net'],c['source_rr'],c['target_rr'])!=(n,q['source'],q['sink']):raise ValueError('criticality identity')
    if not 0<=Fraction(c['criticality_numerator'],c['criticality_denominator'])<=1:raise ValueError('criticality range')
   audit=validate(fields,rc,slots,queries[n],old[n]);self.audits[n]=audit;self.oldcount.update(audit['owned'])
  if any(v>self.ledger.get(n,0) for n,v in self.oldcount.items()):raise ValueError('missing group owners')
  self.outside=Counter(self.ledger);self.outside.subtract(self.oldcount);self.outside={n:v for n,v in self.outside.items() if v};self.cache={}
 def get(self,node,default=0):
  if type(node) is not int or not 0<=node<self.n:raise ValueError('cost node domain')
  if node not in self.cache:self.cache[node]=self.base[node]*(1+self.history.get(node,0))*(1+max(0,self.outside.get(node,0)-self.caps[node]+1))+self.weight*self.spans.get(node,0)
  return self.cache[node]

def prepare(snapshot,candidate):
 s=snapshot
 if set(candidate)!=set(s.queries):raise ValueError('candidate group cardinality')
 audits={};newcount=Counter();before=Fraction(0);after=Fraction(0)
 for n in sorted(candidate):
  oldbyid={q['connection_id']:q for q in s.old[n]};audit=validate(s.fields,s.rc,s.slots,s.queries[n],candidate[n]);audits[n]=audit;newcount.update(audit['owned'])
  for rec in candidate[n]:
   old=oldbyid[rec['connection_id']]
   if {k:v for k,v in rec.items() if k!='answer'}!={k:v for k,v in old.items() if k!='answer'}:raise ValueError('frozen NET metadata changed')
  before+=score(s.fields,s.slots,s.old[n],s.criticalities,s,s.audits[n]['delays']);after+=score(s.fields,s.slots,candidate[n],s.criticalities,s,audit['delays'])
 updates={};delta=0
 for node in s.oldcount.keys()|newcount.keys():
  current=s.ledger.get(node,0);value=current-s.oldcount[node]+newcount[node]
  if value<0:raise ValueError('negative group occupancy')
  delta+=max(0,value-s.caps[node])-max(0,current-s.caps[node])
  if value!=current:updates[node]=value
 accepted=delta<=0 and after<=before
 return dict(accepted=accepted,status='ADMIT_GROUP_PROPOSAL' if accepted else 'RETAIN_GROUP_OBJECTIVE_INCREASE' if after>before else 'RETAIN_GROUP_OVERFLOW_INCREASE',old_score=before,candidate_score=after,objective_delta=after-before,prospective_overflow_delta=delta,updates=updates,old_owner_counts=dict(s.oldcount),new_owner_counts=dict(newcount),members=sorted(candidate),scope='Pure proposed batch criterion, no state commit or legacy singleNET equivalence claim.')

def propose(snapshot,original,max_labels=10000):
 s=snapshot
 if original.n!=s.n:raise ValueError('search graph domain')
 scratch=Counter(s.outside);candidate={};events=[]
 for n in sorted(s.queries):
  queries=s.queries[n];source=queries[0]['source'];scratch[source]+=1
  mask=CapacityMask(s.caps,scratch,{source});graph=Graph(original,mask,max_labels)
  answer=route(graph,queries,s.old[n],s.criticalities,s,s.fields['edge_ids'],scratch,s.caps,s.slots,min_fanout=len(queries)+1)
  events.append(dict(net_id=n,complete=answer['complete'],first_failed_connection_id=answer['first_failed_connection_id'],search_events=graph.events))
  if not answer['complete']:return None,dict(status='NO_COMPLETE_GROUP_PROPOSAL',events=events,failed_NET=n,partial_trees_discarded=True)
  oldbyid={q['connection_id']:q for q in s.old[n]};attempts={q['connection_id']:q['physical_edge_ids'] for q in answer['attempts']};recs=[]
  for q in queries:
   cid=q['connection_id'];path=attempts[cid];u=source;delay=s.rc.initial(source)
   for eid in path:
    edge=s.slots[eid];delay+=s.rc.increment(edge);u=s.fields['dest_ranks'][edge]
   recs.append(dict(oldbyid[cid],answer=dict(status='FOUND',physical_edge_ids=path,delay=delay)))
  audited=validate(s.fields,s.rc,s.slots,queries,recs);scratch.update(audited['owned']-{source});candidate[n]=recs
 plan=prepare(s,candidate)
 expected=Counter(s.outside);expected.update(plan['new_owner_counts']);assert dict(+scratch)==dict(+expected)
 return candidate,dict(status='COMPLETE_GROUP_PROPOSAL',events=events,plan=plan,policy='Group old trees unseeded; numeric NET order, original criticality pin order, fixed common cost, zero admissible bound, fixed label cap. Pure scratch only.')
