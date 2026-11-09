"""Independent ElementTree full XML scan checks positive and zero adjacency flags."""
import json,xml.etree.ElementTree as ET,array
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def ar(p,t):
 a=array.array(t);a.frombytes(p.read_bytes());return a

def main():
 root=R/'experiments/mmc_topology_context_v1_2026-10-19';rp=root/'receipt.json';r=read(rp);assert r['status']=='ALL3_FIXED_DIRECTED_TOPOLOGY_CONTEXTS_PRODUCED' and not r['target_final_labels_read'];assert all(sha(p)==h for p,h in r['bindings'].items());graph=R/'experiments/ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';cases=[z['case'] for z in r['rows']];prefix=R/'experiments/mmc_native_first_iteration_v1_2026-10-18';ledgers=[{int(n):v for n,v in read(prefix/c/'diagnostic_sketch_v1.json')['ledger'].items()} for c in cases];caps={};over=[];incoming=[set() for c in cases];outgoing=[set() for c in cases];stack=[];edges=0
 for event,e in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(e);continue
  parent=stack[-2] if len(stack)>1 else None
  if e.tag=='node' and parent is not None and parent.tag=='rr_nodes':caps[int(e.get('id'))]=int(e.get('capacity'));parent.remove(e);e.clear()
  elif e.tag=='rr_nodes':
   assert len(caps)==904438;over=[{n for n,v in l.items() if caps[n]>0 and v>caps[n]} for l in ledgers]
  elif e.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   u,v=int(e.get('src_node')),int(e.get('sink_node'));edges+=1
   if u!=v:
    for i,ns in enumerate(over):
     if u in ns:incoming[i].add(v)
     if v in ns:outgoing[i].add(u)
   parent.remove(e);e.clear()
  stack.pop()
 assert edges==8097539 and not stack;ids=ar(R/'experiments/mmc_resource_context_v1_2026-10-19/CHANNEL_ids.u32','I');rows=[]
 for i,c in enumerate(cases):
  saved=(root/(c+'.all_node_flags.u8')).read_bytes();assert len(saved)==904438
  assert all(saved[n]==int(n in incoming[i])+2*int(n in outgoing[i]) for n in range(904438));base=ar(R/f'experiments/mmc_resource_owner_context_v1_2026-10-19/{c}.u16','H');new=ar(root/(c+'.u16'),'H');assert len(new)==len(base)==len(ids)==258720 and all(v==4*b+saved[n] for n,b,v in zip(ids,base,new));rows.append(dict(case=c,all_node_flags_verified=904438,CHANNEL_codes_verified=258720));print('FULL_XML_TOPOLOGY_FLAGS_PASS',c,flush=True)
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL3_ORIGINAL_XML_POSITIVE_AND_ZERO_FLAGS_AND_CODES_INDEPENDENTLY_VERIFIED',rows=rows,bindings={str(p):sha(p) for p in [rp,Path(__file__).resolve()]},scope='Independent parser and set-based directed neighbor traversal; no target labels or fitted scores. Upstream prefix identity/budget diagnostic proofs inherited.'),f,indent=2)
if __name__=='__main__':main()
