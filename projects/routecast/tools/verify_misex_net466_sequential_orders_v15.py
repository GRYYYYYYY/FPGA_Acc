"""Independent bounded order coverage and exact earlier-tree preservation."""
import json,hashlib,sys
from collections import defaultdict,Counter
from pathlib import Path
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=R/'experiments/misex_net466_extra_owner_joint_v15_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());ep=out/'event.json';e=json.loads(ep.read_text());bindings={**r['bindings'],str(rp):sha(rp),str(ep):sha(ep),str(Path(__file__).resolve()):sha(__file__)};assert all(sha(k)==v for k,v in bindings.items());count=0
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from nonzero_rc_endpoint_context import load_endpoints
_,_,xmlnodes,fields,_,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json')
slots={edge:i for i,edge in enumerate(fields['edge_ids'])};original_nodes=defaultdict(set)
for rec in e['before_records']:original_nodes[rec['net_id']].add(rec['source']);original_nodes[rec['net_id']].update(fields['dest_ranks'][slots[edge]] for edge in rec['answer']['physical_edge_ids'])
spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in xmlnodes]
for attempt in r['attempts']:
 release=set(attempt['release']);kept=[rec for rec in e['before_records'] if rec['net_id'] not in release];nets=sorted(release|{q['net_id'] for q in e['selection']['queries']});orders=[]
 targets=sorted({q['net_id'] for q in e['selection']['queries']});others=sorted(set(nets)-set(targets))
 for index in range(64):
  ranked=sorted(others,key=lambda n:(hashlib.sha256(f'routecast-target-first-v1:{index}:{n}'.encode()).digest(),n));order=targets+ranked
  if order not in orders:orders.append(order)
 for i,b in enumerate(attempt['branches']):
  assert b['index']==i and b['net_order']==orders[i] and b['constraints']==[];seed={x['connection_id']:x for x in kept};directory=out/f"attempt{attempt['index']}_branch{i}";seen=[]
  for net in orders[i]:
   p=directory/f'net{net}.json';assert sha(p)==r['files'][str(p)];bindings[str(p)]=sha(p);s=json.loads(p.read_text());records={x['connection_id']:x for x in s['records']};assert all(records[cid]==rec for cid,rec in seed.items());assert b['failures'][str(net)]==s['failure'];seen.append(net);count+=1
   if net in b.get('warm_restored_nets',[]):
    original={x['connection_id']:x for x in e['before_records'] if x['net_id']==net};assert original and all(records[cid]==rec for cid,rec in original.items());assert s['failure'] is None
   else:
    future=orders[i][orders[i].index(net)+1:];pressure=Counter(node for owner in future for node in original_nodes[owner]);weighted=[span+32*pressure[node] for node,span in enumerate(spans)];assert b['reservation_pressure_sha256'][str(net)]==hashlib.sha256(','.join(map(str,weighted)).encode()).hexdigest()
   if s['failure'] is not None:break
   required={x['connection_id'] for x in e['before_records'] if x['net_id']==net}|{q['connection_id'] for q in e['selection']['queries'] if q['net_id']==net};assert set(records)==set(seed)|required;seed=records
  assert set(map(int,b['failures']))==set(seen);assert {p.name for p in directory.glob('net*.json')}=={f'net{n}.json' for n in seen}
 if attempt['status']=='SEARCH_EXHAUSTED':assert len(attempt['branches'])==len(orders)
assert all(sha(k)==v for k,v in bindings.items());(out/'sequential_order_verification.json').write_text(json.dumps(dict(bindings=bindings,net_states_verified=count,scope='Frozen SHA256-ranked target-first order prefixes, complete successful NET query sets, exact prior-tree preservation; no general complete permutation search.'),indent=2)+'\n');print('PASS sequential orders',count)
