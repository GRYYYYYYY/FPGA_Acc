"""Execute fixed two-initializer plus fresh original-XML proof on one frozen case."""
import json,sys,subprocess,hashlib
from pathlib import Path
R=Path(__file__).resolve().parents[1];case=sys.argv[1];assert case in ['case_01','case_02','case_03'];I=R/'experiments/mmc_multiplacement_inputs_v1_2026-10-18'/case;assert (I/'staged_input_verification_v1.json').exists()
D=R/'experiments/mmc_multiplacement_models_v1_2026-10-18';D.mkdir(exist_ok=True);O=D/case;O.mkdir()
files=[Path(__file__),R/'experiments/mmc_multiplacement_geometry_v1_2026-10-18/cohort_protocol.json',I/'staged_input_verification_v1.json',R/'experiments/mmc_common_native_label_matrix_v1_2026-10-18/native_retained_initializer_protocol_v1.json']
for name in ['run_mmc_multiplacement_initializers_v1_2026_10_18.py','verify_mmc_multiplacement_raw_floor_xml_v1_2026_10_18.py','verify_mmc_multiplacement_initializers_v1_2026_10_18.py']:files.append(R/'tools'/name)
bindings={str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files}
with (O/'protocol.json').open('x') as f:json.dump(dict(bindings=bindings,case=case,policy='Unchanged NATIVE_ENDPOINT_ANCHORED_PROXY_V2; raw_min/native_retained off initializers then independent proof; same original2round feedback remains primary candidate retained_on in later phase.',timing_scope='Unbalanced correctness production and fresh audits, no speed inference',labels_read=False),f,indent=2)
rows=[]
for script in ['run_mmc_multiplacement_initializers_v1_2026_10_18.py','verify_mmc_multiplacement_raw_floor_xml_v1_2026_10_18.py','verify_mmc_multiplacement_initializers_v1_2026_10_18.py']:
 print('INITIALIZER STAGE',case,script,flush=True)
 code=subprocess.call([sys.executable,str(R/'tools'/script),str(I),str(O)],cwd=R);rows.append(dict(script=script,exit_code=code));(O/'stage_status.json').write_text(json.dumps(rows,indent=2));assert code==0
print('CASE INITIALIZERS AND FRESH PROOFS PASS',case,flush=True)
