"""Independent geometry-greedy Python tree versus compiled candidate and fallbacks."""
import copy,json,random,sys
from fractions import Fraction
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from compiled_criticality_tree_v1 import Graph,BINARY
from criticality_shared_tree_sparse_reference_v3 import Graph as Reference
from retained_criticality_tree_seed_v1 import seed
from retained_tree_frontier_state_v3 import GraphContext
from borrowed_compiled_frontier_v1 import Probe
from native_retained_frontier_order_v1 import initialize,SelectionError
from native_retained_net_initializer_v1 import initialize as baseline

def main():
 out=R/'experiments/frontier_order_core_v1_2026-10-18';out.mkdir(exist_ok=False);rng=random.Random(20261018);calls=changed_orders=undefined=0
 for trial in range(200):
  n=14;edges={}
  for v in range(1,10):edges[0,v]=rng.randrange(1,25)
  for u in range(1,10):
   for v in range(u+1,14):
    if v>=10 or rng.random()<.25:edges[u,v]=rng.randrange(1,25)
  edges[1,2]=rng.randrange(1,25);offset=[0];dest=[];inc=[];slots={}
  for u in range(n):
   for (a,b),w in sorted(edges.items()):
    if a==u:slots[a,b]=len(dest);dest.append(b);inc.append(w)
   offset.append(len(dest))
  f=dict(row_offsets=offset,dest_ranks=dest,edge_ids=list(range(len(dest))),capacities=[1]*n);initial=[rng.randrange(5)]*n;g=Graph(f,inc,initial);ref=Reference(f,inc,initial);kinds=['SOURCE']+['CHANX' if i%2 else 'CHANY' for i in range(1,10)]+['SINK']*4;geo={}
  for i,kind in enumerate(kinds):
   x,y=rng.randrange(12),rng.randrange(12);geo[i]=(kind,x,x+(rng.randrange(3) if kind=='CHANX' else 0),y,y+(rng.randrange(3) if kind=='CHANY' else 0),1 if i==11 and trial%3==0 else 0)
  probe=Probe(g,GraphContext('g',geo,lambda a,b:(a,b) in edges));oldpath=[slots[0,1],slots[1,2],slots[2,10]];raw=initial[0]+sum(inc[s] for s in oldpath);old=[dict(connection_id=c,net_id=0,source=0,sink=10,answer=dict(status='FOUND',physical_edge_ids=oldpath.copy(),delay=raw)) for c in range(4)];q=[dict(connection_id=c,net_id=0,source=0,sink=10+c) for c in range(4)];budget={c:100000 for c in range(4)};saved=copy.deepcopy(old);events=[];fallback=lambda:(_ for _ in ()).throw(AssertionError('unexpected fallback'));actual=initialize(g,f,kinds,q,old,budget,range(len(dest)),fallback,frontier_probe=probe,emit=lambda e:events.append(dict(e)));rt=ref.tree(0);seed(rt,[(10,oldpath,100000)]);expected={0:old[0]['answer']};remaining={1,2,3};order=[];event=0
  while remaining:
   gaps={}
   for cid in remaining:
    b=geo[10+cid];dist=[]
    for node in rt.arrival:
     a=geo[node]
     if a[0] not in ['SOURCE','OPIN','CHANX','CHANY'] or a[5]!=b[5]:continue
     dx=max(0,max(a[1],b[1])-min(a[2],b[2]));dy=max(0,max(a[3],b[3])-min(a[4],b[4]));dist.append(dx+dy)
    gaps[cid]=min(dist) if dist else None
   undefined+=sum(v is None for v in gaps.values());cid=min(remaining,key=lambda c:(gaps[c] is None,gaps[c] if gaps[c] is not None else 0,c));remaining.remove(cid);order.append(cid);select=events[event];assert select['phase']=='select' and select['connection_id']==cid and dict(select['candidates'])==gaps and select['tree_nodes']==len(rt.arrival);result=rt.expand(10+cid,Fraction(1),{},100000);assert result['committed'];after=events[event+1];assert after['phase']=='expanded' and after['committed'] and tuple(after['path_edge_ids'])==result['path_slots'] and after['raw']==result['raw'];expected[cid]=dict(status='FOUND',physical_edge_ids=list(result['path_slots']),delay=result['raw']);event+=2;calls+=1
  assert actual['answers']==expected and not actual['whole_NET_fallback'] and actual['retained_connection_ids']==[0] and set(actual['owner_nodes'])==set(rt.arrival) and old==saved and event==len(events);changed_orders+=order!=[1,2,3];g.close()
 assert calls==600 and changed_orders>0 and undefined>0
 # Single unresolved sink: unchanged whole-NET raw fallback and failure law.
 f=dict(row_offsets=[0,3,4,6,6,6,6],dest_ranks=[1,2,3,2,4,5],edge_ids=list(range(6)),capacities=[1]*6);g=Graph(f,[1,100,1,1,1,1],[0]*6);kinds=['SOURCE','CHANX','CHANX','SINK','SINK','SINK'];geo={i:(k,i,i,0,0,0) for i,k in enumerate(kinds)};probe=Probe(g,GraphContext('g',geo,lambda a,b:True));q=[dict(connection_id=0,net_id=0,source=0,sink=4),dict(connection_id=1,net_id=0,source=0,sink=5)];old=[dict(connection_id=0,net_id=0,source=0,sink=4,answer=dict(status='FOUND',physical_edge_ids=[1,4],delay=101)),dict(connection_id=1,net_id=0,source=0,sink=3,answer=dict(status='FOUND',physical_edge_ids=[2],delay=1))];fallback={0:dict(status='FOUND',physical_edge_ids=[0,3,4],delay=3),1:dict(status='FOUND',physical_edge_ids=[0,3,5],delay=3)};a=baseline(g,f,kinds,q,old,{0:101,1:4},range(6),lambda:fallback);b=initialize(g,f,kinds,q,old,{0:101,1:4},range(6),lambda:fallback,frontier_probe=probe);assert a==b and b['whole_NET_fallback'] and b['fallback_reason']=='RETAIN_RAW_BUDGET'
 count=[]
 class Broken:
  def capture(self,*args):raise ValueError('bad geometry binding')
 try:initialize(g,f,kinds,q,old,{0:101,1:4},range(6),lambda:count.append(1),frontier_probe=Broken())
 except SelectionError:pass
 else:raise AssertionError('selector error became fallback')
 assert not count;g.close();bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/native_retained_frontier_order_v1.py',R/'tools/native_retained_net_initializer_v1.py',R/'tools/borrowed_compiled_frontier_v1.py',R/'tools/criticality_shared_tree_sparse_reference_v3.py',R/'tools/retained_criticality_tree_seed_v1.py',BINARY]};spec=E=R/'experiments/mmc_frontier_order_candidate_protocol_v1_2026-10-18/protocol.json';bindings[str(spec)]=sha(spec)
 with (out/'verification.json').open('x') as f:json.dump(dict(status='fixed_frontier_order_independent_geometry_python_reference_and_fallback_core_pass',bindings=bindings,random_graphs=200,reference_repair_calls=calls,NETs_with_non_CID_order=changed_orders,undefined_gaps_preserved=undefined,whole_NET_budget_fallback_equal_to_baseline=True,selector_binding_errors_do_not_invoke_routing_fallback=True,scope='Development model ordering candidate only; no real-layout quality, native utility or full-flow gain established.'),f,indent=2)
 print('FRONTIER ORDER CORE PASS',calls,changed_orders,undefined,flush=True)
if __name__=='__main__':main()
