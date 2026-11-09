"""Full compiled messages versus qualified Python, overflow/domain atomicity."""
import json,random,ctypes as C
from array import array
from pathlib import Path
from compiled_endpoint_full_v1 import Graph,BINARY,MAX
from endpoint_graph_signals_v1 import extract
from exact_factor_elimination_v1 import sha
R=Path(__file__).resolve().parents[1]
def main():
 rng=random.Random(20261020);cells=0
 for trial in range(400):
  ids=[5+13*i for i in range(rng.randrange(1,13))];edges=[(rng.choice(ids),rng.choice(ids)) for _ in range(rng.randrange(40))];queries=[];nets={};cid=0
  for net in range(rng.randrange(6)):
   source=rng.choice(ids);count=rng.randrange(1,7);nets[net]={'source_RR':source,'fanout':count,'endpoint_bbox':[0,0,rng.randrange(9),rng.randrange(9)]}
   for _ in range(count):queries.append({'net_id':net,'connection_id':cid,'source':source,'sink':rng.choice(ids)});cid+=1
  g=Graph(ids,edges);actual=g.unpack(g.rebuild(queries,nets));expected=extract(ids,edges,queries,nets);assert actual==expected;cells+=15*len(ids)
 g=Graph([0],[(0,0)]);v=g.propagate(array('Q',[MAX,0,0,0,0]));assert v[0]==v[5]==v[8]==MAX
 invalid=0
 for call in [lambda:Graph([1,1],[]),lambda:Graph([1],[(1,2)]),lambda:g.propagate(array('Q',[0])),lambda:g.rebuild([{'net_id':0,'connection_id':1,'source':0,'sink':0}],{0:{'source_RR':0,'fanout':1,'endpoint_bbox':[0,0,MAX,0]}})]:
  try:call()
  except ValueError:invalid+=1
  else:raise AssertionError('invalid compiled layout accepted')
 for edges,source in [([(0,0),(0,0)],0), ([(0,0)],1)]:
  q=Graph([0],edges);base=(C.c_uint64*5)(MAX,0,0,0,0);output=(C.c_uint64*15)(*([73]*15))
  if source:q.sources[0]=1
  rc=q.lib.rc_endpoint_full(1,len(edges),q.a,q.b,base,output);assert rc!=0 and list(output)==[73]*15;invalid+=1
 D=R/'experiments/compiled_endpoint_full_contract_v1_2026-10-20';D.mkdir(exist_ok=False);files=[Path(__file__),R/'tools/compiled_endpoint_full_v1.py',R/'tools/soft_demand_cpp/endpoint_full_v1.cpp',BINARY,R/'build/endpoint_full_v1_2026-10-20/receipt.json'];(D/'verification.json').write_text(json.dumps({'status':'ALL400_COMPILED_FULL_REFERENCES_AND6_INVALID_ATOMIC_CASES_PASS','graphs':400,'integer_cells':cells,'invalid_rejections':invalid,'bindings':{str(p):sha(p) for p in files},'scope':'Checked uint64 domain only; overflow rejected without writing output. Parallel arcs/selfloops/sparse IDs/zero NETs supported. No performance or quality claim.'},indent=2)+'\n');print('COMPILED_FULL_CONTRACT_PASS',cells,invalid)
if __name__=='__main__':main()
