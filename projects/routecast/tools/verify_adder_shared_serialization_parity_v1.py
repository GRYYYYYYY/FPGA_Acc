"""All4 full serialized-byte/pin identities against independently native-certified predecessor."""
import json
from pathlib import Path
from serialization_rr_inventory_v1 import SerializationInventory
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_multinet_wire_guard_shared_serialization_v1_2026-10-08';B=E/'adder_multinet_wire_guard_serialization_v2_2026-10-08'
v=json.loads((D/'verification.json').read_text());b=json.loads((B/'verification.json').read_text())
for doc in (v,b):assert all(sha(f)==h for f,h in doc['bindings'].items())
assert v['rows']==b['rows'] and len(v['rows'])==4
for step in range(4):
 for suffix in ('.route','_identity.jsonl'):assert (D/f'step_{step}{suffix}').read_bytes()==(B/f'step_{step}{suffix}').read_bytes()
ep=E/'adder_tree_family_endpoints_2026-10-06/adder_tree_2L_032bits/endpoints.json';m=json.loads(ep.read_text());g=m['inputs']['graph']['path'];inv=SerializationInventory(g,m['graph_sha256'])
try:inv.nodes[0][1]['ptc']='broken'
except TypeError:pass
else:raise AssertionError('Mutable site inventory')
try:inv.validate(g,'0'*64)
except ValueError:pass
else:raise AssertionError('Wrong epoch accepted')
report=dict(bindings={str(p):sha(p) for p in (D/'verification.json',B/'verification.json',Path(__file__),R/'tools/serialization_rr_inventory_v1.py')},all4_route_and_identity_bytes_equal=True,owned_node_sites_immutable=True,wrong_epoch_rejected=True,observed_shared_component_seconds=v['component_seconds'],scope='Complete4 serialized bytes/identity parity and all2064 paths verified in producer. Frozen predecessor native/canonical evidence applies to identical route bytes, no new native execution or paired wholeworkflow gain. Shared component includes cold XML inventory, all hash/serialization/path/physical checks; startup and initial baseline bindings outside.')
(D/'parity_verification.json').write_text(json.dumps(report,indent=2)+'\n');print(report['observed_shared_component_seconds'])
