"""All12 raw floors, graph-affine exact cache, independent new minima, every path."""
import json,array,struct,subprocess,shutil,time,resource,xml.etree.ElementTree as ET
from decimal import Decimal
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
from graph_raw_floor_cache_v1 import Cache,VERSION
R=Path(__file__).resolve().parents[1];INF=2**64-1

def read(p):return json.loads(p.read_text())
def run(cmd,stdout,stderr=None):
 def limit():resource.setrlimit(resource.RLIMIT_AS,(8*2**30,8*2**30))
 with Path(stdout).open('x') as out:
  if stderr:
   with Path(stderr).open('x') as err:r=subprocess.run(list(map(str,cmd)),stdout=out,stderr=err,preexec_fn=limit)
  else:r=subprocess.run(list(map(str,cmd)),stdout=out,stderr=subprocess.STDOUT,preexec_fn=limit)
 if r.returncode:raise RuntimeError(f'failed exit{r.returncode}: {cmd[0]}, logs retained')

def setup_graph(frame,d):
 start=time.perf_counter();graph=Path(frame['graph']);digest=sha(graph);assert digest==frame['graph_sha256'];n=frame['graph_nodes'];m=frame['graph_edges'];us=array.array('Q');vs=array.array('Q');weights=array.array('Q');caps=array.array('Q');kinds=[];switches={};stack=[]
 for event,x in ET.iterparse(graph,events=('start','end')):
  if event=='start':stack.append(x);continue
  parent=stack[-2] if len(stack)>1 else None
  if x.tag=='switch' and parent is not None and parent.tag=='switches':
   sid=int(x.get('id'));assert sid not in switches;t=x.find('timing');assert all(Decimal(t.get(k,'0'))==0 for k in ['R','Cin','Cout','Cinternal']);delay=Decimal(t.get('Tdel','0'))*10**18;assert delay.is_finite() and delay>=0 and delay==delay.to_integral_value();switches[sid]=int(delay);parent.remove(x);x.clear()
  elif x.tag=='node' and parent is not None and parent.tag=='rr_nodes':
   assert int(x.get('id'))==len(caps);cap=int(x.get('capacity'));assert cap>0;t=x.find('timing');assert Decimal(t.get('R'))==Decimal(t.get('C'))==0;caps.append(cap);kinds.append(x.get('type'));parent.remove(x);x.clear()
  elif x.tag=='edge' and parent is not None and parent.tag=='rr_edges':
   u,v=int(x.get('src_node')),int(x.get('sink_node'));assert 0<=u<n and 0<=v<n;us.append(u);vs.append(v);weights.append(switches[int(x.get('switch_id'))]);parent.remove(x);x.clear()
  stack.pop()
 assert len(caps)==n and len(us)==len(vs)==len(weights)==m and n*max(weights)<INF;offset=array.array('Q',[0])*(n+1)
 for v in vs:offset[v+1]+=1
 for i in range(n):offset[i+1]+=offset[i]
 cur=array.array('Q',offset);dest=array.array('Q',[0])*m;cost=array.array('Q',[0])*m;physical=array.array('Q',[0])*m
 for eid,(u,v,w) in enumerate(zip(us,vs,weights)):s=cur[v];cur[v]+=1;dest[s]=u;cost[s]=w;physical[s]=eid
 inverse=array.array('Q',[0])*m
 for slot,eid in enumerate(physical):inverse[eid]=slot
 assert all(physical[inverse[eid]]==eid for eid in range(m))
 for eid,(u,v,w) in enumerate(zip(us,vs,weights)):
  slot=inverse[eid];assert offset[v]<=slot<offset[v+1] and dest[slot]==u and cost[slot]==w
 static=d/'reverse_payload.bin'
 with static.open('xb') as f:
  for a in [offset,dest,cost,caps,array.array('Q',[0])*n]:a.tofile(f)
 mp=d/'reverse_slot_to_physical.u64';mp.write_bytes(physical.tobytes());assert sha(graph)==digest;proof=d/'graph_input_verification.json';proof.write_text(json.dumps(dict(status='ALL_XML_ELECTRICAL_CAPACITY_AND_STATIC_REVERSE_INPUTS_BOUND',graph_sha256=digest,nodes=n,edges=m,objective=VERSION,setup_seconds=time.perf_counter()-start,bindings={str(p):sha(p) for p in [graph,static,mp,Path(__file__).resolve()]}),indent=2));return dict(n=n,m=m,hash=digest,caps=caps,kinds=kinds,us=us,vs=vs,weights=weights,physical=physical,static=static,proof=proof)

