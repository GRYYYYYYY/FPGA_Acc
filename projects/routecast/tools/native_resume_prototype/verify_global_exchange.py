"""Replay branch paths, union budgets, parents and combined node ownership."""
import json,sys,xml.etree.ElementTree as ET
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from native_route_ledger_import_compact import physical_paths
ROOT=Path(__file__).resolve().parents[2];w,i=map(int,sys.argv[1:]);d=ROOT/f'experiments/native_resume_global_exchange_delay_0.01_w{w}_m{i}_2026-10-07';r=json.loads((d/'receipt.json').read_text());p=json.loads((d/'protocol.json').read_text());assert r['protocol_sha256']==sha(d/'protocol.json');assert all(sha(f)==h for f,h in p['inputs'].items());ep=ROOT/f'experiments/mux_budget_move_cohort_2026-10-06/w{w}_m{i}/target_endpoints.json';meta=json.loads(ep.read_text());graph,digest,nodes,f,rc,queries=load_endpoints(ep);edges={f['edge_ids'][slot]:(u,f['dest_ranks'][slot],f['switch_ids'][slot]) for u in range(len(nodes)) for slot in range(f['row_offsets'][u],f['row_offsets'][u+1])};old=physical_paths(ROOT/f'experiments/native_resume_singlepass_floor_w{w}_m{i}_workflow_2026-10-07/canonical/design.route');owners={name:{n for path in ps for n,_ in path} for name,ps in old.items() if ps};original_occ=Counter(n for ns in owners.values() for n in ns);span={}
for _,node in ET.iterparse(graph,events=('end',)):
 if node.tag=='node':
  if node.get('type') in ('CHANX','CHANY'):
   loc=node.find('loc');span[int(node.get('id'))]=1+int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))
  node.clear()
count=0
for row in r['rows']:
 name=row['net'];expected={q['connection_id']:q for q in queries if meta['net_names'][str(q['net_id'])]==name};assert {x['query']['connection_id'] for x in row['records']}==set(expected);union=set();parents={}
 for record in row['records']:
  q=record['query'];assert q==expected[q['connection_id']];node=q['source'];union.add(node)
  for eid in record['physical_edge_ids']:
   u,v,sw=edges[eid];assert u==node;assert v not in parents or parents[v]==(u,sw);parents[v]=(u,sw);node=v;union.add(v)
  assert node==q['sink'];delay=rc.path(q['source'],q['sink'],record['physical_edge_ids']);assert delay==record['conditional_integer']<=record['current_path_additive_integer'];count+=1
 assert union==set(row['new_union']);assert sum(span.get(n,0) for n in owners[name])==row['old_wire'];assert sum(span.get(n,0) for n in union)==row['new_wire']<=row['old_wire'];assert all(v<=f['capacities'][n] for n,v in Counter(n for ns in {**owners,name:union}.values() for n in ns).items())
 owners[name]=union
occ=Counter(n for ns in owners.values() for n in ns);overflow=sum(max(0,v-f['capacities'][n]) for n,v in occ.items());assert overflow==0;assert all(sha(f)==h for f,h in p['inputs'].items());(d/'verification.json').write_text(json.dumps(dict(receipt_sha256=sha(d/'receipt.json'),simultaneous_replacement_overflow=overflow,connections=count,wire_budget_pass=True,paths_and_parents_verified=True,scope='Physical edge and additive delay replay; independent union span and combined occupancy. Shared RC loader; not optimality or native FULL/STA.'),indent=2)+'\n');print(w,count,'verified')
