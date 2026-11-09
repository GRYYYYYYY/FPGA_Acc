"""Transfer exact common-field audit scopes only through full snapshot projection identity."""
import json,itertools
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];A=R/'experiments/mmc_native_iteration_state_observer_v1_2026-10-10';B=R/'experiments/mmc_native_iteration_state_observer_v2_2026-10-10'
proofs=[A/'verification.json',A/'state_node_audit_v1.json',A/'tree_edge_audit_v1.json',A/'tree_delay_audit_v1.json',B/'verification.json'];bindings={};data={}
for p in proofs:
 v=json.loads(p.read_text());assert all(sha(n)==h for n,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p);data[p.name if p.parent==A else 'v2_trial']=v
assert data['v2_trial']['route_bytes_equal_fully_audited_cold']
assert data['state_node_audit_v1.json']['all21rounds_full_XML_capacity_and_float32_history_recurrence_pass']
assert data['tree_edge_audit_v1.json']['all21rounds_rooted_acyclic_parent_structure_and_original_XML_edge_switch_membership_pass']
assert data['tree_delay_audit_v1.json']['all21rounds_tree_delay_float32_recurrence_pass']
rows=[]
for iteration in range(1,22):
 count=0
 with (A/'states'/f'round_{iteration}.tsv').open() as a,(B/'states'/f'round_{iteration}.tsv').open() as b:
  for old,new in itertools.zip_longest(a,b):
   assert old is not None and new is not None
   x=old.split();y=new.split();assert (len(y)==len(x)+1 if x[0]=='T' else len(y)==len(x))
   assert x==(y[:-1] if x[0]=='T' else y),(iteration,count,'projection mismatch');count+=1
 rows.append({'iteration':iteration,'records':count});print('PROJECTION',iteration,count,flush=True)
assert (A/'criticality.tsv').read_bytes()==(B/'criticality.tsv').read_bytes()
bindings[str(Path(__file__).resolve())]=sha(Path(__file__));assert all(sha(n)==h for n,h in bindings.items())
f=B/'common_state_projection_verification_v1.json';assert not f.exists();f.write_text(json.dumps({'bindings':bindings,'all21rounds_common_state_fields_exactly_equal':True,'criticality_trace_bytes_equal':True,'rows':rows,'inherited_scopes':['full RR capacity/history recurrence','tree union occupancy diagnostic','rooted acyclic parent/XML edge-switch membership','zero-RC tree float32 delay recurrence'],'scope':'Exact full common-field projection to independently audited v1 states. Does not transfer new pin-index identity, extra ignored pin semantics, budgets, STA, native equivalence or quality.'},indent=2)+'\n')