def check_path(g,s,t,entry):
 if entry.minimum is None:assert entry.edges is None;return 0
 u=s;seen={u};total=0
 for eid in entry.edges:
  assert 0<=eid<g['m'] and g['us'][eid]==u;u=g['vs'][eid];assert u not in seen and g['caps'][u]>0;seen.add(u);total+=g['weights'][eid]
 assert u==t and total==entry.minimum;return len(entry.edges)

def main():
 root=R/'experiments/wbuart_frame_raw_floors_v1_2026-10-20';root.mkdir(exist_ok=False);matrix=R/'experiments/wbuart_width_frames_v2_2026-10-20/verification.json';independent=matrix.with_name('independent_verification_v1.json');v=read(matrix);iv=read(independent);assert len(v['rows'])==len(iv['rows'])==12
 for d in [v,iv]:
  assert all(sha(p)==h for p,h in d['bindings'].items())
 primary_root=R/'experiments/prospective_external_family_raw_floors_v1_2026-10-19';primary=primary_root/'rr_floor';ip=read(primary_root/'input_receipt.json');assert ip['bindings'][str(primary)]==sha(primary)
 contract=R/'experiments/graph_raw_floor_cache_contract_v1_2026-10-19/verification.json';cv=read(contract);assert all(sha(p)==h for p,h in cv['bindings'].items());verifier_source=R/'tools/verify_external_raw_floor_distances_v2.cpp';verifier=root/'forward_verifier';build=['/usr/bin/c++','-std=c++17','-O3',str(verifier_source),'-o',str(verifier)]
 bindings={str(p):sha(p) for p in [matrix,independent,primary_root/'input_receipt.json',primary,contract,verifier_source,R/'tools/graph_raw_floor_cache_v1.py',Path(__file__).resolve()]}
 (root/'protocol.json').write_text(json.dumps(dict(bindings=bindings,build_command=build,objective=VERSION,policy='All12 frozen wbuart routing views; all2493 CIDs per frame, full_connection_id preserved. Fresh graph-affine cache with NO cross-family floor imports. Exact key(graph SHA,SOURCE RR,SINK RR,objective version); raw costs only. Missing pairs reverse heap-Dijkstra then independent forward ordered-set Dijkstra before admission. Every physical path rechecked. No timing/price/history/budget/route labels used.',scope='Input preparation only; cache reuse records per-graph verified origin proofs; all graph/setup/search/audit/import costs remain paid, no quality or full-flow benefit claim.'),indent=2));run(build,root/'build.log');cache=Cache();origin_proofs={};rows=[];currentwidth=None;g=None
 for item in v['rows']:
  fp=Path(item['verification']);assert sha(fp)==item['sha256'];frame=read(fp);assert all(sha(p)==h for p,h in frame['bindings'].items());case=f"w{frame['width']:03d}/{frame['frame']}";ep=fp.parent/'routing_endpoints.json';e=read(ep);frame=dict(frame,case=case,endpoint=str(ep),graph=e['inputs']['graph']['path']);d=root/case;d.mkdir(parents=True);start=time.perf_counter();qs=e['connections'];assert len(qs)==2493 and e['graph_sha256']==frame['graph_sha256']
  if frame['width']!=currentwidth:
   currentwidth=frame['width'];gd=root/f'w{currentwidth:03d}'/'graph';gd.mkdir();g=setup_graph(frame,gd)
  assert g['hash']==frame['graph_sha256'];missing=defaultdict(list);priorhits=0;priororigins=set()
  for q in qs:
   s,t=q['source'],q['sink'];assert g['kinds'][s]=='SOURCE' and g['kinds'][t]=='SINK';entry=cache.get(g['hash'],s,t)
   if entry is None:missing[s,t].append(q['connection_id'])
   else:priorhits+=1;priororigins.add(entry.origin)
  pairs=sorted(missing);newconnections=sum(len(ids) for ids in missing.values());assert priorhits+newconnections==len(qs);missfile=d/'new_queries.json';missfile.write_text(json.dumps([dict(query_index=i,source=s,sink=t,current_CIDs=missing[s,t]) for i,(s,t) in enumerate(pairs)],indent=2));search_seconds=0;independent_seconds=0
  if pairs:
   binary=d/'reverse_queries.bin'
   with binary.open('xb') as f,g['static'].open('rb') as static:
    f.write(struct.pack('=4Q',0x5243464c4f4f5231,g['n'],g['m'],len(pairs)));shutil.copyfileobj(static,f)
    for i,(s,t) in enumerate(pairs):f.write(struct.pack('=3Q',i,t,s))
   tick=time.perf_counter();run([primary,binary],d/'new_reverse_results.jsonl',d/'primary_stderr.log');search_seconds=time.perf_counter()-tick;raw={a['connection_id']:a for a in map(json.loads,(d/'new_reverse_results.jsonl').open())};assert set(raw)==set(range(len(pairs)));expected=d/'new_expected_minima.txt';pending=[]
   with expected.open('x') as f:
    for i,(s,t) in enumerate(pairs):
     a=raw[i];minimum=a['minimum_integer'];edges=None if a['slots'] is None else tuple(g['physical'][slot] for slot in reversed(a['slots']));assert (minimum is None)==(edges is None);f.write(f'{i} {INF if minimum is None else minimum}\n');pending.append((s,t,minimum,edges))
   tick=time.perf_counter();run([verifier,binary,expected],d/'independent_forward.log');independent_seconds=time.perf_counter()-tick;assert f'FORWARD_SET_DIJKSTRA_ALL_FLOORS_PASS {len(pairs)} ' in (d/'independent_forward.log').read_text()
   for s,t,minimum,edges in pending:cache.put(g['hash'],s,t,minimum,edges,case)
  output=d/'floors.jsonl';path_edges=0;unreachable=0
  with output.open('x') as f:
   for q in qs:
    entry=cache.get(g['hash'],q['source'],q['sink']);assert entry is not None;path_edges+=check_path(g,q['source'],q['sink'],entry);unreachable+=entry.minimum is None;f.write(json.dumps(dict(q,minimum_integer=entry.minimum,physical_edge_ids=entry.edges,origin_case=entry.origin),separators=(',',':'))+'\n')
  assert not list(d.glob('*.route'));proof=d/'verification.json';files=[root/'protocol.json',fp,ep,Path(frame['graph']),g['proof'],missfile,output];files += [origin_proofs[o] for o in sorted(priororigins)];files += [d/'reverse_queries.bin',d/'new_reverse_results.jsonl',d/'new_expected_minima.txt',d/'independent_forward.log'] if pairs else [];record=dict(status='ALL_FRAME_RAW_FLOORS_ORIGIN_PROOFS_NEW_MINIMA_AND_CURRENT_XML_PATHS_VERIFIED',case=case,graph_sha256=g['hash'],objective=VERSION,connections=len(qs),prior_verified_origin_connection_hits=priorhits,new_query_connections=newconnections,new_unique_queries=len(pairs),unreachable=unreachable,physical_path_edges_checked=path_edges,new_primary_seconds=search_seconds,new_independent_minima_seconds=independent_seconds,whole_frame_component_seconds=time.perf_counter()-start,origin_cases=sorted(priororigins),bindings={str(p):sha(p) for p in files},scope='Per-connection raw minimum only, not a shared-NET tree, congestion legality, timing budget or forecast. Null unreachable rows retained and independently checked with infinity sentinel.');proof.write_text(json.dumps(record,indent=2));origin_proofs[case]=proof;rows.append(dict(case=case,verification=str(proof),sha256=sha(proof),connections=len(qs),prior_verified_origin_connection_hits=priorhits,new_unique_queries=len(pairs),unreachable=unreachable));(root/'progress.json').write_text(json.dumps(dict(rows=rows,cache_entries=len(cache)),indent=2));print('FRAME_RAW_FLOORS_VERIFIED',case,'hits',priorhits,'new',len(pairs),'unreachable',unreachable,flush=True)
 assert len(rows)==12 and all(sha(p)==h for p,h in bindings.items());(root/'verification.json').write_text(json.dumps(dict(status='ALL12_RAW_FLOOR_DOMAINS_COMPLETE_CACHE_ORIGINS_NEW_MINIMA_AND_PHYSICAL_WITNESSES_VERIFIED',rows=rows,cache_entries=len(cache),connections_admitted=sum(r['connections'] for r in rows),new_unique_queries=sum(r['new_unique_queries'] for r in rows),prior_verified_origin_connection_hits=sum(r['prior_verified_origin_connection_hits'] for r in rows),bindings={str(p):sha(p) for p in [root/'protocol.json',root/'build.log',verifier,*[Path(r['verification']) for r in rows]]},paid_import_dependency=None,no_budget_assigned=True,no_native_route_labels=True,strict_unseen_admitted=False,scope='Wbuart raw-floor input preparation only, no cross-family floor import. All graph namespaces distinct; no full-model or matched full-flow speed/quality result.'),indent=2))
if __name__=='__main__':main()
