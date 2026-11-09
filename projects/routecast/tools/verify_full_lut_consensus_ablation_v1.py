"""Authenticate a finished Full source/export LUT-model diagnostic ablation."""
from pathlib import Path
import hashlib,json,re
root=Path(__file__).resolve().parents[1]
p=root/'experiments/full_source_export_lut_consensus_diagnostic_v3_2026-10-09'
b=root/'experiments/full_source_export_four_state_compare_v2_2026-10-09'
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
protocol=json.loads((p/'protocol.json').read_text())
for name,h in protocol['bindings'].items():assert sha(name)==h
assert sha(b/'receipt.json')==protocol['parent_comparison_receipt_sha256']
for name in ['reference.v','design.v','tb.v','control.py','run.py']:assert (p/name).read_bytes()==(b/name).read_bytes()
def remove_lut(s):
 return re.sub(r'module LUT_K\b.*?endmodule','<LUT_MODEL>',s,count=1,flags=re.S)
assert remove_lut((p/'primitives.v').read_text())==remove_lut((b/'primitives.v').read_text())
stages=json.loads((p/'stages.json').read_text())
assert len(stages)==3 and all(r['exit_code']==0 for r in stages)
receipt=json.loads((p/'receipt.json').read_text());assert receipt['exit_code']==0
log=(p/'control.log').read_text();match=re.search(r'ROUTECAST_FULL_COMPARE_DONE mismatches=\s*(\d+)',log);assert match
assert 'reason="finish"' in log
original=json.loads((b/'receipt.json').read_text())['output_mismatches']
report={'original_mismatches':original,'consensus_model_mismatches':int(match[1]),'ablation_only_lut_behavior_verified':True,'bindings':{str(f):sha(f) for f in [Path(__file__),p/'protocol.json',p/'receipt.json',p/'control.log',p/'stages.json',b/'receipt.json']},'scope':'Matched model-semantics diagnostic over the same 11 startup snapshots/145 output bits. Not Full sequential equivalence, physical initialization or unseen-family admission.'}
(p/'ablation_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k!='bindings'}))
