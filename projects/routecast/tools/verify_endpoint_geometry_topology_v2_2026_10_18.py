"""Original XML edge-by-edge authentication and independent adjacency features."""
import array,collections,json,sys,xml.etree.ElementTree as ET
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha

def main():
 E=R/'experiments';root=E/'mmc_endpoint_geometry_topology_v2_2026-10-18';rp=root/'receipt.json';r=json.loads(rp.read_text());manifest=json.loads((root/'vector_manifest.json').read_text());graph=E/'ultraembedded_mmc_continuous_workflow_v6_2026-10-08/seed/rr/mmc/rr_graph.xml';idx=json.loads((E/'real_joint_full_score_v2_2026-10-18/graph_index.json').read_text());edges=[]
 for name in ['edge_source','edge_destination']:
  desc=idx['arrays'][name];assert sha(desc['path'])==desc['sha256'];a=array.array('I');a.frombytes(Path(desc['path']).read_bytes());edges.append(a)
 cases={};sources=set();sinks=set()
 for case in ['case_01','case_02','case_03']:
  p=E/f'mmc_multiplacement_inputs_v1_2026-10-18/{case}/demand/endpoints.json';assert sha(p)==r['bindings'][str(p)];q=json.loads(p.read_text())['connections'];cases[case]=q;sources.update(x['source'] for x in q);sinks.update(x['sink'] for x in q)
 needed=sources|sinks;geometry={};kind={};out=collections.defaultdict(list);inc=collections.defaultdict(list);stack=[];edge=0;nodes=0
 for event,e in ET.iterparse(graph,events=['start','end']):
  if event=='start':stack.append(e);continue
  parent=stack[-2] if len(stack)>1 else None
  if e.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   n=int(e.attrib['id']);assert n not in kind;kind[n]=e.attrib['type'];nodes+=1
   if n in needed:
    loc=e.find('loc').attrib;geometry[n]=tuple(int(loc[k]) for k in ['xlow','xhigh','ylow','yhigh'])+(int(loc.get('layer','0')),)
   parent.remove(e);e.clear()
  elif e.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   a,b=int(e.attrib['src_node']),int(e.attrib['sink_node']);assert a==edges[0][edge] and b==edges[1][edge];edge+=1
   if a in sources or kind[a]=='OPIN':out[a].append(b)
   if b in sinks or kind[b]=='IPIN':inc[b].append(a)
   parent.remove(e);e.clear()
  stack.pop()
 assert edge==len(edges[0])==8097539 and nodes==904438 and set(geometry)==needed
 forward={};reverse={}
 for s in sources:
  assert kind[s]=='SOURCE' and all(kind[m]=='OPIN' for m in out[s]);forward[s]=len(set(n for m in set(out[s]) for n in out[m]))
 for t in sinks:
  assert kind[t]=='SINK' and all(kind[m]=='IPIN' for m in inc[t]);reverse[t]=len(set(n for m in set(inc[t]) for n in inc[m]))
 checked=0
 for case,qs in cases.items():
  vectors={}
  for name in ['abs_dx','abs_dy','manhattan_distance','source_outdegree','sink_indegree','source_two_hop_unique','sink_two_hop_unique']:
   d=manifest[case+'__'+name];assert sha(d['path'])==d['sha256'];a=array.array('I');a.frombytes(Path(d['path']).read_bytes());assert len(a)==115572;vectors[name]=a
  for q in qs:
   s,t,c=q['source'],q['sink'],q['connection_id'];a,b=geometry[s],geometry[t];assert a[0]==a[1] and a[2]==a[3] and b[0]==b[1] and b[2]==b[3] and a[4]==b[4];dx,dy=abs(a[0]-b[0]),abs(a[2]-b[2]);expected=[dx,dy,dx+dy,len(set(out[s])),len(set(inc[t])),forward[s],reverse[t]]
   assert [v[c] for v in vectors.values()]==expected;checked+=len(expected)
  print('ORIGINAL XML FEATURE VERIFICATION PASS',case,flush=True)
 for p,h in r['bindings'].items():assert sha(p)==h
 bindings={str(p):sha(p) for p in [Path(__file__),rp,root/'vector_manifest.json',root/'protocol.json']}
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='all2427012CID_feature_values_and8097539original_XML_edges_verified',bindings=bindings,feature_values_verified=checked,XML_edges_verified=edge,RR_nodes_verified=nodes,scope='Independent originalXML adjacency and endpoint geometry. No outcome labels, legal route multiplicity or search/time-benefit claim.'),f,indent=2)
if __name__=='__main__':main()
