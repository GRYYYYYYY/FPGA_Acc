import json,sys
from pathlib import Path
from collections import Counter
R=Path.cwd();sys.path.insert(0,str(R/'tools'))
from pre_route_endpoints import sha
out=R/'experiments/aes_native_demand_frontend_v1_2026-10-08';receipt=out/'receipt.json';d=json.loads(receipt.read_text());assert all(sha(k)==v for k,v in d['bindings'].items());bindings={str(receipt):sha(receipt),str(Path(__file__)):sha(Path(__file__))};rows=[]
for row in d['rows']:
 assert all(sha(k)==v for k,v in row['files'].items());w=out/row['name'];all_ep=json.loads((w/'all_endpoints.json').read_text());physical=json.loads((w/'endpoints.json').read_text());part=json.loads((w/'scope_partition.json').read_text());original={q['connection_id']:q for q in all_ep['connections']};assert set(original)==set(range(len(original)));table=Path(physical['inputs']['native_identity']['path']);ids={x['name']:x for x in map(json.loads,table.read_text().splitlines())};expect=[];excluded=[]
 for cid,q in sorted(original.items()):
  n=all_ep['net_names'][str(q['net_id'])];assert n in ids
  if ids[n]['ignored']:excluded.append(cid)
  else:expect.append(cid)
 assert [x['original_connection_id'] for x in part['physical_to_original_connection_ids']]==expect;assert [x['physical_connection_id'] for x in part['physical_to_original_connection_ids']]==list(range(len(expect)));assert [x['original_query']['connection_id'] for x in part['native_ignored_queries']]==excluded
 for newcid,oldcid in enumerate(expect):assert physical['connections'][newcid]=={**original[oldcid],'connection_id':newcid}
 for record,cid in zip(part['native_ignored_queries'],excluded):assert record['original_query']==original[cid] and record['native_net_id']==ids[record['net_name']]['net_id'] and ids[record['net_name']]['ignored']
 assert not set(expect)&set(excluded) and set(expect)|set(excluded)==set(original)
 original_groups=Counter(q['net_id'] for q in original.values());physical_groups=Counter(q['net_id'] for q in physical['connections']);assert all(count==original_groups[n] for n,count in physical_groups.items())
 assert all_ep['graph_sha256']==physical['graph_sha256'];assert all(sha(v['path'])==v['sha256'] for v in physical['inputs'].values());bindings.update(row['files']);bindings[str(table)]=sha(table);rows.append({'name':row['name'],'original_queries':len(original),'physical_queries':len(expect),'ignored_queries':len(excluded),'exhaustive_disjoint_partition_exact_original_queries_and_whole_NET_scope_pass':True})
assert all(sha(k)==v for k,v in bindings.items());(out/'verification.json').write_text(json.dumps({'bindings':bindings,'rows':rows},indent=2)+'\n');print(rows)
