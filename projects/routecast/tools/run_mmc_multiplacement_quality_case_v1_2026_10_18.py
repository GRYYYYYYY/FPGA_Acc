"""Full four-arm/control quality and independent metric audit for one frozen case."""
import json,sys,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];case=sys.argv[1];assert case in ['case_01','case_02','case_03'];M=R/'experiments/mmc_multiplacement_models_v1_2026-10-18'/case;N=R/'experiments/mmc_multiplacement_cold_labels_v1_2026-10-18'/case;endpoint=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case/'demand/endpoints.json';frozen=N.parent/'evaluation_protocol.json'
required=[M/'initial_independent_verification_v1.json',M/'feedback_audits/verification.json',N/'verification.json',frozen]
assert all(p.exists() for p in required)
D=R/'experiments/mmc_multiplacement_quality_v1_2026-10-18';D.mkdir(exist_ok=True);O=D/case;O.mkdir()
predictions={'raw_min_off':str(M/'raw_min/initial.json'),'raw_min_on':str(M/'feedback_on/raw_min/sketch.json'),'native_retained_off':str(M/'native_retained/initial.json'),'native_retained_on':str(M/'feedback_on/native_retained/sketch.json'),'previous_native':str(R/'experiments/mmc_native_source_checkpoint_v1_2026-10-18/initial.json')}
with (O/'protocol.json').open('x') as f:json.dump(dict(bindings={str(Path(__file__)):hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),str(frozen):hashlib.sha256(frozen.read_bytes()).hexdigest()},frozen_cohort_protocol=str(frozen),frozen_cohort_protocol_sha256=hashlib.sha256(frozen.read_bytes()).hexdigest(),endpoint=str(endpoint),model_directory=str(M),native_admission=str(N/'verification.json'),labels={'cold':str(N/'cold/physical_audit.json')},predictions=predictions,primary_candidate='native_retained_on',primary_controls=['raw_min_on','previous_native'],evidence_scope='Registered cohort policy and full-positive-domain/tie/K rules unchanged. One exposed development layout; all3 required for cohort primary gate. Congested estimators are sketches, previous_native only a density forecast. No heldout, candidate native QoR or workflow gain.'),f,indent=2)
for script in ['evaluate_mmc_multiplacement_quality_case_v1_2026_10_18.py','verify_mmc_multiplacement_quality_case_v1_2026_10_18.py']:
 print('QUALITY',case,script,flush=True);code=subprocess.call([sys.executable,str(R/'tools'/script),str(O)],cwd=R);assert code==0
print('QUALITY FULL DOMAIN AND METRICS VERIFIED',case,flush=True)
