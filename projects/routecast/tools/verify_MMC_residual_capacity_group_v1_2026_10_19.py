"""Independent residual graph minima, complete trees and prefix occupancy."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET
from fractions import Fraction
from array import array
from collections import Counter,deque
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_residual_capacity_group_v1_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=json.loads((O/'protocol.json').read_text());result=json.loads((O/'results.json').read_text())
 for p,h in protocol['bindings'].items():assert sha(pathlib.Path(p))==h
 graph=next(pathlib.Path(p) for p in protocol['bindings'] if p.endswith('rr_graph.xml'));caps=array('I');kinds=[];us=array('I');vs=array('I');weights=array('Q');switches={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert e.get('type') in ['buffer','mux','tristate'] and Fraction(t.get('Cinternal','0'))==0;w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;switches[int(e.get('id'))]=int(w)
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));weights.append(switches[int(e.get('switch_id'))])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(us)==8097539 and len(caps)==904438;occupancy=Counter();verified=[];prefix=R/'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19';bindings={str(p):sha(p) for p in [O/'protocol.json',O/'results.json',graph,pathlib.Path(__file__).resolve()]}
 for row in result['rows']:
  net=row['net_id'];ip=O/f'net_{net}_input.json';x=json.loads(ip.read_text());original=json.loads((prefix/f'net_{net}_original.json').read_text());source=x['source'];sinks=x['sinks'];assert source==original['source'] and sinks==sorted(map(int,original['paths']));assert x['original_floors']==original['sink_floors'] and x['original_budgets']==original['sink_budgets'];blocked=set(x['prefix_saturated_nodes']);assert sorted(blocked)==sorted(v for v,n in occupancy.items() if n==caps[v]);bindings[str(ip)]=sha(ip)
  if row['status']!='DIAGNOSTIC_TREE_COMMITTED':
   # Exact reachability of the residual physical graph, independently of producer.
   offsets=array('Q',[0]);cursor=0
   for node in range(len(caps)):
    while cursor<len(us) and us[cursor]==node:cursor+=1
    offsets.append(cursor)
   seen=set() if source in blocked else {source};q=deque(seen)
   while q:
    a=q.popleft()
    if kinds[a]=='SINK':continue
    for eid in range(offsets[a],offsets[a+1]):
     b=vs[eid]
     if b not in blocked and caps[b]>0 and kinds[b]!='SOURCE' and b not in seen:seen.add(b);q.append(b)
   missing=sorted(set(sinks)-seen);assert missing;verified.append(dict(net_id=net,status='FIXED_PREFIX_UNREACHABILITY_INDEPENDENTLY_VERIFIED',unreachable_sinks=len(missing)));break
  pc=array('Q');ph=array('I');pcp=O/f'net_{net}_potential_cost.bin';php=O/f'net_{net}_potential_hops.bin';pc.frombytes(pcp.read_bytes());ph.frombytes(php.read_bytes());assert len(pc)==len(ph)==len(caps) and (pc[source],ph[source])==(0,0);checked=0
  for a,b,w in zip(us,vs,weights):
   if caps[a]>0 and caps[b]>0 and a not in blocked and b not in blocked and kinds[a]!='SINK' and kinds[b]!='SOURCE':assert (pc[b],ph[b])<=(pc[a]+w,ph[a]+1);checked+=1
  tp=O/f'net_{net}_tree.json';tree=json.loads(tp.read_text());assert tree['source']==source and set(map(int,tree['paths']))==set(sinks);nodes={source};parents={};total=0;violations=[]
  for sink,path in tree['paths'].items():
   sink=int(sink);current=source;seen={source};value=0;assert kinds[sink]=='SINK'
   for eid in path:
    assert type(eid) is int and 0<=eid<len(us);a,b,w=us[eid],vs[eid],weights[eid];assert a==current and b not in seen and b not in blocked and kinds[a]!='SINK' and kinds[b]!='SOURCE' and caps[b]>0
    if b in parents:assert parents[b]==(a,eid)
    parents[b]=(a,eid);seen.add(b);nodes.add(b);current=b;value+=w
   assert current==sink and [value,len(path)]==tree['sink_labels'][str(sink)]==[pc[sink],ph[sink]];floor=x['original_floors'][str(sink)];budget=x['original_budgets'][str(sink)];assert value>=floor;total+=value-floor
   if value>budget:violations.append(value-budget)
  assert nodes.isdisjoint(blocked) and sorted(nodes)==tree['unique_nodes'] and total==tree['excess']==row['sum_sink_RC_increase_units_1e18'];assert len(violations)==row['original_budget_violations'] and max(violations,default=0)==row['maximum_budget_excess_units_1e18'];occupancy.update(nodes);assert all(n<=caps[v] for v,n in occupancy.items())
  for p in [pcp,php,tp]:bindings[str(p)]=sha(p)
  verified.append(dict(net_id=net,status='TREE_PREFIX_CAPACITY_AND_GLOBAL_RESIDUAL_LEX_MINIMA_PASS',sinks=len(sinks),eligible_edge_inequalities=checked,original_budget_violations=len(violations)));print(verified[-1],flush=True)
 op=O/'final_unique_NET_occupancy.json';assert {str(v):n for v,n in occupancy.items()}==json.loads(op.read_text());bindings[str(op)]=sha(op)
 complete=len(verified)==5 and all(row['status']=='TREE_PREFIX_CAPACITY_AND_GLOBAL_RESIDUAL_LEX_MINIMA_PASS' for row in verified);assert result['all_five_committed']==complete
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='FIXED_PREFIX_PHYSICAL_CAPACITY_AND_RESIDUAL_SEARCH_INDEPENDENTLY_VERIFIED',all_five_capacity_legal=complete,rows=verified,bindings=bindings,scope='Fixed five-NET isolated prefix only; shortest minima conditioned on the fixed earlier tree choices. Original budgets audited separately, not relaxed as an acceptance gate. No full MMC route, global joint optimum, native STA or runtime gain.'),f,indent=2)
if __name__=='__main__':main()
