"""Full archived cohort plus exact arithmetic gate boundary contract."""
import json
from pathlib import Path
from native_qor_admission import admit,joint_qor
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/native_qor_admission_contract_2026-10-07';out.mkdir();cold=ROOT/'experiments/bitonic_workflow_tree_swapped_cold_2026-10-07/receipt.json';raw=ROOT/'experiments/bitonic_workflow_tree_resident_staging_native_import_2026-10-07/receipt.json';cr=json.loads(cold.read_text());rr=json.loads(raw.read_text());rows=[admit(c,r) for c,r in zip(cr['rows'],rr['rows'])];assert [x['admitted'] for x in rows]==[False,False,True]
assert joint_qor('1.000000000000000000001',1,'1',1)['admitted'] is False
assert joint_qor('1',2,'1',1)['admitted'] is False
assert joint_qor('1',1,'1.0',1)['admitted'] is True
assert joint_qor('0.9',1,'1',1)['admitted'] is True
(out/'verification.json').write_text(json.dumps(dict(sources={str(f):sha(f) for f in [Path(__file__),ROOT/'tools/native_qor_admission.py']},inputs={str(f):sha(f) for f in [cold,raw]},rows=rows,exact_boundary_fixtures=4,scope='Archived full3 native artifacts/layout/tool/config/log screened. Two reject one provisional admit; not new fresh workflow, canonical accepted proof still required.'),indent=2)+'\n');print(rows)
