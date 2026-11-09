"""Original XML/CSR/path audits plus separate forward ordered-set shortest solver."""
import json,array,struct,subprocess,time,xml.etree.ElementTree as ET
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 root=R/'experiments/prospective_external_family_raw_floors_v1_2026-10-19';rp=root/'receipt.json';r=read(rp);assert r['connections']==15616 and r['unreachable']==0 and all(sha(p)==h for p,h in r['bindings'].items());inp=read(root/'input_receipt.json');assert all(sha(p)==h for p,h in inp['bindings'].items());ep=R/'experiments/prospective_external_family_development_endpoints_v1_2026-10-19/endpoints.json';e=read(ep);graph=Path(e['inputs']['graph']['path']);protocol=read(root/'protocol.json');assert protocol['bindings'][str(graph)]==sha(graph);sem=read(R/'experiments/prospective_external_family_graph_semantics_v1_2026-10-19/verification.json');binaryinput=root/'reverse_graph_queries.bin'
 with binaryinput.open('rb') as f:
  magic,n,m,q=struct.unpack('=4Q',f.read(32));assert (n,m,q)==(119878,1048247,15616);arrays=[]
  for size in [n+1,m,m,n,n]:
   a=array.array('Q');a.fromfile(f,size);arrays.append(a)
  queries=[struct.unpack('=3Q',f.read(24)) for _ in range(q)];assert not f.read(1)
 off,dest,cost,caps,initial=arrays;assert all(v==0 for v in initial);physical=array.array('Q');physical.frombytes((root/'reverse_slot_to_physical_edge.u64').read_bytes());assert len(physical)==m;slotbyedge=array.array('Q',[0])*m
 for s,eid in enumerate(physical):slotbyedge[eid]=s
 assert all(physical[slotbyedge[eid]]==eid for eid in range(m));xmlsrc=array.array('Q');xmldst=array.array('Q');xmlcost=array.array('Q');stack=[];nn=0;mm=0
 for event,x in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(x);continue
  parent=stack[-2] if len(stack)>1 else None
  if x.tag=='node' and parent is not None and parent.tag=='rr_nodes':assert int(x.get('id'))==nn and int(x.get('capacity'))==caps[nn];nn+=1;parent.remove(x);x.clear()
  elif x.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   u,v=int(x.get('src_node')),int(x.get('sink_node'));w=sem['switches'][x.get('switch_id')]['Tdel_1e18'];s=slotbyedge[mm];assert off[v]<=s<off[v+1] and dest[s]==u and cost[s]==w;xmlsrc.append(u);xmldst.append(v);xmlcost.append(w);mm+=1;parent.remove(x);x.clear()
  stack.pop()
 assert nn==n and mm==m;bycid={c['connection_id']:c for c in e['connections']};assert set(queries)=={(cid,c['sink'],c['source']) for cid,c in bycid.items()};floors=list(map(json.loads,(root/'floors.jsonl').open()));assert len(floors)==len({f['connection_id'] for f in floors})==q;expected=root/'expected_floor_values.txt';path_edges=0
 with expected.open('x') as f:
  for a in floors:
   c=bycid[a['connection_id']];assert all(a[k]==v for k,v in c.items());u=c['source'];seen={u};delay=0
   for eid in a['physical_edge_ids']:
    assert xmlsrc[eid]==u;u=xmldst[eid];assert u not in seen and caps[u]>0;seen.add(u);delay+=xmlcost[eid];path_edges+=1
   assert u==c['sink'] and delay==a['minimum_integer'];f.write(f"{a['connection_id']} {delay}\n")
 source=R/'tools/verify_external_raw_floor_distances_v1.cpp';binary=root/'independent_forward_floor_verifier';build=['/usr/bin/c++','-std=c++17','-O3',str(source),'-o',str(binary)];vp=root/'verification_protocol.json';vp.write_text(json.dumps(dict(build_command=build,command=[str(binary),str(binaryinput),str(expected)],bindings={str(p):sha(p) for p in [rp,binaryinput,root/'floors.jsonl',expected,graph,source,Path(__file__).resolve()]},scope='Full XML reverse-CSR/capacity/physical-ID mapping, every original physical path and exact delay, then independent forward grouped ordered-set Dijkstra for every CID.'),indent=2));tick=time.perf_counter()
 with (root/'verification_build.log').open('x') as log:b=subprocess.run(build,stdout=log,stderr=subprocess.STDOUT)
 assert b.returncode==0
 with (root/'independent_forward_floor.log').open('x') as log:run=subprocess.run([str(binary),str(binaryinput),str(expected)],stdout=log,stderr=subprocess.STDOUT)
 text=(root/'independent_forward_floor.log').read_text();assert run.returncode==0 and 'FORWARD_SET_DIJKSTRA_ALL_FLOORS_PASS 15616 ' in text
 with (root/'independent_verification_v1.json').open('x') as f:json.dump(dict(status='ALL15616_XML_PATHS_REVERSE_CSR_AND_INDEPENDENT_FORWARD_MINIMA_VERIFIED',connections=q,physical_path_edges=path_edges,independent_verification_component_seconds=time.perf_counter()-tick,no_budget_assigned=True,bindings={str(p):sha(p) for p in [rp,vp,root/'floors.jsonl',binary,root/'verification_build.log',root/'independent_forward_floor.log']},scope='All graph-local additive integer switch-Tdel minima and simple physical witnesses checked. No global joint capacity legality, native timing closure, criticality, forecast quality or strict family claim.'),f,indent=2)
 print('ALL_EXTERNAL_RAW_FLOORS_VERIFIED',q,path_edges,flush=True)
if __name__=='__main__':main()
