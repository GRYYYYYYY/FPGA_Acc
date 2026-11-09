"""Source-only endpoint geometry and directed two-hop structural support."""
import array,collections,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';out=E/'mmc_endpoint_geometry_topology_v2_2026-10-18';out.mkdir(exist_ok=False);graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';indexp=E/'real_joint_full_score_v2_2026-10-18/graph_index.json';proofp=E/'real_joint_full_score_v2_2026-10-18/verification.json';idx=json.loads(indexp.read_text());proof=json.loads(proofp.read_text());assert proof['status']=='pass';bindings={str(p):sha(p) for p in [Path(__file__),graph,indexp,proofp]};assert bindings[str(graph)]==idx['graph_sha256'];cases={};sources=set();sinks=set()
 for case in ['case_01','case_02','case_03']:
  p=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';ep=json.loads(p.read_text());assert ep['graph_sha256']==idx['graph_sha256'];bindings[str(p)]=sha(p);qs=ep['connections'];assert len(qs)==115572 and sorted(q['connection_id'] for q in qs)==list(range(115572));cases[case]=qs;sources.update(q['source'] for q in qs);sinks.update(q['sink'] for q in qs)
 protocol=dict(status='source_only_definitions_fixed_before_label_evaluation',features=['abs_dx','abs_dy','manhattan_distance','source_outdegree','sink_indegree','source_two_hop_unique','sink_two_hop_unique'],two_hop='Number of distinct RR vertices reachable by exactly2 directed edges from SOURCE, or reaching SINK by exactly2 directed edges. Deduplicate parallel edges and converging walks. Structural alternatives, not legal route count, congestion or a shortest-path distance.',geometry='Require SOURCE/SINK point coordinates and same layer; abs differences and L1 in tile coordinates.',scope='All3current development placements, complete115572CID domains including later uncalled CIDs. No native labels or prior outcome scores read; no fit, outcome selection or full-flow speed claim.')
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2));needed=sources|sinks;coords={};stack=[]
 for event,node in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(node);continue
  parent=stack[-2] if len(stack)>1 else None
  if node.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   n=int(node.get('id'))
   if n in needed:
    kind=node.get('type');assert kind==('SOURCE' if n in sources else 'SINK');loc=node.find('loc');x,y=int(loc.get('xlow')),int(loc.get('ylow'));assert x==int(loc.get('xhigh')) and y==int(loc.get('yhigh'));coords[n]=(x,y,int(loc.get('layer','0')))
   parent.remove(node);node.clear()
  if node.tag=='rr_nodes':break
  stack.pop()
 assert set(coords)==needed;arrays={}
 for name in ['edge_source','edge_destination']:
  desc=idx['arrays'][name];p=desc['path'];assert sha(indexp)==proof['bindings'][str(indexp)] and sha(p)==desc['sha256'];bindings[p]=desc['sha256'];a=array.array('I');a.frombytes(Path(p).read_bytes());assert len(a)==8097539 and sys.byteorder=='little';arrays[name]=a
 first={s:set() for s in sources};last={s:set() for s in sinks}
 for a,b in zip(arrays['edge_source'],arrays['edge_destination']):
  if a in first:first[a].add(b)
  if b in last:last[b].add(a)
 sf=collections.defaultdict(list);sl=collections.defaultdict(list)
 for root,ms in first.items():
  for m in ms:sf[m].append(root)
 for root,ms in last.items():
  for m in ms:sl[m].append(root)
 forward={s:set() for s in sources};reverse={s:set() for s in sinks}
 for a,b in zip(arrays['edge_source'],arrays['edge_destination']):
  for root in sf.get(a,()):forward[root].add(b)
  for root in sl.get(b,()):reverse[root].add(a)
 manifest={};stats=[]
 for case,qs in cases.items():
  qs=sorted(qs,key=lambda q:q['connection_id']);vectors={name:array.array('I') for name in protocol['features']}
  for q in qs:
   s,t=q['source'],q['sink'];a,b=coords[s],coords[t];assert a[2]==b[2];dx,dy=abs(a[0]-b[0]),abs(a[1]-b[1]);values=[dx,dy,dx+dy,len(first[s]),len(last[t]),len(forward[s]),len(reverse[t])]
   for name,v in zip(protocol['features'],values):vectors[name].append(v)
  folder=out/case;folder.mkdir()
  for name,v in vectors.items():
   p=folder/(name+'.u32');p.write_bytes(v.tobytes());manifest[case+'__'+name]=dict(path=str(p),sha256=sha(p),values=len(v),typecode='I',itemsize=v.itemsize,byteorder=sys.byteorder);stats.append(dict(case=case,feature=name,min=min(v),max=max(v),distinct=len(set(v))))
  print('SOURCE ENDPOINT FEATURES COMPLETE',case,flush=True)
 for p,h in bindings.items():assert sha(p)==h
 (out/'vector_manifest.json').write_text(json.dumps(manifest,indent=2))
 with (out/'receipt.json').open('x') as f:json.dump(dict(status='all346716CID_source_geometry_and_directed_topology_features_extracted',bindings=bindings,stats=stats,scope=protocol['scope'],independent_XML_feature_verification_pending=True),f,indent=2)
if __name__=='__main__':main()
