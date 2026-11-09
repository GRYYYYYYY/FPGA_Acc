"""Actual early capture is controlled by n5938; access branch masked."""
import json,itertools,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];T=R/'experiments/full_csr_capture_operands_trace_v1_2026-10-09/trace_audit.json';L=R/'experiments/full_csr_capture_export_luts_v1_2026-10-09/audit.json';t=json.loads(T.read_text());lut=next(r for r in json.loads(L.read_text())['records'] if r['node']=='new_n5937');mask=lut['mask'];routes=lut['input_routes_lsb_first']
def evaluate(values):
 possibilities=[['0','1'] if values[r['node']]=='x' else [values[r['node']]] for r in routes];out={mask[-1-sum(int(v)<<lane for lane,v in enumerate(bits))] for bits in itertools.product(*possibilities)};return next(iter(out)) if len(out)==1 else 'x'
checked=0
for mid,control in itertools.product(['0','1','x'],repeat=2):
 vals={'new_n5324':'1','new_n5375':'0','new_n5940':'1','new_n5366':mid,'new_n5938':control};assert evaluate(vals)==control;checked+=1
rows=[r for r in t['rows'] if r['new_n5324']=='1' and r['new_n5375']=='0' and r['new_n5940']=='1'];assert [r['cycle'] for r in rows]==list(range(136));assert all(r['new_n5937']==r['new_n5938'] for r in rows)
out={'actual_export_three_value_cases':checked,'observed_guard_cycles':[r['cycle'] for r in rows],'first_unknown_capture_witness':rows[5],'source_first_capture_witness':rows[132],'conclusion':'Cycles0..135 actual known operands mask n5366, including cache-access allow branch. Native capture equals n5938,0 first5 thenX; earliest captureX cannot be attributed solely to accessallowX.','next_obligation':'Observe actual n5938 flusher/CSR/memory-management/execute-valid operands and compare exported LUT evaluation. Cycles136..511 require separate multiunknown analysis.','hashes':{str(f.relative_to(R)):hashlib.sha256(f.read_bytes()).hexdigest() for f in [T,L]}}
D=R/'experiments/full_csr_capture_early_mask_v1_2026-10-09';D.mkdir(exist_ok=True);(D/'audit.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps({'checked':checked,'guard_cycles':len(rows),'conclusion':out['conclusion']}))
