"""Full new-graph electrical/domain scan; no inherited MMC assumptions or labels."""
import json,xml.etree.ElementTree as ET
from collections import Counter
from decimal import Decimal
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def main():
 out=R/'experiments/prospective_external_family_graph_semantics_v1_2026-10-19';out.mkdir(exist_ok=False);ep=R/'experiments/prospective_external_family_development_endpoints_v1_2026-10-19/endpoints.json';vp=ep.with_name('independent_verification_v1.json');v=json.loads(vp.read_text());assert v['connections']==15616 and v['bindings'][str(ep)]==sha(ep);e=json.loads(ep.read_text());graph=Path(e['inputs']['graph']['path']);assert sha(graph)==e['graph_sha256'];types=Counter();capacities=Counter();rc=Counter();switches={};segments={};edgecounts=Counter();stack=[];nodes=0;edges=0;timing=0;channel=None;boundaries={}
 for event,x in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(x);continue
  parent=stack[-2] if len(stack)>1 else None
  if x.tag=='channel' and parent is not None and parent.tag=='channels':channel=dict(x.attrib)
  elif x.tag=='switch' and parent is not None and parent.tag=='switches':
   sid=int(x.get('id'));assert sid not in switches;t=x.find('timing');assert t is not None;values={k:Decimal(t.get(k,'0')) for k in ['R','Cin','Cout','Tdel']};assert all(z.is_finite() and z>=0 for z in values.values());scaled=values['Tdel']*10**18;assert scaled==scaled.to_integral_value();switches[sid]=dict(type=x.get('type'),name=x.get('name'),timing={k:str(z) for k,z in values.items()},Tdel_1e18=int(scaled));parent.remove(x);x.clear()
  elif x.tag=='segment' and parent is not None and parent.tag=='segments':sid=int(x.get('id'));assert sid not in segments;segments[sid]=dict(x.attrib);parent.remove(x);x.clear()
  elif x.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   n=int(x.get('id'));assert n==nodes;nodes+=1;kind=x.get('type');cap=int(x.get('capacity'));assert cap>=0;types[kind]+=1;capacities[kind+':'+str(cap)]+=1;t=x.find('timing');assert t is not None;r,c=Decimal(t.get('R')),Decimal(t.get('C'));assert r.is_finite() and c.is_finite() and r>=0 and c>=0;rc[str(r)+','+str(c)]+=1;timing+=1
   if kind in ('CHANX','CHANY'):seg=x.find('segment');assert seg is not None and int(seg.get('segment_id')) in segments
   if kind in ('SOURCE','SINK'):boundaries[n]=kind
   parent.remove(x);x.clear()
  elif x.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   u,w,s=map(lambda k:int(x.get(k)),['src_node','sink_node','switch_id']);assert 0<=u<nodes and 0<=w<nodes and s in switches;edges+=1;edgecounts[s]+=1;parent.remove(x);x.clear()
  stack.pop()
 assert nodes==119878 and edges==1048247 and timing==nodes and channel['chan_width_max']=='128';assert all(boundaries[q['source']]=='SOURCE' and boundaries[q['sink']]=='SINK' for q in e['connections']);zero_rc=all(all(Decimal(z)==0 for z in key.split(',')) for key in rc);result=dict(status='NEW_GRAPH_FULL_NODE_ELECTRICAL_SWITCH_DOMAIN_AND_EDGE_REFERENCES_AUDITED',graph_sha256=e['graph_sha256'],nodes=nodes,edges=edges,node_types=dict(types),capacity_domain=dict(capacities),node_RC_histogram=dict(rc),all_node_RC_zero=zero_rc,switches=switches,segments=segments,edge_switch_counts=dict(edgecounts),channel=channel,connections=len(e['connections']),unique_sources=len({q['source'] for q in e['connections']}),unique_sinks=len({q['sink'] for q in e['connections']}),raw_switch_floor_applicable=zero_rc,scope='Exact XML numeric values and all node/edge references checked. Switch-only integer Tdel is an additive graph-local raw lower-bound model when nodeRC0; it is not automatically native timing closure, budget assignment, capacity feasibility or topology-aware prediction quality.',bindings={str(p):sha(p) for p in [ep,vp,graph,Path(__file__).resolve()]})
 with (out/'verification.json').open('x') as f:json.dump(result,f,indent=2)
 print('GRAPH_SEMANTICS_AUDIT',nodes,edges,'zeroRC',zero_rc,'switches',len(switches),'RCvalues',len(rc),'rawfloor_applicable',zero_rc)
if __name__=='__main__':main()
