"""Provisional admission provenance rejection and incomplete fallback contract."""
import json,copy
from pathlib import Path
from native_qor_admission import admit
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];cp=ROOT/'experiments/bitonic_workflow_tree_swapped_cold_2026-10-07/receipt.json';rp=ROOT/'experiments/bitonic_workflow_tree_resident_staging_native_import_2026-10-07/receipt.json';cold=json.loads(cp.read_text())['rows'][0];raw=json.loads(rp.read_text())['rows'][0];checked=[]
for kind in ['wrong_case','bad_artifact_hash','unconfirmed_raw_file','wrong_workers','wrong_raw_cpd']:
 c,r=copy.deepcopy(cold),copy.deepcopy(raw)
 if kind=='wrong_case':r['count']=8
 if kind=='bad_artifact_hash':r['files'][next(iter(r['files']))]='0'*64
 if kind=='unconfirmed_raw_file':r['serialized_file_unchanged']=False
 if kind=='wrong_workers':r['command'][r['command'].index('--num_workers')+1]='2'
 if kind=='wrong_raw_cpd':r['cpd_ns']='0'
 try:admit(c,r)
 except ValueError:checked.append(kind)
 else:raise AssertionError(kind)
r=copy.deepcopy(raw);r['status']='INCOMPLETE_NOT_SUBMITTED';a=admit(cold,r);assert not a['admitted'] and a['reasons']==['NO_COMPLETE_RAW_NATIVE_CANDIDATE']
p=ROOT/'experiments/native_qor_admission_integrity_2026-10-07';p.mkdir();(p/'verification.json').write_text(json.dumps(dict(sources={str(f):sha(f) for f in [Path(__file__),ROOT/'tools/native_qor_admission.py']},inputs={str(f):sha(f) for f in [cp,rp]},invalid_rejections=checked,incomplete_provisional_rejection=True,scope='Real artifact fixture with tampered caller metadata, no filesystem mutation. Gate does not publish state.'),indent=2)+'\n');print(checked)
