"""Audited full development feedback outcomes and explicit cost accounting."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'full_ram_swap_feedback_summary_v1_2026-10-09';D.mkdir(exist_ok=False)
proof=E/'full_ram_swap_native_audit_v2_2026-10-09/verification.json';v=json.loads(proof.read_text());assert v['passed']
for p,h in v['bindings'].items():assert sha(p)==h
incfile=E/'full_ram_swap_incremental_v1_2026-10-09/receipt.json';inc=json.loads(incfile.read_text());assert inc['status']=='COMPLETE_AUDITED_INCREMENTAL_DECISION'
candfile=E/'full_ram_swap_candidates_v1_2026-10-09/receipt.json';cand=json.loads(candfile.read_text());basefile=E/'full_ram_length_switch_prediction_v1_2026-10-09/receipt.json';base=json.loads(basefile.read_text())
for obj in (inc,cand,base):
 for p,h in obj['bindings'].items():assert sha(p)==h
rows=[]
for native in v['results']:
 cid=native['candidate'];log=E/f'full_ram_swap_native_matrix_v1_2026-10-09/candidate_{cid}/route.log';iters=[]
 for line in log.read_text().splitlines():
  if re.match(r'^\s*\d+\s+[0-9.]+\s+[0-9.]+\s+\d+\s+\d+\s+\d+\s+\d+\s+\d+\s+\(',line):
   w=line.split();iters.append(dict(iteration=int(w[0]),rerouted_nets=int(w[5]),rerouted_connections=int(w[6])))
 assert [x['iteration'] for x in iters]==list(range(1,native['iterations']+1))
 assert iters[0]['rerouted_connections']==16819
 rows.append(dict(**native,route_failure=False,predicted_scores=inc['details']['reports'][cid]['scores'],rerouted_connections_including_initial=sum(x['rerouted_connections'] for x in iters),rerouted_connections_after_initial=sum(x['rerouted_connections'] for x in iters[1:]),rerouted_nets_after_initial=sum(x['rerouted_nets'] for x in iters[1:])))
selected=inc['details']['selected_candidate'];chosen=rows[selected];off=rows[0]
assert selected==0 and chosen['wirelength']==off['wirelength'] and chosen['cpd_ns']==off['cpd_ns']
extract=sum(x['extraction_s'] for x in cand['results']);warm=inc['total_s']+chosen['native_s'];cold=base['total_seconds']+extract+warm
out=dict(rows=rows,selected_candidate=selected,quality_gain_vs_baseline=dict(wirelength=0,cpd_ns=0,route_failure=0),costs=dict(native_off_observed_s=off['native_s'],prepared_state_incremental_decision_s=inc['total_s'],prepared_state_on_stage_sum_s=warm,original_background_acquisition_s=base['total_seconds'],candidate_extraction_measured_s=extract,cold_accounted_stage_sum_lower_bound_s=cold,scope='Separately archived observations, no matched paired timing or amortized reuse claim. Cold lower bound excludes candidate generation non-extraction overhead and validation/archive operations; reused background/CSR acquisition is charged once.'),conclusion='Predictor retains baseline, matching best observed wirelength and CPD among two swaps. No quality gain; positive estimator cost. Not end-to-end benefit or unseen-family evidence.',bindings={str(p):sha(p) for p in [Path(__file__),proof,incfile,candfile,basefile]})
(D/'summary.json').write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
