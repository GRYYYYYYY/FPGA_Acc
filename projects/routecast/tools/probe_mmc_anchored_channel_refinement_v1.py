"""Four-round bounded anchored-channel refinement; input-only graph screen."""
import json,time,resource,sys
from array import array
from pathlib import Path
from collections import Counter,defaultdict
import xml.etree.ElementTree as ET
from pre_route_endpoints import sha
from exact_channel_twins_v1 import Builder
from anchored_channel_refinement_v1 import initial,step,summary
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_anchored_channel_refinement_v1_2026-10-21';D.mkdir()
epf=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';ep=json.loads(epf.read_text());graph=Path(ep['inputs']['graph']['path']);expected=ep['graph_sha256'];assert sha(graph)==expected
bindings={str(p):sha(p) for p in [Path(__file__),epf,R/'tools/exact_channel_twins_v1.py',R/'tools/anchored_channel_refinement_v1.py',R/'tests/test_anchored_channel_refinement_v1.py']};bindings[str(graph)]=expected
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'max_rounds':4,'stop_rule':'Stop at all-singleton positive channels or no partition split, otherwise stop after4; never change limits based on result.','domain':'All non-positive-channel vertices individually fixed, including terminals/local pins/disabled channels. Movable positive CHAN metadata preserves all attributes/children except original id and loc.ptc. Exact directed switch-ID edge multisets retained.','invariant':'Any metadata/switch-preserving graph automorphism fixing all anchors must preserve each refinement color. Singleton colors rule out nonidentity channel permutations in this anchored domain; unresolved colors do not certify an automorphism.','validation':'Exhaustive64 directed3node graph automorphisms; coupled symmetry with no local twins; two-hop anchored propagation; switch/direction/multiplicity/metadata negatives.','scope':'Input-only bounded structural diagnostic on exposed MMC graph; no route label, predictor/native execution, original metric gate or gain claim.','native_calls':0},indent=2)+'\n')
def canonical(e,*,node=False,track=False):
 attrs=tuple(sorted((k,v) for k,v in e.attrib.items() if not (node and k=='id') and not(track and k=='ptc')))
 return (e.tag,attrs,(e.text or '').strip(),tuple(canonical(c,track=node and c.tag=='loc') for c in e),(e.tail or '').strip())
start=time.perf_counter();builder=Builder();stack=[];n=0;switches=set();used=set();nodes_done=False
for event,e in ET.iterparse(graph,events=('start','end')):
 if event=='start':
  stack.append(e)
  if len(stack)==1 and e.tag!='rr_graph':raise ValueError('RR root')
  continue
 parent=stack[-2].tag if len(stack)>1 else None
 if e.tag=='node' and parent=='rr_nodes':
  if int(e.get('id'))!=n:raise ValueError('original node ID')
  cap=int(e.get('capacity'))
  if cap<0:raise ValueError('capacity')
  if e.get('type') in ['CHANX','CHANY'] and cap>0:builder.node(n,canonical(e,node=True))
  n+=1
 elif e.tag=='rr_nodes':nodes_done=True
 elif e.tag=='edge' and parent=='rr_edges':
  u,v,s=map(int,[e.get('src_node'),e.get('sink_node'),e.get('switch_id')])
  if not nodes_done or not 0<=u<n or not 0<=v<n or s<0:raise ValueError('edge identity/domain')
  used.add(s);builder.edge(u,v,s)
 elif e.tag=='switch' and parent=='switches':
  s=int(e.get('id'))
  if s<0 or s in switches:raise ValueError('switch ID')
  switches.add(s)
 if (e.tag,parent) in [('node','rr_nodes'),('edge','rr_edges'),('switch','switches'),('segment','segments')]:stack[-2].remove(e);e.clear()
 stack.pop()
assert used<=switches and n>0 and builder.edges>0
parse_seconds=time.perf_counter()-start;print('REFINEMENT INPUT GRAPH PARSED',n,builder.edges,flush=True)
ids=sorted(builder.meta);files={}
def save(name,values,kind):
 data=array(kind,values)
 assert data.itemsize==({'Q':8,'I':4}[kind])
 if sys.byteorder!='little':data.byteswap()
 p=D/name;p.write_bytes(data.tobytes());files[str(p)]=sha(p)
save('channel_ids.u64',ids,'Q');colors=initial(builder.meta);save('round0.colors.u32',(colors[n] for n in ids),'I');rows=[{'round':0,**summary(colors),'seconds':0.0}]
for r in range(1,5):
 tick=time.perf_counter();new=step(colors,builder.out,builder.inc);stat=summary(new);assert stat['classes']>=rows[-1]['classes'];stable=stat['classes']==rows[-1]['classes'];colors=new;save(f'round{r}.colors.u32',(colors[n] for n in ids),'I');rows.append({'round':r,**stat,'seconds':time.perf_counter()-tick,'partition_stable':stable});print('REFINEMENT',json.dumps(rows[-1]),flush=True)
 if stat['unresolved_channels']==0 or stable:break
bins=defaultdict(list)
for node,color in colors.items():bins[color].append(node)
unresolved=[v for v in bins.values() if len(v)>1]
assert all(sha(p)==h for p,h in bindings.items())
receipt={'original_nodes':n,'original_edges':builder.edges,'positive_channels':len(ids),'rounds':rows,'all_channels_singleton':not unresolved,'unresolved_classes':unresolved,'parse_seconds':parse_seconds,'total_seconds':time.perf_counter()-start,'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'bindings':bindings,'files':files,'scope':'Only anchored channel automorphisms in this exact metadata/switch-ID domain. No approximate interchangeability, general graph rigidity, predictor quality or gain claim.'}
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print('ANCHORED REFINEMENT COMPLETE',not unresolved,flush=True)
