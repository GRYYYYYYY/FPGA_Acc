"""Independent history recurrence and complete proposal union coverage."""
import sys,json,hashlib
from pathlib import Path
from collections import Counter,defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from nonzero_rc_endpoint_context import load_endpoints
out=R/'experiments/misex_net466_extra_owner_joint_v17_2026-10-07';r=json.loads((out/'receipt.json').read_text());e=json.loads((out/'event.json').read_text());bindings={**r['bindings'],**r['files'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json')};assert all(sha(p)==h for p,h in bindings.items())
_,_,nodes,f,rc,_=load_endpoints(R/'experiments/mcnc_prospective_v1_2026-10-07/misex3/endpoints.json');slots={edge:i for i,edge in enumerate(f['edge_ids'])};spans=[1+int(n.find('loc').get('xhigh'))-int(n.find('loc').get('xlow'))+int(n.find('loc').get('yhigh'))-int(n.find('loc').get('ylow')) if n.get('type') in ('CHANX','CHANY') else 0 for n in nodes];checked=0
for a in r['attempts']:
 history=Counter();release=set(a['release']);kept={rec['connection_id']:rec for rec in e['before_records'] if rec['net_id'] not in release};nets=sorted(release|{q['net_id'] for q in e['selection']['queries']});expected=set(kept)|{rec['connection_id'] for rec in e['before_records'] if rec['net_id'] in release}|set(e['selection']['requested_connection_ids']);assert len(a['branches'])<=32
 for i,b in enumerate(a['branches']):
  assert b['index']==i and b['constraints']==[];weighted=[span+8*history[n] for n,span in enumerate(spans)];assert b['history_price_sha256']==hashlib.sha256(','.join(map(str,weighted)).encode()).hexdigest();merged=dict(kept);seen=[];failed=False;d=out/f"attempt{a['index']}_branch{i}"
  for net in nets:
   p=d/f'net{net}.json';assert sha(p)==r['files'][str(p)];s=json.loads(p.read_text());assert s['failure']==b['failures'][str(net)];records={rec['connection_id']:rec for rec in s['records']};assert all(records[cid]==rec for cid,rec in kept.items());seen.append(net)
   if s['failure'] is not None:failed=True;break
   required={rec['connection_id'] for rec in e['before_records'] if rec['net_id']==net}|{q['connection_id'] for q in e['selection']['queries'] if q['net_id']==net};assert set(records)==set(kept)|required
   for cid,rec in records.items():
    if cid in merged:assert merged[cid]==rec
    else:merged[cid]=rec
  assert set(map(int,b['failures']))==set(seen);assert {p.name for p in d.glob('net*.json')}=={f'net{net}.json' for net in seen}
  if failed:assert b['status']=='LOW_LEVEL_FAILED' and i==len(a['branches'])-1
  else:
   assert set(merged)==expected;owners=defaultdict(set)
   for rec in merged.values():owners[rec['net_id']].add(rec['source']);owners[rec['net_id']].update(f['dest_ranks'][slots[edge]] for edge in rec['answer']['physical_edge_ids'])
   ledger=Counter(n for own in owners.values() for n in own);overuse={n:c-f['capacities'][n] for n,c in ledger.items() if c>f['capacities'][n]};assert b['overuse_by_node']=={str(n):v for n,v in sorted(overuse.items())};assert b['conflict_count']==len(overuse);assert b['status']==('NEGOTIATED_OVERUSE' if overuse else 'FOUND_JOINT_BATCH');history.update(overuse)
  checked+=1
 if a['status']=='SEARCH_EXHAUSTED':assert len(a['branches'])==32
assert all(sha(p)==h for p,h in bindings.items());(out/'negotiated_history_verification.json').write_text(json.dumps(dict(bindings=bindings,rounds_verified=checked,scope='Exact soft history recurrence and complete whole-NET proposal unions; physical/budget proof separate, no native/full-workflow claim.'),indent=2)+'\n');print('PASS negotiated history',checked)
