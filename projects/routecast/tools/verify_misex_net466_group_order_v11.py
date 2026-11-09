"""Independent full released-NET and selected scope plus floor ordering."""
import json,hashlib
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
out=R/'experiments/misex_net466_extra_owner_joint_v11_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());bindings={**r['bindings'],str(rp):sha(rp),str(Path(__file__).resolve()):sha(__file__)};ep=out/'event.json';fp=R/'experiments/mcnc_pending_swap_observer_clone_v21_2026-10-07/misex3/floors.json';bindings[str(ep)]=sha(ep);bindings[str(fp)]=sha(fp);assert all(sha(k)==v for k,v in bindings.items());event=json.loads(ep.read_text());floors={(x['source'],x['sink']):x['minimum_integer'] for x in json.loads(fp.read_text())};count=0
for a in r['attempts']:
 p=out/f"attempt{a['index']}_group_order.json";assert sha(p)==r['files'][str(p)];bindings[str(p)]=sha(p);saved=json.loads(p.read_text());expected=defaultdict(list)
 for q in event['selection']['queries']:expected[str(q['net_id'])].append(q)
 for rec in event['before_records']:
  if rec['net_id'] in a['release']:expected[str(rec['net_id'])].append({k:rec[k] for k in ('connection_id','net_id','source','sink')})
 for net,qs in expected.items():
  assert saved[net]==sorted(qs,key=lambda q:(-floors[(q['source'],q['sink'])],q['connection_id']));count+=len(qs)
 assert set(saved)==set(expected)
assert all(sha(k)==v for k,v in bindings.items());(out/'group_order_verification.json').write_text(json.dumps(dict(bindings=bindings,requests_verified=count,scope='Recorded full selected/released request ordering only; no completeness or QoR claim.'),indent=2)+'\n');print('PASS group order',count)
