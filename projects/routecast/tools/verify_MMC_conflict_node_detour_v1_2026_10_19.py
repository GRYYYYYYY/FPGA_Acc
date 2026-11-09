"""Independent XML all-edge dual inequalities plus tight-edge reachability."""
import json,pathlib,sys,xml.etree.ElementTree as ET
from array import array
from fractions import Fraction
from collections import deque
from hashlib import sha256
R=pathlib.Path(__file__).resolve().parents[1];O=R/'experiments/mmc_conflict_node_detour_v1_2026-10-19'
def main():
 protocol=json.loads((O/'protocol.json').read_text());result=json.loads((O/'results.json').read_text())
 for name,h in protocol['bindings'].items():assert sha256(pathlib.Path(name).read_bytes()).hexdigest()==h
 graph=next(pathlib.Path(p) for p in protocol['bindings'] if p.endswith('rr_graph.xml'))
 caps=array('I');kinds=[];us=array('I');vs=array('I');ws=array('Q');switches={};stack=[]
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2].tag if len(stack)>1 else None
  if e.tag=='node' and parent=='rr_nodes':
   assert int(e.get('id'))==len(caps);caps.append(int(e.get('capacity')));kinds.append(e.get('type'));t=e.find('timing');assert Fraction(t.get('R'))==Fraction(t.get('C'))==0
  elif e.tag=='switch' and parent=='switches':
   t=e.find('timing');assert e.get('type') in ['buffer','mux','tristate'] and Fraction(t.get('Cinternal','0'))==0
   w=Fraction(t.get('Tdel','0'))*10**18;assert w.denominator==1;switches[int(e.get('id'))]=int(w)
  elif e.tag=='edge' and parent=='rr_edges':us.append(int(e.get('src_node')));vs.append(int(e.get('sink_node')));ws.append(switches[int(e.get('switch_id'))])
  if (e.tag,parent) in [('node','rr_nodes'),('switch','switches'),('edge','rr_edges')]:stack[-2].remove(e);e.clear()
  stack.pop()
 assert sys.byteorder=='little';rows=[]
 for row in result['rows']:
  assert row['status']=='PRODUCED_NOT_INDEPENDENTLY_VERIFIED'
  net,mode=row['net_id'],row['mode'];pc=array('Q');ph=array('I')
  pc.frombytes((O/f'net_{net}_{mode}_potential_cost.bin').read_bytes());ph.frombytes((O/f'net_{net}_{mode}_potential_hops.bin').read_bytes());assert len(pc)==len(ph)==len(caps)
  labels=json.loads((O/f'net_{net}_{mode}_sink_labels.json').read_text());source=row['source'];assert (pc[source],ph[source])==(0,0)
  blocked=protocol['blocked_node'] if mode=='blocked' else -1;tight={};checked=0
  for a,b,w in zip(us,vs,ws):
   if caps[a]==0 or caps[b]==0 or kinds[a]=='SINK' or kinds[b]=='SOURCE' or a==blocked or b==blocked:continue
   lhs=(pc[b],ph[b]);rhs=(pc[a]+w,ph[a]+1);assert lhs<=rhs;checked+=1
   if lhs==rhs:tight.setdefault(a,[]).append(b)
  seen={source};q=deque([source])
  while q:
   for b in tight.get(q.popleft(),[]):
    if b not in seen:seen.add(b);q.append(b)
  for s,label in labels.items():
   s=int(s);assert kinds[s]=='SINK' and s in seen and [pc[s],ph[s]]==label
  rows.append(dict(net_id=net,mode=mode,sinks_certified=len(labels),edge_inequalities=checked));print(rows[-1],flush=True)
 for net in protocol['NET_ids']:
  before=json.loads((O/f'net_{net}_original_sink_labels.json').read_text());after=json.loads((O/f'net_{net}_blocked_sink_labels.json').read_text());assert before.keys()==after.keys()
  summary=next(r for r in result['rows'] if r['net_id']==net and r['mode']=='blocked')
  assert summary['increased_RC_sinks']==sum(after[s][0]>before[s][0] for s in before)
  assert summary['same_RC_more_hops_sinks']==sum(after[s][0]==before[s][0] and after[s][1]>before[s][1] for s in before)
 bindings={str(p):sha256(p.read_bytes()).hexdigest() for p in O.iterdir() if p.is_file()}
 bindings[str(pathlib.Path(__file__).resolve())]=sha256(pathlib.Path(__file__).read_bytes()).hexdigest()
 with (O/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL4_FULL_GRAPH_MINIMUM_RC_AND_SECONDARY_HOPS_CERTIFIED',rows=rows,bindings=bindings,method='Independent original XML edge inequalities plus source-to-every-sink tight-edge reachability',scope='Fixed two NETs, original and node646275 deleted graphs only; no global multi-NET feasibility claim'),f,indent=2)
if __name__=='__main__':main()
