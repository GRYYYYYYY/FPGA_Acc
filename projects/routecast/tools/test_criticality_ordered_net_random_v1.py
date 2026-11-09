"""Ordered full-NET interface versus per-step exhaustive extension oracle."""
import json,random,copy
from fractions import Fraction
from pathlib import Path
from criticality_ordered_net_primary_v1 import route
from criticality_shared_tree_sparse_reference_v2 import Graph
from pre_route_endpoints import sha
rng=random.Random(121735);nets=0;pins_checked=0;failed=0
for trial in range(220):
 n=rng.randrange(4,8);off=[0];dst=[];inc=[];direct={}
 for u in range(n):
  for v in range(n):
   if u!=v and (u==0 or rng.random()<.3):
    if u==0:direct[v]=len(dst)
    dst.append(v);inc.append(rng.randrange(8))
  off.append(len(dst))
 initial=[2]+[0]*(n-1);graph=Graph(dict(row_offsets=off,dest_ranks=dst),inc,initial)
 targets=rng.sample(range(1,n),rng.randrange(2,n));targets.append(targets[0]);qs=[];old=[];criticalities={};sinkbudgets={s:2+inc[direct[s]]+rng.randrange(5) for s in targets}
 for cid,s in enumerate(targets):
  q=dict(connection_id=cid,net_id=trial,source=0,sink=s);qs.append(q);old.append(dict(q,budget_integer=sinkbudgets[s],answer=dict(physical_edge_ids=[direct[s]],delay=2+inc[direct[s]])))
  c=rng.choice([Fraction(0),Fraction(1),Fraction(1,3),Fraction(7,8)]);criticalities[cid]=dict(net=trial,source_rr=0,target_rr=s,local_sink_pin=cid+1,criticality_numerator=c.numerator,criticality_denominator=c.denominator)
 prices={u:rng.randrange(12) for u in range(n)};before=copy.deepcopy((qs,old,criticalities,prices));result=route(graph,qs,old,criticalities,prices,list(range(len(dst))))
 assert (qs,old,criticalities,prices)==before
 expectedorder=sorted(range(len(qs)),key=lambda cid:(-Fraction(criticalities[cid]['criticality_numerator'],criticalities[cid]['criticality_denominator']),cid+1,cid));assert result['order']==expectedorder
 arrival={0:2};parents={};attempt={a['connection_id']:a['physical_edge_ids'] for a in result['attempts']}
 for step,cid in enumerate(expectedorder):
  if step>=len(result['search_results']):assert attempt[cid] is None;continue
  q=qs[cid];r=result['search_results'][step];c=Fraction(criticalities[cid]['criticality_numerator'],criticalities[cid]['criticality_denominator']);options=[]
  def dfs(u,seen,raw,price):
   if u==q['sink']:options.append(c*raw+(1-c)*price);return
   for slot in range(off[u],off[u+1]):
    v=dst[slot]
    if v not in seen and v not in arrival:dfs(v,seen|{v},raw+inc[slot],price+prices[v])
  for u,raw in arrival.items():dfs(u,{u},raw,0)
  assert options and Fraction(r['objective_numerator'],r['objective_denominator'])==min(options)
  path=attempt[cid];u=0;raw=2;newprice=0;pathparents={};seen={0}
  for slot in path:
   assert off[u]<=slot<off[u+1];v=dst[slot];assert v not in seen;seen.add(v);raw+=inc[slot]
   if v not in arrival:newprice+=prices[v]
   pathparents[v]=(u,slot);u=v
  assert u==q['sink'] and raw==r['raw'] and c*raw+(1-c)*newprice==min(options);pins_checked+=1
  assert r['committed']==(raw<=old[cid]['budget_integer'])
  if r['committed']:
   u=0;raw=2
   for slot in path:
    v=dst[slot];raw+=inc[slot];assert v not in parents or parents[v]==(u,slot);parents[v]=(u,slot);arrival[v]=raw;u=v
  else:
   assert result['first_failed_connection_id']==cid and step==len(result['search_results'])-1;failed+=1
 assert result['complete']==(result['first_failed_connection_id'] is None);nets+=1
out=Path('experiments/criticality_ordered_net_random_contract_v1_2026-10-10');out.mkdir()
files=[Path(__file__).resolve()]+[Path('tools')/x for x in ['criticality_ordered_net_primary_v1.py','criticality_shared_tree_sparse_reference_v2.py']]
(out/'verification.json').write_text(json.dumps(dict(bindings={str(p.resolve()):sha(p) for p in files},nets=nets,pins_checked=pins_checked,nets_stopped_on_budget=failed,independent_perstep_exhaustive_objective_raw_paths_order_and_stopping_pass=True,scope='Small random directed graphs; no full MMC primary or native performance claim.'),indent=2)+'\n');print('ORDERED NET RANDOM CONTRACT PASS',nets,pins_checked,failed)
