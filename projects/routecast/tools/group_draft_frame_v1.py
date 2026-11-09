"""Pure round-frame materialization; no file writes or external atomic commit.

Requires an already admitted complete round frame and immutable graph provider.
The fixed criticality vector belongs to the supplied detached group snapshot.
"""
from copy import deepcopy
from group_vacancy_proposal_v2 import prepare

def integer_map(mapping,label):
 result={}
 for key,value in mapping.items():
  if type(key) is int:node=key
  elif type(key) is str and key.isdecimal() and str(int(key))==key:node=int(key)
  else:raise ValueError(label+' key domain')
  if node<0 or node in result or type(value) is not int or value<0:raise ValueError(label+' count/domain alias')
  result[node]=value
 return result

def materialize(snapshot,candidate,state,expected_epochs):
 s=snapshot
 if set(state)!={'records','ledger','epochs','prices'}:raise ValueError('unsupported complete round-frame schema')
 ledger=integer_map(state['ledger'],'ledger');epochs=integer_map(state['epochs'],'epochs');prices=integer_map(state['prices'],'prices');expected=integer_map(expected_epochs,'expected epochs')
 if set(expected)!=set(s.queries):raise ValueError('expected member domain')
 byid={};groups={}
 for rec in state['records']:
  cid=rec['connection_id'];net=rec['net_id']
  if type(cid) is not int or cid<0 or cid in byid or type(net) is not int or net<0:raise ValueError('complete CID/NET domain')
  byid[cid]=rec;groups.setdefault(net,[]).append(rec)
 if set(groups)!=set(epochs):raise ValueError('complete NET epoch coverage')
 if any(epochs.get(n)!=value for n,value in expected.items()):return None,dict(status='RETAIN_STALE_MEMBER_EPOCH')
 if ledger!=s.ledger:return None,dict(status='RETAIN_STALE_LEDGER')
 expected_prices={n:s.history.get(n,0)+s.spans.get(n,0) for n in s.history.keys()|s.spans.keys()}
 if prices!=expected_prices:return None,dict(status='RETAIN_STALE_HISTORY')
 for n in s.queries:
  if {q['connection_id']:q for q in groups.get(n,[])}!={q['connection_id']:q for q in s.old[n]}:return None,dict(status='RETAIN_STALE_MEMBER_RECORDS')
 if candidate is None:return None,dict(status='RETAIN_NO_COMPLETE_GROUP_PROPOSAL')
 # Never trust a caller-supplied acceptance flag or a search receipt as admission.
 plan=prepare(s,candidate)
 if not plan['accepted']:return None,dict(status=plan['status'],plan=plan)
 replacements={q['connection_id']:q for recs in candidate.values() for q in recs}
 expected_cids={q['connection_id'] for recs in s.queries.values() for q in recs}
 if set(replacements)!=expected_cids:raise ValueError('replacement CID domain')
 draft=deepcopy(state);draft['records']=[deepcopy(replacements.get(q['connection_id'],q)) for q in state['records']];newledger=dict(ledger)
 for node,count in plan['updates'].items():
  if count:newledger[node]=count
  else:newledger.pop(node,None)
 for n in s.queries:epochs[n]+=1
 draft['ledger']={str(n):v for n,v in newledger.items()};draft['epochs']={str(n):v for n,v in epochs.items()}
 if len(draft['records'])!=len(state['records']) or {q['connection_id'] for q in draft['records']}!=set(byid):raise RuntimeError('complete frame coverage drift')
 return draft,dict(status='GROUP_DRAFT_MATERIALIZED',members=sorted(s.queries),expected_epochs=expected,result_epochs={n:epochs[n] for n in s.queries},plan=plan,scope='New detached draft object only. Outside records/prices preserved; graph/criticality epoch provider and admitted source frame are caller preconditions. No external concurrent atomicity claim.')
