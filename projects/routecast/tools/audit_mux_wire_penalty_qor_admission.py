"""Retrospective joint CPD/wirelength eligibility, without inventing timings."""
import json
from pathlib import Path
from fractions import Fraction as F
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];source=ROOT/'experiments/mux_wire_penalty_fixed_cap_cohort_2026-10-07/final_evidence.json';r=json.loads(source.read_text());assert all(sha(f)==h for f,h in r['files'].items());rows=[]
for x in r['rows']:
 if not x.get('new_native_execution'):continue
 candidate=F(x['candidate_native_cpd_ns']);baseline=F(str(x['cold_native_cpd_ns']));cw=x['candidate_wirelength'];bw=x['cold_wirelength'];assert type(cw) is int and type(bw) is int
 reasons=[]
 if candidate>baseline:reasons.append('CPD_EXCEEDS_COLD_REFERENCE')
 if cw>bw:reasons.append('WIRELENGTH_EXCEEDS_COLD_REFERENCE')
 rows.append(dict(width=x['width'],index=x['index'],candidate_cpd_ns=str(candidate),cold_cpd_ns=str(baseline),candidate_wirelength=cw,cold_wirelength=bw,wirelength_increase=cw-bw,quality_eligible=not reasons,reasons=reasons,accepted_lifecycle_status='NOT_MEASURED'))
assert len(rows)==3 # Preserve every outcome; weighted eligibility not predetermined.
out=ROOT/'experiments/mux_wire_penalty_joint_qor_admission_2026-10-07';out.mkdir(exist_ok=True);(out/'report.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),input_sha256=sha(source),rows=rows,scope='Retrospective zero-tolerance CPD/wirelength nonregression screen on three already-qualified fixed-cap candidates against authenticated cold native results. Not an outcome-blind prospective protocol, full cost admission or global infeasibility claim. Complete accepted lifecycle time missing; no ACCEPT or speedup claim. Current CPD-only gate differs from this explicitly stronger joint screen.'),indent=2)+'\n');print(rows,flush=True)
