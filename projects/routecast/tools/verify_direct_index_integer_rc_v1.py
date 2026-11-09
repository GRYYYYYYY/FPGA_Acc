"""Independent original Fraction path evaluation and invalid-path behavior on 200 graphs."""
import random,json,sys
from fractions import Fraction
from pathlib import Path
R=Path.cwd();sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from csr_exact_buffered_rc import ExactBufferedRC
from class_cached_integer_rc_v1 import IntegerRC as Original
from direct_index_integer_rc_v1 import IntegerRC as Candidate
out=R/'experiments/direct_index_integer_rc_contract_v1_2026-10-08';out.mkdir();bindings=closure([Path(__file__)]);valid=invalid=0
for seed in range(200):
 rng=random.Random(seed);n=rng.randint(3,16);classes=[(Fraction(rng.randrange(8),10000),Fraction(rng.randrange(8),10**12)) for _ in range(5)];indices=[rng.randrange(5) for _ in range(n)];switches={i:(Fraction(rng.randrange(6),10000),Fraction(rng.randrange(6),10**11)) for i in range(3)};f={'node_ids':list(range(n)),'row_offsets':[0],'edge_ids':[],'dest_ranks':[],'switch_ids':[]};adj=[];eid=1000
 for u in range(n):
  entries=[]
  for v in range(n):
   if v==(u+1)%n or rng.random()<.25:
    for _ in range(1+(rng.random()<.15)):
     entries.append((v,eid));f['dest_ranks'].append(v);f['edge_ids'].append(eid);f['switch_ids'].append(rng.randrange(3));eid+=rng.randint(1,5)
  adj.append(entries);f['row_offsets'].append(len(f['edge_ids']))
 rc=ExactBufferedRC(f,indices,classes,switches);old=Original(rc);new=Candidate(rc);assert new.scale==old.scale and new.increments==old.increments
 def compare(source,sink,path):
  global valid,invalid
  results=[]
  for model in [old,new]:
   try:results.append(('OK',model.path(source,sink,path)))
   except ValueError:results.append(('INVALID',None))
  assert results[0]==results[1],(seed,source,sink,path,results)
  if results[0][0]=='OK':
   exact=rc.path(source,sink,path)*new.scale;assert exact.denominator==1 and exact.numerator==results[1][1];valid+=1
  else:invalid+=1
 for source in range(n):
  compare(source,source,[]);u=source;seen={u};path=[]
  for _ in range(n-1):
   options=[x for x in adj[u] if x[0] not in seen]
   if not options:break
   u,e=rng.choice(options);path.append(e);seen.add(u);compare(source,u,path)
  compare(source,(source+1)%n,[]);compare(source,source,[-1]);compare(source,source,[True]);compare(source,source,[eid+100]);other=(source+1)%n;compare(source,adj[other][0][0],[adj[other][0][1]])
  cycle=[];u=source
  for _ in range(n):v,e=next(x for x in adj[u] if x[0]==(u+1)%n);cycle.append(e);u=v
  compare(source,source,cycle)
assert valid>0 and invalid>0 and all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps({'bindings':bindings,'random_graphs':200,'valid_paths_exact_integer_and_Fraction_parity':valid,'invalid_paths_same_rejection':invalid,'scope':'Unique original physical edge IDs, parallel arcs, noncontiguous IDs, exact electrical classes and zero costs. Synthetic contract proof; real model parity required separately.'},indent=2)+'\n');print(valid,invalid)
