"""Predeclared input-only exact channel exchangeability screen; no routing labels."""
import json,time,resource
import xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from exact_channel_twins_v1 import Builder
R=Path(__file__).resolve().parents[1];D=R/'experiments/mmc_exact_channel_twins_v1_2026-10-21';D.mkdir()
epf=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18/case_01/demand/endpoints.json';ep=json.loads(epf.read_text());graph=Path(ep['inputs']['graph']['path']);expected=ep['graph_sha256'];assert expected==ep['inputs']['graph']['sha256'] and sha(graph)==expected
bindings={str(p):sha(p) for p in [Path(__file__),R/'tools/exact_channel_twins_v1.py',R/'tests/test_exact_channel_twins_v1.py',epf]};bindings[str(graph)]=expected
(D/'protocol.json').write_text(json.dumps({'bindings':bindings,'hypothesis':'An exact metadata/weighted-incoming/weighted-outgoing equivalence class of positive CHAN nodes supports simultaneous whole-route node permutations with capacity and RC/native switch identities preserved. This may provide physically supported alternative states beyond minimum-raw paths. Screen existence before any predictor.','metadata':'All node attributes except original id; all child metadata recursively, except direct loc.ptc for CHAN nodes. Capacity/geometry/direction/segment/electrical attributes retained. Exact switch IDs and edge multiplicities retained. SOURCE/SINK/pin nodes never moved.','failure_rule':'If no class has at least2members, close this sufficient local twin mechanism without pooling geometry classes, changing edge equivalence or fitting labels. This does not rule out general multi-node graph automorphisms.','validation':'Exhaustive64 directed3node simple graphs, switch/multiplicity/incoming/metadata negative controls, whole-path/capacity transport toy contract. On real graph independently verify every representative/member incident-edge multiset under swap.','scope':'One exposed immutable MMC RR graph, input-only diagnostic. No old or target route/occupancy label read; no forecast, native run, prediction gate or gain claim.','native_calls':0},indent=2)+'\n')
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
parse_seconds=time.perf_counter()-start;print('INPUT GRAPH PARSED',n,builder.edges,flush=True);tick=time.perf_counter();groups=builder.classes();partition_seconds=time.perf_counter()-tick
metadata_sizes=Counter(builder.meta.values());metadata_multimember=sum(v>1 for v in metadata_sizes.values());verified_swaps=0
for group in groups:
 for member in group[1:]:builder.verify_swap(group[0],member);verified_swaps+=1
assert all(sha(p)==h for p,h in bindings.items())
receipt={'original_nodes':n,'original_edges':builder.edges,'positive_channels':len(builder.meta),'metadata_groups':len(metadata_sizes),'metadata_groups_with_multiple_members':metadata_multimember,'exact_twin_classes':len(groups),'exact_twin_channel_members':sum(map(len,groups)),'all_representative_member_swaps_verified':verified_swaps,'classes':[list(g) for g in groups],'parse_seconds':parse_seconds,'exact_partition_seconds':partition_seconds,'total_seconds':time.perf_counter()-start,'peak_RSS_KiB':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'input_bindings_unchanged':True,'bindings':bindings,'scope':'Sufficient local exact adjacency twins only. No geometric pooling, general automorphism impossibility, prediction accuracy, current moved-endpoint joint legality, native or gain claim.'}
(D/'verification.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:v for k,v in receipt.items() if k not in ['bindings','classes']},indent=2),flush=True)
