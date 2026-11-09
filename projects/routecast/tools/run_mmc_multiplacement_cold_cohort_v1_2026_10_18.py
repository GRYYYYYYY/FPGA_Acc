"""Freeze cold-label cohort protocol before labels; route only admitted cases."""
import json,sys,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18';G=R/'experiments/mmc_multiplacement_geometry_v1_2026-10-18'
assert json.loads((I/'preparation_complete.json').read_text())['all3_endpoint_and_native_identity_checks_pass']
D=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18';D.mkdir()
def sha(p):
 h=hashlib.sha256()
 with Path(p).open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
files=[Path(__file__),R/'tools/run_mmc_multiplacement_cold_label_v1_2026_10_18.py',G/'cohort_protocol.json',G/'geometry_independent_verification_v1.json',I/'preparation_complete.json',R/'experiments/mmc_common_native_label_matrix_v1_2026-10-18/native_retained_initializer_protocol_v1.json']
for i in range(1,4):files.append(I/('case_%02d'%i)/'staged_input_verification_v1.json')
protocol=dict(bindings={str(p):sha(p) for p in files},case_order=['case_01','case_02','case_03'],native_label='cold unseeded, original width128/workers1/seed1/FULL/current binary/architecture/RR',candidate_policy='Unchanged NATIVE_ENDPOINT_ANCHORED_PROXY_V2 retained_on; no data-driven arm replacement',primary_controls=['previous_native density footprint (not a legal moved-endpoint route)','matched-budget raw_min_on'],quality_metrics=['concrete Spearman','concrete precision at top5percent','spatial Spearman','spatial precision at top20'],domain='All positive CHANX/CHANY; inclusive spatial span bins(layer,x,y,type,segment); retain zero entries',tie_rule='descending value then ascending numeric resource ID/tuple',primary_gate='Each frozen case must nonregress in all4 primary metrics versus both controls and strictly improve >=1 metric versus each; Spearman epsilon1e-12. All cases required. No replacement on route/model failure.',scope='Cold labels and global rerouting coverage first. Four-arm estimator runs are subsequent work, not proven by this launcher. Development design only, no heldout/hardware/full-time claim.')
with (D/'evaluation_protocol.json').open('x') as f:json.dump(protocol,f,indent=2)
rows=[]
for case in protocol['case_order']:
 print('COLD LABEL START',case,flush=True)
 code=subprocess.call([sys.executable,str(R/'tools/run_mmc_multiplacement_cold_label_v1_2026_10_18.py'),str(I/case),str(D/case)],cwd=R)
 rows.append(dict(case=case,exit_code=code));(D/'stage_status.json').write_text(json.dumps(rows,indent=2));assert code==0
with (D/'cohort_complete.json').open('x') as f:json.dump(dict(rows=rows,all3_cold_labels_admitted=True),f,indent=2)
print('ALL3 COLD LABELS FULL PHYSICAL CANONICAL PASS',flush=True)
