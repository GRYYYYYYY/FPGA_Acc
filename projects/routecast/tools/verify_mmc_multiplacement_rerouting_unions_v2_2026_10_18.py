"""Independent token NET-union lower bounds on global native rerouting."""
import json,sys
from pathlib import Path
from collections import Counter
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));sys.path.insert(0,str(R/'tools/native_resume_prototype'))
from pre_route_endpoints import sha
from source_binding_v2 import closure
D=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18';rp=D/'global_rerouting_diagnostic_v1.json';r=json.loads(rp.read_text());bindings={**r['bindings'],**closure([Path(__file__)]),str(rp):sha(rp)};assert all(sha(p)==h for p,h in bindings.items())
g=json.loads((R/'experiments/mmc_native_state_geometry_v1_2026-10-18/protocol.json').read_text());oldmeta=json.loads(Path(g['previous_endpoint']).read_text());wanted={oldmeta['net_names'][str(q['net_id'])] for q in oldmeta['connections']}
def parse(path):
 unions={};current=None
 with Path(path).open() as f:
  for line in f:
   w=line.split()
   if w and w[0]=='Net':
    current=line.split('(',1)[1].rsplit(')',1)[0] if line.rstrip().endswith(')') else None
    if current is not None:assert current not in unions;unions[current]=set()
   elif w and w[0]=='Node:':
    assert current in wanted;unions[current].add(int(w[1]))
 assert set(unions)==wanted and len(unions)==55300
 return unions
old=parse(g['previous_native_route']);oldledger=Counter(n for nodes in old.values() for n in nodes);source=R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json';assert oldledger==Counter({int(n):v for n,v in json.loads(source.read_text())['ledger'].items()});rows=[]
for row in r['rows']:
 case=row['case'];I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case;ip=I/'staged_input_verification_v1.json';p=json.loads(ip.read_text());newmeta=json.loads((I/'demand/endpoints.json').read_text());dirty={newmeta['net_names'][str(n)] for n in p['affected']['affected_net_ids']};new=parse(D/case/'cold/output.route');proof=json.loads((D/case/'cold/physical_audit.json').read_text());ledger=Counter(n for nodes in new.values() for n in nodes);assert ledger==Counter({int(n):v for n,v in proof['node_occupancy'].items()});changed={n for n in old if old[n]!=new[n]};outside=changed-dirty
 assert len(changed)<=row['actual_changed_NETs'] and len(outside)<=row['changed_NETs_outside_dirty_NETs'];assert row['changed_NETs_outside_dirty_NETs']<=row['changed_paths_outside_dirty_NETs']
 rows.append(dict(case=case,independently_changed_NET_node_unions=len(changed),independently_changed_NET_unions_outside_endpoint_closure=len(outside),producer_exact_changed_NETs=row['actual_changed_NETs'],producer_exact_changed_NETs_outside_closure=row['changed_NETs_outside_dirty_NETs'],scope='NET node-union changes are an independent lower bound on physical-path-changing NETs, not an exact count of path-only changes.'))
 bindings[str(ip)]=sha(ip)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'rerouting_union_independent_verification_v2.json').open('x') as f:json.dump(dict(status='pass',bindings=bindings,rows=rows,all4_full_printed_NET_union_ledgers_equal_admitted_ledgers=True,scope='Independent NET token/name/node-set parse and closure lower-bound checks. Exact CID node/switch path counts rely on admitted physical paths and diagnostic parser; no causal or prediction quality claim.'),f,indent=2)
print('PASS independent global rerouting NET-union bounds',rows,flush=True)
