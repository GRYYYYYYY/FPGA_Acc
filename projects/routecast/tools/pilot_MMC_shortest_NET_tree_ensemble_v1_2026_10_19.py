"""One input-selected real NET; exact XML costs, no target route labels."""
import pathlib,json,hashlib,sys,resource,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import defaultdict,Counter
from shortest_NET_tree_ensemble_v1 import prepare,sample
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def write(p,j):
 with p.open('x') as f:json.dump(j,f,indent=2);f.write('\n')
def main():
 resource.setrlimit(resource.RLIMIT_AS,(32*2**30,32*2**30))
 epfile=R/'experiments/mmc_prospective_swap_predictor_inputs_v2_2026-10-19/episode_01/demand/endpoints.json';meta=json.loads(epfile.read_text());groups=defaultdict(list)
 for q in meta['connections']:groups[q['net_id']].append(q)
 net=min(n for n,qs in groups.items() if len({q['sink'] for q in qs})>=2);qs=groups[net];sources={q['source'] for q in qs};assert len(sources)==1;source=sources.pop();sinks=sorted({q['sink'] for q in qs});graph=pathlib.Path(meta['inputs']['graph']['path']);assert sha(graph)==meta['graph_sha256']
 O=R/'experiments/mmc_shortest_NET_tree_ensemble_pilot_v1_2026-10-19';O.mkdir();bindings={str(p):sha(p) for p in [epfile,graph,pathlib.Path(__file__).resolve(),R/'tools/shortest_NET_tree_ensemble_v1.py']}
 write(O/'protocol.json',dict(bindings=bindings,net_id=net,source=source,sinks=sinks,selection='smallest physical NET id with at least2distinct sinks, episode01',samples=16,seed=19,policy='Exact additive RC minimum, then minimum hops; shared parent choices. Only positive capacity nodes; no intermediate SOURCE/SINK. No target native routes read.',scope='Single-NET real-graph feasibility only; no full forecast, quality, STA, full-flow timing or unseen-family claim.'))
 print('SELECTED',net,source,len(sinks),flush=True)
 caps=array('I');kinds=[];switches={};us=array('I');vs=array('I');costs=array('Q');eligible=[];stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   assert e.get('type') in ['buffer','mux','tristate'];t=e.find('timing');assert Fraction(t.get('Cinternal','0'))==0;value=Fraction(t.get('Tdel','0'))*10**18;assert value.denominator==1 and 0<=value<2**64;switches[int(e.get('id'))]=int(value)
  elif e.tag=='edge' and parent=='rr_edges':
   u,v,s=(int(e.get(k)) for k in ['src_node','sink_node','switch_id']);eid=len(us);cost=switches[s];us.append(u);vs.append(v);costs.append(cost)
   if caps[u]>0 and caps[v]>0 and kinds[u]!='SINK' and kinds[v]!='SOURCE':eligible.append((eid,u,v,cost))
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert len(caps)==904438 and len(us)==8097539 and kinds[source]=='SOURCE' and all(kinds[s]=='SINK' for s in sinks)
 print('GRAPH READY',len(eligible),flush=True);prepared=prepare(eligible,source,sinks);del eligible
 payload=dict(source=source,sinks=sinks,choices={str(v):list(x) for v,x in prepared['choices'].items()},distance={str(v):list(x) for v,x in prepared['distance'].items()});write(O/'predecessor_support.json',payload)
 floorfile=R/'experiments/mmc_prospective_swap_initializers_v1_2026-10-19/episode_01/fresh_raw/initial.json';minimum={q['sink']:q['floor_integer'] for q in json.loads(floorfile.read_text())['records'] if q['net_id']==net};assert set(minimum)==set(sinks)
 assert all(prepared['distance'][s][0]==minimum[s] for s in sinks)
 rows=[];occupancy=Counter()
 for i in range(16):
  tree=sample(prepared,seed=19,net_id=net,sample_index=i);assert len(tree['edge_ids'])==len(tree['nodes'])-1;occupancy.update(tree['nodes'])
  for sink,path in tree['paths'].items():
   u=source;cost=0;seen={u}
   for eid in path:
    assert us[eid]==u;u=vs[eid];assert u not in seen and caps[u]>0;seen.add(u);cost+=costs[eid]
   assert u==sink and cost==minimum[sink] and len(path)==prepared['distance'][sink][1]
  rows.append(dict(sample_index=i,nodes=sorted(tree['nodes']),paths={str(s):list(path) for s,path in tree['paths'].items()}))
 write(O/'samples.json',rows);write(O/'occupancy_counts.json',dict(occupancy));bindings[str(floorfile)]=sha(floorfile)
 for p in O.iterdir():
  if p.is_file():bindings[str(p)]=sha(p)
 write(O/'receipt.json',dict(status='REAL_MMC_SINGLE_NET_16_SHARED_PARENT_TREES_PATHS_AND_FLOORS_PASS',bindings=bindings,net_id=net,distinct_sink_count=len(sinks),support_nodes=len(prepared['distance']),branching_nodes=sum(len(x)>1 for x in prepared['choices'].values()),distinct_sampled_node_unions=len({tuple(x['nodes']) for x in rows}),independent_audit_pending=True,scope='Single NET pilot only. Real graph node R/C zero checked; edge Tdel exact integer. Unique-NET empirical occupancy, not independent-sink union, full-cohort prediction, legal multiNET routing, hardware or speed evidence.'))
 print('REAL NET PILOT PASS',net,len(sinks),len(prepared['distance']),flush=True)
if __name__=='__main__':main()
