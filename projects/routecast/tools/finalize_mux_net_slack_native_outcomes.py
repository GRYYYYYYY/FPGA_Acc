"""Bind final12 sketch/audit/native/cost evidence with explicit acceptance scopes."""
import json
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06';r=json.loads((out/'receipt.json').read_text());a=json.loads((out/'audit_summary.json').read_text());n=json.loads((out/'native_outcomes_snapshot.json').read_text());c=json.loads((out/'cost_lower_bound_snapshot.json').read_text());assert len(r['rows'])==len(n['rows'])==len(c['rows'])==12;assert a['receipt_sha256']==c['online_receipt_sha256']==sha(out/'receipt.json');assert n['protocol_sha256']==sha(out/'protocol.json');rows=[]
for row,native,cost in zip(r['rows'],n['rows'],c['rows']):
 key=(row['width'],row['index']);assert key==(native['width'],native['index'])==(cost['width'],cost['index'])
 if row['status']=='COMPLETE_CANDIDATE':assert 'candidate_cpd_ns' in native and native['selected'] in ['predicted','reference']
 elif row['status']=='PRIOR_ALLOCATION_SKIP':assert native['status']=='INITIAL_SKIP' and cost['cost_bound'] is None
 else:assert native['status']=='INCOMPLETE_NOT_SUBMITTED'
 if row['status']!='PRIOR_ALLOCATION_SKIP':assert native['result_sha256']==row['result_sha256'] and cost['recorded_lower_bound_exceeds_cold'] and cost['recorded_cost_lower_bound_s']==cost['budget_preparation_s']+cost['sketch_loop_s']
 rows.append(dict(width=key[0],index=key[1],sketch_status=row['status'],native_status=native['status'],selected=native.get('selected'),candidate_cpd_ns=native.get('candidate_cpd_ns'),recorded_cost_lower_bound_s=cost.get('recorded_cost_lower_bound_s'),cold_accepted_lifecycle_s=cost.get('cold_accepted_lifecycle_s')))
(out/'native_outcomes_final.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),receipt_sha256=sha(out/'receipt.json'),audit_summary_sha256=sha(out/'audit_summary.json'),native_evidence_sha256=sha(out/'native_outcomes_snapshot.json'),cost_bound_sha256=sha(out/'cost_lower_bound_snapshot.json'),rows=rows,sketch_statuses=dict(Counter(x['sketch_status'] for x in rows)),native_validated=2,forecast_selected=1,reference_selected=1,scope='Final fixed12 cohort, sixaudit/provenance and completecandidate nativeOWNcanonical/gate selection evidence bound. Two valid candidates, onlyone forecast selected; skips/incomplete never submitted. Setup+sketch recorded lower bounds exceed single cold accepted timings even before native gates; no fullcohort success/general speedup/board claim.'),indent=2)+'\n');print('final12 native/cost evidence bound:2validated,1forecast selected')
