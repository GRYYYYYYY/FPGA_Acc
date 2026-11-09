"""Independent original XML tree/RC audits and all32 isolated assignments."""
import pathlib,json,hashlib,xml.etree.ElementTree as ET,itertools
from fractions import Fraction
from array import array
from collections import defaultdict
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_complete_tree_bank_csr_v2_2026-10-19'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 protocol=json.loads((O/'protocol.json').read_text());result=json.loads((O/'results.json').read_text());cache={}
 def bound(p,h):
  p=pathlib.Path(p)
  if str(p) not in cache:cache[str(p)]=sha(p)
  assert cache[str(p)]==h
 for p,h in protocol['bindings'].items():
  bound(p,h)
  if p.endswith('independent_verification_v1.json'):
   for q,g in json.loads(pathlib.Path(p).read_text())['bindings'].items():bound(q,g)
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
 assert len(us)==8097539 and len(caps)==904438;banks={};rows=[];bindings={str(p):sha(p) for p in [O/'protocol.json',O/'results.json',graph,pathlib.Path(__file__).resolve()]}
 oldcert=json.loads((R/'experiments/mmc_NET_support_capacity_v1_2026-10-19/results.json').read_text())['cases'][0]['certificate'];old={a['net_id']:a for a in oldcert['owners']}
 for net in protocol['NETs']:
  banks[net]=[]
  root=R/('experiments/mmc_conflict_node_detour_v1_2026-10-19' if net in old else 'experiments/mmc_conflict_group_remaining_detours_v1_2026-10-19');floor=json.loads((root/f'net_{net}_original_sink_labels.json').read_text());budget=json.loads((root/f'net_{net}_blocked_sink_labels.json').read_text())
  for mode in ['original','blocked']:
   path=O/f'net_{net}_{mode}.json';x=json.loads(path.read_text());source=x['source'];expectedsource=old[net]['source'] if net in old else json.loads((root/f'net_{net}_{mode}_support.json').read_text())['source'];assert source==expectedsource and kinds[source]=='SOURCE'
   assert set(x['paths'])==set(floor)==set(budget);nodes={source};edges=set();parents={};total=0
   for sink,route in x['paths'].items():
    sink=int(sink);assert kinds[sink]=='SINK';current=source;seen={source};cost=0
    for eid in route:
     assert type(eid) is int and 0<=eid<len(us);a,b,w=us[eid],vs[eid],weights[eid];assert a==current and b not in seen and kinds[a]!='SINK' and kinds[b]!='SOURCE' and caps[b]>0
     if b in parents:assert parents[b]==(a,eid)
     parents[b]=(a,eid);seen.add(b);nodes.add(b);edges.add(eid);cost+=w;current=b
    assert current==sink and floor[str(sink)][0]<=cost<=budget[str(sink)][0];assert cost==x['sink_costs'][str(sink)]
    assert x['sink_floors'][str(sink)]==floor[str(sink)][0] and x['sink_budgets'][str(sink)]==budget[str(sink)][0]
    expected=(floor if mode=='original' else budget)[str(sink)][0]
    assert cost==expected;total+=cost-floor[str(sink)][0]
   assert sorted(nodes)==x['unique_nodes'] and sorted(edges)==x['unique_edges'] and total==x['excess']
   if mode=='blocked':assert 646275 not in nodes
   banks[net].append((nodes,total));rows.append(dict(net_id=net,mode=mode,sinks=len(x['paths']),unique_nodes=len(nodes),excess=total));bindings[str(path)]=sha(path)
 nets=protocol['NETs'];feasible=[]
 for mask in itertools.product([0,1],repeat=5):
  consumers=defaultdict(set);cost=0
  for net,ci in zip(nets,mask):
   nodes,excess=banks[net][ci];cost+=excess
   for node in nodes:consumers[node].add(net)
  if all(len(owners)<=caps[node] for node,owners in consumers.items()):feasible.append((cost,mask))
 native=result['isolated_five_NET_selection'];expected='OPTIMAL_WITHIN_CANDIDATES' if feasible else 'INFEASIBLE_WITHIN_CANDIDATES';assert native['status']==expected and native['excess']==(min(a for a,_ in feasible) if feasible else None)
 with (O/'independent_XML_verification_v1.json').open('x') as f:json.dump(dict(status='ALL10_COMPLETE_TREES_XML_RC_UNIQUE_NET_OCCUPANCY_AND_ALL32_CHOICES_PASS',rows=rows,feasible_isolated_assignments=len(feasible),solver_status=expected,bindings=bindings,scope='Ten deterministic complete candidates for fixed five known MMC NETs, isolated zero external occupancy only. No full MMC route, quality, runtime or generalization gain.'),f,indent=2)
 print('PASS',expected,'feasible isolated assignments',len(feasible),flush=True)
if __name__=='__main__':main()
