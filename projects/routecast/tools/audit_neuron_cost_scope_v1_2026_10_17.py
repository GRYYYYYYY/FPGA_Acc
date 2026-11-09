"""Authenticate cross-run clocks without constructing a fictitious full workflow."""
import json,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];D=R/'experiments/neuron_cost_scope_v1_2026-10-17';D.mkdir(exist_ok=False)
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
bindings={str(Path(__file__).resolve()):sha(__file__)}
def load(p):bindings[str(p)]=sha(p);return json.loads(p.read_text())
n=R/'experiments/titan23_neuron_native_cold_label_v1_2026-10-14';m=R/'experiments/neuron_proxy_budget_trial_v2_2026-10-17'
a=load(R/'experiments/neuron_certified_native_metrics_v1_2026-10-15/label_admission.json');assert a['label_accepted']
terminal=load(n/'terminal.json');assert sha(n/'terminal.json')==a['bindings'][str(n/'terminal.json')] and terminal['exit_status']==0
process=load(n/'process.json');frozen=load(R/'experiments/titan23_neuron_native_label_prereg_v2_2026-10-13/protocol.json');assert process['args']==frozen['native_command']
launch=load(n/'launch.json');assert launch['command']==process['args'] and sha(n/'launch.json')==a['bindings'][str(n/'launch.json')]
for name in ['native.log','output.route']:
 assert sha(n/name)==a['bindings'][str(n/name)];bindings[str(n/name)]=sha(n/name)
closed=load(m/'research_decision_v1.json');assert closed['full_trial_complete'] and closed['all_three_audits_closed_admission_all8_metrics_pass']
mt=load(m/'model_terminal.json');assert sha(m/'model_terminal.json')==closed['bindings'][str(m/'model_terminal.json')] and mt['exit_status']==0
receipt=load(m/'model/receipt.json');protocol=load(m/'model/protocol.json')
epfile=R/'experiments/titan23_neuron_native_demand_v1_2026-10-13/demand/endpoints.json';ep=load(epfile);assert sha(epfile)==protocol['bindings'][str(epfile)]
inputs=load(n/'input_bindings.json')
for key in ['graph','net','place']:
 spec=ep['inputs'][key];assert sha(spec['path'])==spec['sha256']==inputs['original'][spec['path']];bindings[spec['path']]=spec['sha256']
assert abs(receipt['model_setup_seconds']+receipt['initial_seconds']+receipt['feedback_seconds']-receipt['total_paid_resident_seconds'])<1
out=dict(bindings=bindings,matched_original_graph_net_placement=True,native_cold_process_seconds=terminal['seconds'],model_outer_process_seconds=mt['seconds'],model_inner_seconds=receipt['total_paid_resident_seconds'],model_disjoint_major_phases={k:receipt[k] for k in ['model_setup_seconds','initial_seconds','feedback_seconds']},nested_overlapping_model_clocks={k:receipt[k] for k in ['search_seconds','cpp_prepare_seconds','occupancy_context_seconds','fallback_seconds','ledger_check_seconds']},external_model_audits={k:closed['costs'][k] for k in ['initial_audit','sketch_audit','event_audit']},scope='Different dates, independently measured runs. No paired speedup, full workflow sum, attribution to host conditions or actual break-even. Native timing excludes physical/canonical label validation; model inner phases contain nested search/setup/cache costs.',next_action='Pilot exact raw-only quotient A* for initial floors, reusing the already-built static lower graph. First verify randomized multi-target prefixes and every2450XTEA floor against archived independent exact floors; record tie-path changes and full physical path/single-parent consistency. Do not launch large neuron run or claim speedup before correctness and component cost gates.')
with (D/'verification.json').open('x') as f:json.dump(out,f,indent=2);f.write('\n')
print(json.dumps({k:v for k,v in out.items() if k!='bindings'},indent=2))
