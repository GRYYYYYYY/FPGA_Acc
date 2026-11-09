"""Authenticate original packed-netlist entry and freshly captured pin identity."""
import json
from pathlib import Path
from pre_route_endpoints import sha

R=Path(__file__).resolve().parents[1];E=R/'experiments'
D=E/'single_pass_candidate_reload_v1_2026-10-08'
p=json.loads((D/'protocol.json').read_text());r=json.loads((D/'receipt.json').read_text())
assert r['exit_code']==0 and r['full_consistency_pass'] and r['vpr_succeeded']
assert sha(D/'protocol.json')==r['protocol_sha256']
assert all(sha(path)==digest for path,digest in p['inputs'].items())
assert all(sha(path)==digest for path,digest in r['files'].items())
source=R/'work/mux_crossbar_channel_pressure_2026-10-06/mux_w32_c128'
place=E/'mux_budget_move_cohort_2026-10-06/w32_m2/target.place'
for name in ('design.blif','design.net'):assert sha(D/name)==sha(source/name)
assert sha(D/'design.place')==sha(place)
assert p['identity_exit_code']==1 and p['identity_command'][p['identity_command'].index('--route_file')+1]=='missing.route'
identity=D/'identity.jsonl'
assert str(identity) in p['inputs'] and identity.exists()
records=[json.loads(line) for line in identity.read_text().splitlines()]
assert records and len({record['net_id'] for record in records})==len(records)
dump=json.loads((D/'verification.json').read_text())
assert dump['connections']==1929 and dump['changed_physical_connection_ids']==[]
assert dump['budget_violation_connection_ids']==[785,1637]
canonical=E/'single_pass_candidate_canonical_v1_2026-10-08/verification.json'
c=json.loads(canonical.read_text());assert c['all1929_paths_and_original_xml_physical_checks_pass']
assert c['pin_mismatches']==c['trace_fixups']==0
quality_path=D/'native_quality_verification.json';q=json.loads(quality_path.read_text())
assert q['full_chain_pass'] and q['joint_quality_pass']
bindings={**p['inputs'],**dump['bindings'],**c['bindings'],**q['bindings'],
          str(D/'protocol.json'):sha(D/'protocol.json'),str(D/'receipt.json'):sha(D/'receipt.json'),
          str(canonical):sha(canonical),str(quality_path):sha(quality_path),str(Path(__file__)):sha(Path(__file__))}
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,original_packed_netlist_and_target_place_byte_identity_pass=True,
         pin_identity_freshly_captured_in_this_directory=True,
         all1929_postsync_paths_preserved=True,first_native_mismatches=dump['pin_mismatches'],
         first_native_fixups=dump['trace_fixups'],canonical_fixups=0,
         cpd_ns=q['cpd_ns'],wirelength=q['wirelength'],original_budget_violation_ids=[785,1637],
         scope='Actual native acceptance from original provided packed netlist and exact target placement with newly generated pin identity. Prior canonical packed netlist/place/identity not used as execution inputs; historical artifacts remain in authenticated development proof ancestry. No original HDL equivalence, full original-input clock, all-budget admission, paired or unseen-family gain claim. This one-shot adapter did not save its own wall clock.')
(D/'entry_verification.json').write_text(json.dumps(out,indent=2)+'\n')
print({k:v for k,v in out.items() if k!='bindings'},flush=True)
