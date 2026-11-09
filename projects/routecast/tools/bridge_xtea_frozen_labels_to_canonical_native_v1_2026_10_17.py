"""Connect unchanged frozen physical labels to newly canonical-audited cold route."""
import json,hashlib
from pathlib import Path
from audit_native_route import NET,NODE
R=Path(__file__).resolve().parents[1];D=R/'experiments/xtea_frozen_label_canonical_bridge_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
old=R/'experiments/freecores_native_cold_v1_2026-10-08/xtea';new=R/'experiments/xtea_proxy_budget_native_comparison_v1_2026-10-17';p=new/'verification.json';v=json.loads(p.read_text());assert v['all_three_native_physical_and_canonical_pass']
r=next(x for x in v['rows'] if x['arm']=='cold');c=r['canonical'];assert c['semantic_consistency_gate_pass'] and c['native_ignored_only_mismatch_pins']==26 and not c['original_zero_counter_gate_pass']
label=R/'experiments/freecores_hotspots_v1_2026-10-08/xtea/comparison.json';lp=json.loads(label.read_text());bindings={str(p):sha(p),str(label):sha(label),str(Path(__file__).resolve()):sha(__file__)}
for name in ['physical_audit.json','output.route']:
 a=old/name;b=new/'cold'/name
 assert sha(a)==lp['bindings'][str(a)] and sha(b)==v['bindings'][str(b)];bindings[str(a)]=sha(a);bindings[str(b)]=sha(b)
a=json.loads((old/'physical_audit.json').read_text());b=json.loads((new/'cold/physical_audit.json').read_text())
assert a['node_occupancy']==b['node_occupancy'] and a['connections']==b['connections'] and a['overflow_units']==b['overflow_units']==0
assert a['inputs_sha256']['graph']==b['inputs_sha256']['graph']
for name in ['design.blif','design.net','design.place']:
 x=old/name;y=new/'cold'/name;assert sha(x)==sha(y);bindings[str(x)]=sha(x);bindings[str(y)]=sha(y)
def sequences(path):
 result={};net=None
 for line in path.read_text().splitlines():
  m=NET.match(line)
  if m:net=m[2];assert net not in result;result[net]=[]
  m=NODE.match(line)
  if m:assert net is not None;result[net].append((int(m[1]),m[2],int(m[3])))
 return result
assert sequences(old/'output.route')==sequences(new/'cold/output.route')
q=R/'experiments/freecores_hotspots_v1_2026-10-08/xtea/comparison_vectors.json';vectors=json.loads(q.read_text());assert sha(q)==lp['bindings'][str(q)]
assert all(x['native']==b['node_occupancy'].get(str(x['node']),0) for x in vectors['channels']);bindings[str(q)]=sha(q)
with (D/'verification.json').open('x') as f:json.dump(dict(bindings=bindings,all_original_frozen_occupancies_connections_and_NET_node_type_switch_sequences_identical=True,original_blif_net_place_bytes_identical=True,all13216_original_channel_truth_values_identical=True,current_cold_canonical_ignored_only_semantic_gate_pass=True,original_zero_counter_gate_pass=False,ignored_pin_fixups=26,scope='No new labels or changed predictions. Historical canonical_reload_pass=false remains untouched. Exact bridge to the separately executed cold native FULL/physical/canonical ignored-pin semantic audit, not the stricter zero-counter gate, characterized CPD, heldout or full workflow gain.'),f,indent=2);f.write('\n')
print('PASS frozen XTEA labels match canonical-audited cold route exactly; original zero-counter gate remains false')
