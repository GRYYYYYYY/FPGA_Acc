"""Random complete DAG trees and independent full occupancy rebuilding."""
import random,json,copy
from collections import Counter
from pathlib import Path
from criticality_net_admission_v1 import prepare
from pre_route_endpoints import sha
rng=random.Random(973153);admitted=rejected=0
for trial in range(400):
 n=rng.randrange(4,12);off=[0];dst=[];edges=[];weights=[];slotbyuv={}
 for u in range(n):
  for v in range(u+1,n):slotbyuv[u,v]=len(dst);dst.append(v);edges.append(len(edges)+100);weights.append(rng.randrange(6))
  off.append(len(dst))
 f=dict(row_offsets=off,dest_ranks=dst,edge_ids=edges,capacities=[rng.randrange(1,4) for _ in range(n)]);slots={e:i for i,e in enumerate(edges)}
 class RC:
  def initial(self,u):return 2
  def increment(self,s):return weights[s]
 def paths(parents,targets):
  result={}
  for sink in targets:
   u=sink;path=[]
   while u:
    a=parents[u];path.append(edges[slotbyuv[a,u]]);u=a
   result[sink]=list(reversed(path))
  return result
 targets=rng.sample(range(1,n),rng.randrange(2,n));a=paths({u:rng.randrange(u) for u in range(1,n)},targets);b=paths({u:rng.randrange(u) for u in range(1,n)},targets)
 qs=[dict(connection_id=i,net_id=trial,source=0,sink=s) for i,s in enumerate(targets)];old=[];new=[]
 for q in qs:
  raw=lambda path:2+sum(weights[slots[e]] for e in path)
  budget=max(raw(a[q['sink']]),raw(b[q['sink']]))+2
  old.append(dict(q,budget_integer=budget,answer=dict(status='FOUND',physical_edge_ids=a[q['sink']],delay=raw(a[q['sink']]))));new.append(dict(q,budget_integer=budget,answer=dict(status='FOUND',physical_edge_ids=b[q['sink']],delay=raw(b[q['sink']]))))
 def owned(records):return {0}|{dst[slots[e]] for r in records for e in r['answer']['physical_edge_ids']}
 other=[set(rng.sample(range(n),rng.randrange(1,n+1))) for _ in range(5)]
 ledger=Counter(u for o in [owned(old),*other] for u in o);expected=Counter(u for o in [owned(new),*other] for u in o)
 before=copy.deepcopy((old,new,ledger));r=prepare(f,RC(),slots,qs,old,new,ledger);assert (old,new,ledger)==before
 overflow=lambda counts:sum(max(0,counts.get(u,0)-f['capacities'][u]) for u in range(n));delta=overflow(expected)-overflow(ledger)
 assert r['prospective_overflow_delta']==delta
 if delta>0:rejected+=1;assert not r['updates']
 else:
  admitted+=1;actual=ledger.copy()
  for u,v in r['updates'].items():
   if v:actual[u]=v
   else:actual.pop(u,None)
  assert actual==expected
 bad=copy.deepcopy(new);bad[0]['answer']['delay']+=1
 try:prepare(f,RC(),slots,qs,old,bad,ledger)
 except ValueError:pass
 else:raise AssertionError('invalid reported raw admitted')
 assert ledger==before[2]
out=Path('experiments/criticality_net_admission_random_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/x for x in ['criticality_net_admission_v1.py','criticality_net_occupancy_gate_v1.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},random_DAG_tree_pairs=400,admitted=admitted,overflow_rejected=rejected,independent_full_owner_rebuild_and_raw_rejection_pass=True,scope='Valid random DAG tree pairs plus bad raw reports; full real feedback/XML validation remain open.'),indent=2)+'\n');print('RANDOM FULL NET ADMISSION PASS',400,admitted,rejected)
