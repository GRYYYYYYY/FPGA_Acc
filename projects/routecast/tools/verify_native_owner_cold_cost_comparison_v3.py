"""Independent actual cold output authentication and honest observed fee comparison."""
import json,re
from fractions import Fraction as F
from pathlib import Path
from pre_route_endpoints import sha
from buffered_rc_node_classes import read as rc_read
from native_route_ledger_import_compact import physical_paths
from stream_native_route_audit_cached import audit
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'declared_input_cold_workflow_v1_2026-10-08';bindings={}
def read(path):
 obj=json.loads(path.read_text())
 for name,digest in obj.get('bindings',{}).items():
  assert sha(name)==digest,name
  assert name not in bindings or bindings[name]==digest
  bindings[name]=digest
 bindings[str(path)]=sha(path);return obj
r=read(D/'receipt.json');p=read(D/'protocol.json');assert sha(D/'protocol.json')==r['protocol_sha256']
assert r['exit_code']==0 and all(sha(path)==digest for path,digest in r['files'].items())
canonical=r['canonical'];assert canonical['exit_code']==0 and canonical['mismatches']==canonical['fixups']==0
assert all(sha(path)==digest for path,digest in canonical['files'].items())
graph=Path(p['command'][p['command'].index('--read_rr_graph')+1])
case=next(c for c in json.loads((E/'owner50_retained_rr_2026-10-07_predictor/protocol.json').read_text())['cases'] if c['width']==32 and c['index']==2)
ep=json.loads(Path(case['target']).read_text());b=json.loads(Path(case['budget']).read_text());ids,classes,switches,digest=rc_read(graph);assert digest==ep['graph_sha256']
paths={}
for name,branches in physical_paths(D/'cold/output.route').items():
 for branch in branches:
  key=name,branch[0][0],branch[-1][0];assert key not in paths;paths[key]=branch
rows=[]
for q in ep['connections']:
 cid=q['connection_id'];branch=paths[ep['net_names'][str(q['net_id'])],q['source'],q['sink']];nr,nc=classes[ids[q['source']]];delay=nr*nc/2
 for dst,s in branch[1:]:nr,nc=classes[ids[dst]];sr,td=switches[s];delay+=(sr+nr/2)*nc+td
 limit=F(b['budgets_ns'].get(str(cid),b['default_budget_ns']));rows.append(dict(connection_id=cid,delay_seconds=str(delay),budget_ns=str(limit),budget_pass=delay*10**9<=limit))
assert len(paths)==len(rows)==1929 and rows==json.loads((D/'fraction_budget_rows.json').read_text())
assert [row['connection_id'] for row in rows if not row['budget_pass']]==r['budget_violation_ids']
physical=audit(graph,D/'canonical/design.route');assert physical['overflow_units']==0 and len(physical['connections'])==1929
assert physical_paths(D/'canonical/design.route')==physical_paths(D/'cold/output.route')
text=(D/'cold/run.log').read_text();assert 'VPR succeeded' in text and 'ROUTECAST_RESUME_LOADED_TREES' not in text
assert F(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',text)[-1])==F(r['cold_cpd_ns'])
assert r['wirelength']==int(re.findall(r'Total wirelength:\s*(\d+)',text)[-1])
candidate=read(E/'old_route_native_owner_workflow_v3_2026-10-08/verification.json')
cp=read(E/'old_route_native_owner_workflow_v3_2026-10-08/protocol.json')
assert candidate['all_thirteen_measured_stages_terminal_zero']
for path,digest in p['common_cached_inputs'].items():assert cp['bindings'][path]==digest==sha(path)
assert sum(r['phases_seconds'].values())<=r['declared_input_workflow_seconds']
generation=sum(stage['elapsed_seconds'] for stage in candidate['stages'] if stage['script'] in ('trial_fresh_retained_branch_seed_v7.py','native_resume_prototype/trial_fresh_retained_branch_resume_v7.py','trial_raw_route_native_owner_candidate_v3.py'))
bindings.update(r['files']);bindings.update(canonical['files']);bindings[str(Path(__file__))]=sha(Path(__file__))
assert all(sha(path)==digest for path,digest in bindings.items())
out=dict(bindings=bindings,all1929_cold_fraction_budgets_and_canonical_physical_paths_pass=True,
 common_declared_input_bytes_equal=True,cold_declared_input_seconds=r['declared_input_workflow_seconds'],
 candidate_declared_input_seconds=candidate['declared_input_workflow_seconds'],
 observed_candidate_over_cold_ratio=candidate['declared_input_workflow_seconds']/r['declared_input_workflow_seconds'],
 candidate_seed_resume_and_generation_seconds=generation,
 observed_candidate_generation_alone_exceeds_cold_workflow=generation>r['declared_input_workflow_seconds'],
 cold_cpd_ns=r['cold_cpd_ns'],candidate_cpd_ns=candidate['cpd_ns'],cold_wirelength=r['wirelength'],candidate_wirelength=candidate['wirelength'],
 cold_budget_violation_ids=r['budget_violation_ids'],candidate_budget_violation_ids=candidate['original_budget_violation_ids'],
 all_original_budgets_admitted=False,observed_declared_boundary_time_gain=candidate['declared_input_workflow_seconds']<r['declared_input_workflow_seconds'],
 paired_speedup_proved=False,full_original_input_workflow_seconds=None,
 scope='Same declared supplied packed netlist/place/RR/endpoints/budget/model/old route bytes, actual native outputs and canonical physical/Fraction gates. Sequential single observations; candidate has additional development trace certificates and model stages, cold clocks omit initial imports/protocol and final receipt/this verifier. Shared cache generation/amortization and full original-input cold/candidate costs absent. Printed QoR improvement does not establish original-budget admission, original HDL equivalence, unseen-family or net time gain.')
output_directory=E/'native_owner_cold_cost_comparison_v3_2026-10-08';output_directory.mkdir(exist_ok=False)
(output_directory/'verification.json').write_text(json.dumps(out,indent=2)+'\n');print({k:v for k,v in out.items() if k!='bindings'},flush=True)
