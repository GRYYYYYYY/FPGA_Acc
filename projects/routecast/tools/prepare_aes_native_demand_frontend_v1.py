"""Fresh extraction with authenticated native ignored flags; all source queries accounted."""
import json,sys,copy
from pathlib import Path
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha,extract
from source_binding_v2 import closure
out=R/'experiments/aes_native_demand_frontend_v1_2026-10-08';out.mkdir();receipt=R/'experiments/aes_ignored_identity_v1_2026-10-08/receipt.json';data=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in data['bindings'].items());bindings={**closure([Path(__file__)]),str(receipt):sha(receipt)};rows=[]
(out/'protocol.json').write_text(json.dumps({'bindings':bindings,'policy':'Fresh original packed NET/place/RR extraction, original root-clock policy; all original connections saved. Native physical scope excludes exactly actual native ignored NETs by frozen pre-route identity. Physical CIDs contiguous with explicit original CID mapping. No name-based constant assumption or endpoint-only sink dropping. Graph semantics and fixed 50ps span/two rounds/exact RC budget model unchanged. Old all-query experiment remains immutable. Corrected-scope diagnostic study, previously observed family, no unseen-family claim.'},indent=2)+'\n')
for name in ['aes_cipher','aes_inv_cipher']:
 w=out/name;w.mkdir();old=R/f'experiments/aes_rr_graph_only_v1_2026-10-08/{name}/endpoints.json';reference=json.loads(old.read_text());ep,mapping=extract(*(Path(reference['inputs'][k]['path']) for k in ['net','place','graph']));assert ep['connections']==reference['connections'];(w/'all_endpoints.json').write_text(json.dumps(ep)+'\n');(w/'mapping.json').write_text(json.dumps(mapping)+'\n')
 table=receipt.parent/name/'identity.jsonl';native=[json.loads(x) for x in table.read_text().splitlines()];assert sha(table)==next(x for x in data['results'] if x['name']==name)['identity_sha256'];lookup={x['name']:x for x in native};assert len(lookup)==len(native);physical=[];ignored=[];cids=[]
 for q in ep['connections']:
  net=ep['net_names'][str(q['net_id'])];assert net in lookup
  if lookup[net]['ignored']:ignored.append({'original_query':q,'net_name':net,'native_net_id':lookup[net]['net_id'],'reason':'actual_native_net_is_ignored_before_route'})
  else:cids.append({'physical_connection_id':len(physical),'original_connection_id':q['connection_id']});physical.append({**q,'connection_id':len(physical)})
 result=copy.deepcopy(ep);result['connections']=physical;result['native_demand_policy']='exclude_authenticated_native_ignored_NETs_v1';result['inputs']['native_identity']={'path':str(table),'sha256':sha(table)};result['inputs']['all_endpoints']={'path':str(w/'all_endpoints.json'),'sha256':sha(w/'all_endpoints.json')};result['original_connection_count']=len(ep['connections']);result['native_ignored_connection_count']=len(ignored);(w/'endpoints.json').write_text(json.dumps(result)+'\n');(w/'scope_partition.json').write_text(json.dumps({'physical_to_original_connection_ids':cids,'native_ignored_queries':ignored,'all_query_count':len(ep['connections'])})+'\n');assert len(physical)+len(ignored)==len(ep['connections'])
 for p in [old,table]:bindings[str(p)]=sha(p)
 bindings.update({v['path']:v['sha256'] for v in ep['inputs'].values()});rows.append({'name':name,'all_queries':len(ep['connections']),'physical_queries':len(physical),'ignored_queries':len(ignored),'files':{str(p):sha(p) for p in w.iterdir() if p.is_file()}})
assert all(sha(k)==v for k,v in bindings.items());(out/'receipt.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n');print(rows)
