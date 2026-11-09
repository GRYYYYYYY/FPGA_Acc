"""Authenticate full proof chain and compare complete native wire/printed CPD."""
import json,re,xml.etree.ElementTree as ET
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[1]
D=R/'experiments/raw_route_native_owner_candidate_v4_2026-10-08'
N=R/'experiments/native_owner_candidate_reload_v4_2026-10-08'
C=R/'experiments/native_owner_candidate_canonical_v4_2026-10-08'
B=R/'experiments/native_cold_branch_control_v8_2026-10-08'
bindings={str(Path(__file__)):sha(Path(__file__))}
proofs=[]
for path in (D/'verification.json',N/'verification.json',C/'verification.json'):
 p=json.loads(path.read_text());assert all(sha(f)==h for f,h in p['bindings'].items())
 bindings.update(p['bindings']);bindings[str(path)]=sha(path);proofs.append(p)
model,native,canonical=proofs
assert model['all1929_wire_events_answers_work_counts_and_full_state_equal']
assert not native['changed_physical_connection_ids'] and native['connections']==1929
assert canonical['all1929_paths_and_original_xml_physical_checks_pass'] and canonical['pin_mismatches']==canonical['trace_fixups']==0
assert model['original_budget_violation_ids']==native['budget_violation_connection_ids']==canonical['budget_violation_connection_ids']==[785,1637]
cr=json.loads((C/'receipt.json').read_text())['canonical'];graph=Path(cr['command'][cr['command'].index('--read_rr_graph')+1]);length={}
for node in ET.parse(graph).getroot().find('rr_nodes'):
 if node.get('type') in ('CHANX','CHANY'):
  loc=node.find('loc');length[int(node.get('id'))]=int(loc.get('xhigh'))-int(loc.get('xlow'))+int(loc.get('yhigh'))-int(loc.get('ylow'))+1
def metrics(route,log):
 paths=physical_paths(route);wire=sum(sum(length.get(n,0) for n in {n for path in branches for n,s in path}) for branches in paths.values())
 text=log.read_text();printed=int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1]);assert wire==printed
 cpd=F(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])
 assert 'Completed routing consistency check successfully.' in text and 'VPR succeeded' in text
 bindings[str(route)]=sha(route);bindings[str(log)]=sha(log)
 return wire,cpd
cold=json.loads((B/'receipt.json').read_text());assert cold['rows'][0]['exit_code']==0 and cold['protocol_sha256']==sha(B/'protocol.json')
assert cold['rows'][0]['route_sha256']==sha(B/'cold/output.route') and cold['rows'][0]['log_sha256']==sha(B/'cold/run.log')
wire,cpd=metrics(C/'canonical/design.route',C/'canonical/reload.log');coldwire,coldcpd=metrics(B/'cold/output.route',B/'cold/run.log')
assert wire==model['final_wire'] and cpd==F(str(canonical['cpd_ns']))
for path in (B/'receipt.json',B/'protocol.json',C/'receipt.json',graph):bindings[str(path)]=sha(path)
assert all(sha(f)==h for f,h in bindings.items())
report=dict(bindings=bindings,full_chain_pass=True,connections=1929,cpd_ns=str(cpd),wirelength=wire,cold_cpd_ns=str(coldcpd),cold_wirelength=coldwire,printed_cpd_nonregression=cpd<=coldcpd,wire_nonregression=wire<=coldwire,joint_quality_pass=cpd<=coldcpd and wire<=coldwire,budget_safe_connections=1927,initial_fixups=native['trace_fixups'],canonical_fixups=canonical['trace_fixups'],scope='Complete development-state native printed CPD/wire comparison only. Two original budget failures remain; original HDL equivalence, unseen-family validity and end-to-end time gain unproved.')
(N/'native_quality_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print({k:v for k,v in report.items() if k!='bindings'},flush=True)
