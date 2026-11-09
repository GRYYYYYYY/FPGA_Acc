"""Graph-local zeroRC switch-Tdel floors; reverse grouped exact Dijkstra."""
import json,array,struct,subprocess,time,xml.etree.ElementTree as ET,resource
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prospective_external_family_raw_floors_v1_2026-10-19';out.mkdir(exist_ok=False);proof=R/'experiments/prospective_external_family_graph_semantics_v1_2026-10-19/verification.json';v=read(proof);assert v['all_node_RC_zero'] and v['raw_switch_floor_applicable'];assert all(sha(p)==h for p,h in v['bindings'].items());ep=R/'experiments/prospective_external_family_development_endpoints_v1_2026-10-19/endpoints.json';e=read(ep);graph=Path(e['inputs']['graph']['path']);assert sha(graph)==v['graph_sha256'];source=R/'tools/native_resume_prototype/rr_floor_cpp/main.cpp';binary=out/'rr_floor';cmd=['/usr/bin/c++','-std=c++17','-O3',str(source),'-o',str(binary)];paths=[proof,ep,graph,source,Path(__file__).resolve()];bindings={str(p):sha(p) for p in paths};protocol=dict(bindings=bindings,build_command=cmd,queries=len(e['connections']),scale=10**18,algorithm='Exact nonnegative directed additive Dijkstra on reversed XML edges, grouped by original SINK. Query(original SOURCE,SINK) becomes(reverse SINK,SOURCE); initial0. Node capacities unchanged and required positive. Reverse CSR order follows original physical edge order within each sink. Native pair(distance,nodeID) heap and strict-improvement ties frozen.',path_policy='Reverse reported slot path then map to original physical edge IDs. Archive every CID, including unreachable nulls; no dropping failures.',budget_policy='Floor calculation only, no ceiling, criticality or budget assigned. Current per-CID initial timing remains unavailable, never substitute MMC timing.',scope='Unknown-history development source only. Switch-Tdel integer lower-bound model admitted by full nodeRC0 audit, not native timing closure/capacity legality/model quality. Graph-local files only, no old graph cache. No routed target labels.');(out/'protocol.json').write_text(json.dumps(protocol,indent=2));start=time.perf_counter()
 with (out/'build.log').open('x') as f:build=subprocess.run(cmd,stdout=f,stderr=subprocess.STDOUT)
 assert build.returncode==0
 n=v['nodes'];m=v['edges'];caps=array.array('Q');us=array.array('Q');vs=array.array('Q');weights=array.array('Q');stack=[]
 for event,x in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(x);continue
  parent=stack[-2] if len(stack)>1 else None
  if x.tag=='node' and parent is not None and parent.tag=='rr_nodes':assert int(x.get('id'))==len(caps);caps.append(int(x.get('capacity')));parent.remove(x);x.clear()
  elif x.tag=='edge' and parent is not None and parent.tag=='rr_edges':us.append(int(x.get('src_node')));vs.append(int(x.get('sink_node')));weights.append(v['switches'][x.get('switch_id')]['Tdel_1e18']);parent.remove(x);x.clear()
  stack.pop()
 assert len(caps)==n and len(us)==len(vs)==len(weights)==m;offset=array.array('Q',[0])*(n+1)
 for target in vs:offset[target+1]+=1
 for i in range(n):offset[i+1]+=offset[i]
 cursor=array.array('Q',offset);dest=array.array('Q',[0])*m;cost=array.array('Q',[0])*m;physical=array.array('Q',[0])*m
 for eid,(u,w,c) in enumerate(zip(us,vs,weights)):
  slot=cursor[w];cursor[w]+=1;dest[slot]=u;cost[slot]=c;physical[slot]=eid
 inputp=out/'reverse_graph_queries.bin'
 with inputp.open('xb') as f:
  f.write(struct.pack('=4Q',0x5243464c4f4f5231,n,m,len(e['connections'])))
  for a in [offset,dest,cost,caps,array.array('Q',[0])*n]:a.tofile(f)
  for q in e['connections']:f.write(struct.pack('=3Q',q['connection_id'],q['sink'],q['source']))
 mapping=out/'reverse_slot_to_physical_edge.u64';mapping.write_bytes(physical.tobytes());inputreceipt=out/'input_receipt.json';inputreceipt.write_text(json.dumps(dict(bindings={str(p):sha(p) for p in [out/'protocol.json',inputp,mapping,binary]},native_byteorder=__import__('sys').byteorder,all_queries=len(e['connections'])),indent=2));tick=time.perf_counter()
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 with (out/'reverse_floor_results.jsonl').open('x') as f,(out/'solver_stderr.log').open('x') as err:result=subprocess.run([str(binary),str(inputp)],cwd=out,stdout=f,stderr=err,preexec_fn=limit)
 assert result.returncode==0;bycid={q['connection_id']:q for q in e['connections']};seen=set();fail=0;count=0
 with (out/'floors.jsonl').open('x') as f:
  for a in map(json.loads,(out/'reverse_floor_results.jsonl').open()):
   cid=a['connection_id'];assert cid in bycid and cid not in seen;seen.add(cid);q=bycid[cid];edges=None if a['slots'] is None else [physical[s] for s in reversed(a['slots'])];fail+=edges is None;count+=1;f.write(json.dumps(dict(q,minimum_integer=a['minimum_integer'],physical_edge_ids=edges),separators=(',',':'))+'\n')
 assert seen==set(bycid);assert all(sha(p)==h for p,h in bindings.items());files=[out/'protocol.json',inputreceipt,out/'reverse_floor_results.jsonl',out/'floors.jsonl',out/'solver_stderr.log'];(out/'receipt.json').write_text(json.dumps(dict(status='ALL_DEVELOPMENT_GRAPH_RAW_FLOORS_PRODUCED_PENDING_INDEPENDENT_CHECK',connections=count,unreachable=fail,scale=10**18,solver_and_reconstruction_seconds=time.perf_counter()-tick,whole_preparation_component_seconds=time.perf_counter()-start,bindings={str(p):sha(p) for p in files},independent_floor_and_path_verification_pending=True,no_budget_assigned=True,new_route_labels=False),indent=2));print('EXTERNAL_RAW_FLOORS_PRODUCED',count,'unreachable',fail,flush=True)
if __name__=='__main__':main()
