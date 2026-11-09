"""Adversarial integer boundaries and fallback; synthetic, not FPGA physical evidence."""
from array import array
from collections import Counter
from pathlib import Path
import json
from pre_route_endpoints import sha
from native_bounded_wire_search_v1 import NativeBoundedSearch,MAX
from csr_integer_budget_search_bounded_v1 import query
R=Path(__file__).resolve().parents[1];D=R/'experiments/native_bounded_integer_boundary_v1_2026-10-08';D.mkdir(exist_ok=False)
class ExactChain:
 def __init__(self,initial,increments):
  self.value=initial;self.increments=increments;n=len(increments)+1
  self.fields={k:array('Q',v) for k,v in dict(node_ids=list(range(n)),row_offsets=list(range(n))+[n-1],dest_ranks=list(range(1,n)),edge_ids=list(range(n-1)),switch_ids=[0]*(n-1),capacities=[1]*n).items()}
 def node(self,n):assert type(n) is int and 0<=n<len(self.fields['node_ids']);return 0,0
 def initial(self,n):self.node(n);return self.value if n==0 else 0
 def increment(self,i):return self.increments[i]
 def path(self,source,sink,edges):assert source==0 and sink==len(self.increments) and edges==list(range(sink));return self.value+sum(self.increments)
cases=[
 ('delay_at_u64_max',MAX-4,[4],{1:1},MAX,2,100,'FOUND',False),
 ('delay_addition_overflow_rejected',MAX-4,[5],{1:1},MAX,2,100,'NO_STRICT_IMPROVEMENT',False),
 ('objective_at_exclusive_bound',0,[0],{1:MAX},0,MAX,100,'NO_STRICT_IMPROVEMENT',False),
 ('objective_below_u64_max',0,[0],{1:MAX-1},0,MAX,100,'FOUND',False),
 ('objective_addition_overflow_rejected',0,[0,0],{1:MAX-1,2:3},0,MAX,100,'NO_STRICT_IMPROVEMENT',False),
 ('increment_above_u64_exact_fallback',0,[MAX+1],{1:1},MAX+1,2,100,'FOUND',True),
 ('initial_above_u64_exact_fallback',MAX+1,[0],{1:1},MAX+1,2,100,'FOUND',True),
 ('objective_above_u64_exact_fallback',0,[0],{1:MAX+1},0,MAX+2,100,'FOUND',True),
 ('label_limit_is_incomplete',0,[1],{1:1},1,2,1,'LABEL_LIMIT',False),
 ('zero_bound_no_search',0,[1],{1:1},1,0,100,'NO_STRICT_IMPROVEMENT',False),
]
rows=[];bindings={str(Path(__file__)):sha(Path(__file__)),str(R/'tools/native_bounded_wire_search_v1.py'):sha(R/'tools/native_bounded_wire_search_v1.py'),str(R/'tools/csr_integer_budget_search_bounded_v1.py'):sha(R/'tools/csr_integer_budget_search_bounded_v1.py')}
for name,initial,increments,length,budget,bound,limit,status,falls in cases:
 rc=ExactChain(initial,increments);native=NativeBoundedSearch(rc,length);bindings.update(native.bindings);sink=len(increments)
 actual=native.query(0,sink,budget,Counter(),set(),{},limit,bound)
 expected=query(rc,0,sink,budget,lambda u,i:True,lambda u,i:length.get(rc.fields['dest_ranks'][i],0),max_labels=limit,cost_limit_exclusive=bound)
 assert actual==expected and actual['status']==status and bool(native.fallback_calls)==falls
 if status=='FOUND':assert actual['delay']==initial+sum(increments) and actual['cost']==sum(length.values())
 rows.append(dict(case=name,result=actual,python_fallback_calls=native.fallback_calls,native_calls=native.native_calls));native.close()
assert all(sha(f)==h for f,h in bindings.items())
out=dict(bindings=bindings,all10_adversarial_boundary_and_fallback_cases_pass=True,rows=rows,scope='Synthetic exact arithmetic/API boundary evidence only: overflow rejection before addition, >64-bit Python fallback with no quantization, zero bound and incomplete LABEL_LIMIT semantics. Does not substitute original XML/physical/STA/full-cohort evidence.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS10 adversarial boundaries and exact fallback',flush=True)
