"""Synthetic callback controls, not physical routing evidence."""
from bounded_conflict_branch_core import bounded_conflict_branches
calls=[]
def allocate(r):return (0,r)
def attempt(r,s):
 assert r==s;calls.append(r)
 complete=2 in r
 return dict(failure=None if complete else {'status':'UNREACHABLE'},completed_connections=int(complete),required_connections=1)
def observe(c,r,s):return dict(status='OBSERVED_CONFLICT',query={'net_id':1},blockers=[dict(node=7,owners=[2])])
r=bounded_conflict_branches({},attempt,observe,allocate)
assert r['status']=='COMPLETE_CANDIDATE' and len(calls)==3 and r['trace'][2]['parent']==0
calls.clear();r=bounded_conflict_branches({},attempt,observe,allocate,max_attempts=1)
assert r['status']=='ATTEMPT_LIMIT' and len(calls)==1
r=bounded_conflict_branches({},attempt,observe,lambda r:None)
assert r['status']=='INITIAL_ALLOCATION_REJECTED' and r['trace']==[]
r=bounded_conflict_branches({},lambda r,s:dict(failure={},completed_connections=0,required_connections=1),lambda c,r,s:dict(status='UNSUPPORTED_FAILURE'),allocate)
assert r['status']=='FRONTIER_EXHAUSTED' and len(r['trace'])==1
print('branch controls passed: sibling selection, attempt bound, initial reject, exhausted frontier')

r=bounded_conflict_branches({},lambda r,s:dict(failure={},completed_connections=0,required_connections=1),observe,allocate,max_attempts=10)
assert r['status']=='FRONTIER_EXHAUSTED' and len(r['trace'])==4
assert any(o['status']=='DUPLICATE' for t in r['trace'] for o in t.get('options',[]))
r=bounded_conflict_branches({},attempt,observe,allocate,max_frontier=1)
assert r['dropped_frontier']>0 and len(r['trace'])<=4
for kwargs in [dict(max_attempts=0),dict(max_frontier=0),dict(max_attempts=True)]:
 try:bounded_conflict_branches({},attempt,observe,allocate,**kwargs)
 except ValueError:pass
 else:raise AssertionError('invalid bound accepted')
print('deduplication/frontier cap/invalid bound controls passed')
r=bounded_conflict_branches({},attempt,observe,allocate)
for t in r['trace']:
 selected=t['queue_before'][0]
 assert selected['order']==t['queue_order'] and selected['depth']==t['depth'] and selected['restrictions']==t['restrictions']
 if t['parent'] is not None:
  parent=r['trace'][t['parent']];assert t['parent']<t['iteration'] and t['depth']==parent['depth']+1
  assert all(set(v)<=set(t['restrictions'][k]) for k,v in parent['restrictions'].items())
assert r['trace'][1]['restrictions']!=r['trace'][2]['restrictions'] and r['trace'][2]['parent']==0
print('parent causality and archived queue choice controls passed')
