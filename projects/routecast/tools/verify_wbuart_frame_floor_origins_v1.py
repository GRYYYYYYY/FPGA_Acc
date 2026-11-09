"""Independent per-CID cache-origin graph/objective/value/witness lineage audit."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from graph_raw_floor_cache_v1 import VERSION
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def table(p,graph):
 result={}
 for a in map(json.loads,Path(p).open()):
  key=(graph,a['source'],a['sink'],VERSION);value=(a['minimum_integer'],None if a['physical_edge_ids'] is None else tuple(a['physical_edge_ids']))
  if key in result:assert result[key]==value
  result[key]=value
 return result

def main():
 root=R/'experiments/wbuart_frame_raw_floors_v1_2026-10-20';vp=root/'verification.json';v=read(vp);assert len(v['rows'])==12 and all(sha(p)==h for p,h in v['bindings'].items());matrix=R/'experiments/wbuart_width_frames_v2_2026-10-20/verification.json';frames={f"w{row['width']:03d}/{row['frame']}":dict(read(Path(row['verification'])),endpoint=str(Path(row['verification']).parent/'routing_endpoints.json')) for row in read(matrix)['rows']};assert set(frames)=={row['case'] for row in v['rows']};origins={};order={};count=0;prior_count=0;selfkeys=0;rows=[]
 for ordinal,item in enumerate(v['rows']):
  case=item['case'];p=Path(item['verification']);assert sha(p)==item['sha256'];proof=read(p);assert proof['objective']==VERSION and all(sha(f)==h for f,h in proof['bindings'].items());frame=frames[case];graph=frame['graph_sha256'];ep=Path(frame['endpoint']);queries={q['connection_id']:q for q in read(ep)['connections']};source=p.parent/'floors.jsonl';local=table(source,graph);origins[case]=local;order[case]=ordinal;seen=set();newkeys=set();prior=0;selfconnections=0
  for a in map(json.loads,source.open()):
   cid=a['connection_id'];assert cid in queries and cid not in seen;seen.add(cid);q=queries[cid];assert all(a[k]==val for k,val in q.items());origin=a['origin_case'];assert origin in origins;key=(graph,a['source'],a['sink'],VERSION);value=(a['minimum_integer'],None if a['physical_edge_ids'] is None else tuple(a['physical_edge_ids']));assert key in origins[origin] and origins[origin][key]==value
   if origin==case:newkeys.add(key);selfconnections+=1
   else:assert order[origin]<ordinal;prior+=1
  assert seen==set(queries) and len(seen)==2493;new=read(p.parent/'new_queries.json');expectedkeys={(graph,q['source'],q['sink'],VERSION) for q in new};assert newkeys==expectedkeys and len(new)==proof['new_unique_queries'];assert prior==proof['prior_verified_origin_connection_hits'] and selfconnections==proof['new_query_connections'];count+=len(seen);prior_count+=prior;selfkeys+=len(newkeys);rows.append(dict(case=case,complete_CIDs=len(seen),prior_origin_connections=prior,new_origin_connections=selfconnections,new_unique_minima=len(newkeys)));print('FLOOR_CACHE_ORIGINS_PASS',case,prior,len(newkeys),flush=True)
 assert count==29916 and prior_count==v['prior_verified_origin_connection_hits'] and selfkeys==v['new_unique_queries'];paths=[vp,matrix,Path(__file__).resolve(),R/'tools/graph_raw_floor_cache_v1.py']
 with (root/'independent_cache_origin_verification_v1.json').open('x') as f:json.dump(dict(status='ALL29916_CURRENT_CIDS_GRAPH_OBJECTIVE_MINIMA_WITNESSES_AND_ACYCLIC_CACHE_ORIGINS_VERIFIED',rows=rows,connections=count,prior_origin_connection_hits=prior_count,new_unique_queries=selfkeys,bindings={str(p):sha(p) for p in paths},scope='Independent immutable cache-lineage/value/path-identity accounting; new-distance and original XML witness proofs remain bound separately. Fresh per-graph cache, no cross-family imports; all source floor costs remain paid. Not a prediction, common NET tree, legal global route or full-workflow speed result.'),f,indent=2)
 print('ALL_FRAME_FLOOR_CACHE_ORIGINS_PASS',count,prior_count,selfkeys)
if __name__=='__main__':main()
