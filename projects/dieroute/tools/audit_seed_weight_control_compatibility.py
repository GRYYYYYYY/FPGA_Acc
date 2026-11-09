"""Compare completed weight128 runs with the frozen fanout serial parent."""
import hashlib
import json
from pathlib import Path

root=Path(__file__).resolve().parents[1]
parent=root/'work/rr_fanout_net_order_variant_20261015/native_runs/fanout_serial_0'
candidate=root/'work/rr_fanout_seed_weight_variant_v2_20261015'
manifest=json.loads((candidate/'native_manifest.json').read_text())
completed={s['label'] for s in manifest['steps'] if s['status']=='passed'}
source_hashes={}
def sha(p):
 h=hashlib.sha256(p.read_bytes()).hexdigest();source_hashes[str(p)]=h;return h
records=[]
for i in range(5):
 label=f'weight128_{i}'
 if label not in completed:continue
 d=candidate/'native_runs'/label
 left={p.name:p for p in parent.glob('route.*')}
 right={p.name:p for p in d.glob('route.*')}
 assert left.keys()==right.keys(),label
 checks=[]
 for name,a in sorted(left.items()):
  b=right[name];ah,bh=sha(a),sha(b)
  if name=='route.json':
   x,y=json.loads(a.read_text()),json.loads(b.read_text())
   x.pop('wall_ms');y.pop('wall_ms');assert x==y,label
  else:assert ah==bh,(label,name)
  checks.append(dict(name=name,parent_sha256=ah,control_sha256=bh))
 records.append(dict(label=label,checks=checks))
assert records
sha(Path(__file__).resolve())
out=candidate/f'control_parent_review_{len(records)}_completed.json'
with out.open('x') as stream:
 json.dump(dict(status='completed_weight128_controls_match_frozen_fanout_serial',runs=records,
               source_sha256=source_hashes,
               scope='Snapshot of completed weight128 routes, all route-prefix files exact except JSON wall_ms. Does not certify incomplete repetitions, weight256, native quality or failed-v2 replay correction.',board_result=False,research_complete=False),stream,indent=2)
 stream.write('\n')
print(json.dumps(dict(runs=len(records),checks=sum(len(r['checks']) for r in records))))
