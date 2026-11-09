"""Instrumented hybrid output parity on consecutive mixed-branch queries."""
import json,random,sys
from pathlib import Path
from types import SimpleNamespace
from hybrid_bidirectional_search_stats_v2 import Search as Original
from hybrid_bidirectional_search_prepriced_stats_v3 import Search as Candidate
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from source_binding_v2 import closure
old=R/'experiments/soft_demand_workspace_radix_stats_build_v4_2026-10-08/search.so';new=R/'experiments/soft_demand_workspace_prepriced_stats_build_v5_2026-10-09/search.so';bidi=R/'experiments/bidirectional_rc_build_v2_2026-10-08/search.so';bindings={**closure([Path(__file__)]),**{str(p):sha(p) for p in [old,new,bidi]}};calls=0;branches={};missing=0
for seed in range(40):
 rng=random.Random(seed);n=rng.randrange(3,25);f=dict(capacities=[1]*n,row_offsets=[0],dest_ranks=[]);inc=[]
 for u in range(n):
  for v in range(n):
   if rng.random()<.12:f['dest_ranks'].append(v);inc.append(rng.choice([0,1,5,2**40]))
  f['row_offsets'].append(len(inc))
 rc=SimpleNamespace(increments=inc,initial=lambda node:node%9);a=Original(f,rc,old);b=Candidate(f,rc,new)
 for step in range(12):
  source=rng.randrange(n);targets=set(rng.sample(range(n),[0,1,min(3,n)][step%3]));prices={i:rng.randrange(8) for i in range(n)};weight=[0,1,13,2**63][step%4]
  a.prepare(prices,weight);b.prepare(prices,weight);x=a.search(source,targets);y=b.search(source,targets);assert x[2]==y[2],(seed,step);
  if len(targets)==1:assert x==y,(seed,step)
  else:
   for field in ['raw','pn','pe','settled']:assert list(getattr(a.forward,field))==list(getattr(b.forward,field)),(seed,step,field)
  assert a.metrics[-1]['counts']==b.metrics[-1]['counts'],(seed,step,'reported counts')
  m=b.metrics[-1];assert m['targets']==len(targets) and m['seconds']>=0;assert m['branch']==('singleton_bidirectional' if len(targets)==1 else 'multitarget_forward');branches[m['branch']]=branches.get(m['branch'],0)+1;missing+=int(not m['counts_available']);calls+=1
  if m['branch']=='multitarget_forward':assert m['counts']['settled']==sum(b.forward.settled)
 a.close();b.close()
assert calls==480 and set(branches)=={'singleton_bidirectional','multitarget_forward'} and missing>0
assert all(sha(p)==h for p,h in bindings.items());D=R/'experiments/hybrid_prepriced_stats_contract_v3_2026-10-09';D.mkdir(exist_ok=True);out=dict(bindings=bindings,mixed_queries=calls,graphs=40,branch_counts=branches,missing_unreachable_bidirectional_counts=missing,all_original_raw_parents_settled_outputs_equal=True,all_reported_operation_counts_equal=True,scope='Consecutive random-graph differential hybrid outputs, empty/single/multi targets, disconnected and zero-cost paths, wide weights. Counters available only as reported by kernel; unreachable bidi counts missing, never zero-filled. Timings instrumented, not full model parity, MMC profiling, native quality or speedup.')
(D/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({k:v for k,v in out.items() if k not in ['bindings','scope']},indent=2))
