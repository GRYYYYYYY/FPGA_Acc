"""Authenticate isolated replay and report measured costs without acceleration claims."""
import hashlib,json,math
from pathlib import Path
root=Path(__file__).resolve().parents[1]
out=root/'experiments/ex5p_swapped_cost_replay_2026-10-06'
def digest(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p): return json.loads(Path(p).read_text())
p=read(out/'protocol.json');r=read(out/'receipt.json');replay=Path(p['replay_root'])
assert r['completed'] and len(r['stages'])==len(p['stages'])==15
assert digest(out/'protocol.json')==r['protocol_sha256']
assert digest(root/'tools/trial_ex5p_swapped_cost_replay.py')==r['source_sha256']
for path,h in p['fixed_inputs'].items(): assert digest(path)==h
costs={}
for i,(s,expected) in enumerate(zip(r['stages'],p['stages'])):
 assert s['index']==i and [s['category'],s['tool']]==expected and s['exit_code']==0
 assert math.isfinite(s['wall_s']) and s['wall_s']>0
 assert digest(out/f'{i:02d}.log')==s['log_sha256']
 assert digest(replay/'tools'/s['tool'])==p['stage_source_sha256'][s['tool']]
 costs[s['category']]=costs.get(s['category'],0)+s['wall_s']
assert sum(costs.values())<=r['total_wall_s']
e=replay/'experiments';cold=read(e/'ex5p_swapped_place_cold_2026-10-06/receipt.json')
assert cold['exit_code']==0 and cold['native_success'] and cold['cpd_ns']==5.44704
for path,h in cold['files_sha256'].items(): assert digest(path)==h
assert digest(e/'ex5p_swapped_place_cold_2026-10-06/protocol.json')==cold['protocol_sha256']
assert cold['source_sha256']==p['stage_source_sha256']['trial_ex5p_swapped_place_cold.py']
gate=read(e/'ex5p_swapped_quality_gate_2026-10-06/verification.json')
assert gate['FULL_reload_success'] and gate['rejected_predicted_timing_regression']
assert gate['connections']==1916 and gate['packing_mismatches']==gate['trace_fixups']==0
assert gate['selected_reference_cpd_ns']==cold['cpd_ns'] and gate['rejected_predicted_cpd_ns']==5.85882
assert digest(e/'ex5p_swapped_quality_gate_2026-10-06/selection.json')==gate['selection_sha256']
result={'authenticated':True,'receipt_sha256':digest(out/'receipt.json'),'category_wall_s':costs,'workflow_non_audit_including_cold_reference_s':sum(v for k,v in costs.items() if k!='audit'),'audit_wall_s':costs['audit'],'cold_native_process_wall_s':cold['native_process_wall_s'],'replay_total_wall_s':r['total_wall_s'],'quality_gate':gate,'scope':'Fresh frozen swappedplacement development pipeline; coldreference generated and included in workflow cost, not archivalfallback. Common pre-route fixture/build/original candidate preparation and replay staging excluded. Extra timing-tuning rounds outside this baseline policy. Non-audit subtotal not optimized production latency or prospective generalization.'}
(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(result,indent=2))
