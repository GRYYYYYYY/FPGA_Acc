"""Adversarial static topology cases against original exact count DP semantics."""
from pathlib import Path
from fractions import Fraction as F
import json
from pre_route_endpoints import sha
from exact_integer_global_timing_v1 import ExactGlobalTiming as Original
from exact_integer_global_timing_v2 import ExactGlobalTiming as Optimized
R=Path(__file__).resolve().parents[1];D=R/'experiments/static_timing_multiplicity_contract_v1_2026-10-08';D.mkdir(exist_ok=False)
cases=[
 ('serial_same_query',3,[2],[(0,1,0),(1,2,0)],{0:2}),
 ('parallel_same_query',3,[1,2],[(0,1,0),(0,2,0)],{0:1}),
 ('dead_repeat_excluded',5,[3],[(0,1,0),(1,4,0),(2,3,0)],{0:1}),
 ('mixed_repeated_and_single',4,[3],[(0,1,0),(1,2,1),(2,3,0)],{0:2,1:1}),
 ('no_sink_path',3,[2],[(0,1,0)],{0:0}),
]
rows=[]
for name,n,sinks,arcs,expected in cases:
 tg={'nodes':{str(i):'SINK' if i in sinks else 'OTHER' for i in range(n)},'edges':{str(i):dict(source=u,sink=v,disabled=False,max_delay_seconds='0') for i,(u,v,cid) in enumerate(arcs)}}
 allocation={'edge_connection_ids':{str(i):cid for i,(u,v,cid) in enumerate(arcs)}};mapping={'external_edges':{str(i):{'old_local_offset_seconds':'0'} for i in range(len(arcs))}};delays={cid:F('1/10') for cid in expected}
 original=Original(tg,mapping,allocation,10,F(1),delays);model=Optimized(tg,mapping,allocation,10,F(1),delays)
 assert model.multiplicities==expected
 for stage in ('initial','updated'):
  assert original.weights==model.weights and original.forward==model.forward and original.back==model.back and original.cpd==model.cpd
  for cid,k in expected.items():
   left=original.safe_upper(cid,F(1));right=model.safe_upper(cid,F(1));assert left==right and right[1]==k
  if stage=='initial':cid=next(iter(delays));original.update(cid,F('1/5'));model.update(cid,F('1/5'))
 rows.append(dict(case=name,multiplicities=model.multiplicities,repeated_query_ids=sorted(model.repeated_queries)))
# A cycle must be rejected, rather than treated as an antichain DAG.
tg={'nodes':{'0':'OTHER','1':'SINK'},'edges':{'0':dict(source=0,sink=1,disabled=False,max_delay_seconds='0'),'1':dict(source=1,sink=0,disabled=False,max_delay_seconds='0')}}
try:Optimized(tg,{'external_edges':{}},{'edge_connection_ids':{}},10,F(1),{})
except AssertionError:cycle_rejected=True
else:raise AssertionError('cycle unexpectedly accepted')
bindings={str(path):sha(path) for path in (Path(__file__),R/'tools/exact_integer_global_timing_v1.py',R/'tools/exact_integer_global_timing_v2.py')}
out=dict(bindings=bindings,all5_topology_cases_and_cycle_rejection_pass=True,rows=rows,cycle_rejected=cycle_rejected,scope='Synthetic topology contract only: repeated labels use exact fallback K, parallel/dead edges do not force K>1, updates leave static multiplicity valid, cycles rejected. Does not replace complete original XML/Fraction/STA or runtime evidence.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print('PASS5 topology boundary cases and cycle rejection',flush=True)
