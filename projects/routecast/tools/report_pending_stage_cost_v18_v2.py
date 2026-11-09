"""Authenticate paid top-level stage timings; no speedup or native-quality claim."""
import json,sys,math
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
out=R/'experiments/mcnc_pending_swap_stage_timing_v18_2026-10-07'
p=json.loads((out/'protocol.json').read_text());receipt=json.loads((out/'receipt.json').read_text());assert receipt['protocol_sha256']==sha(out/'protocol.json')
bindings={**p['inputs'],**p['sources'],**closure([Path(__file__)]),str(out/'receipt.json'):sha(out/'receipt.json'),str(out/'protocol.json'):sha(out/'protocol.json')}
for row in receipt['rows']:bindings.update(row['files'])
assert all(sha(k)==v for k,v in bindings.items());rows=[]
for row in receipt['rows']:
 calls=json.loads((out/row['name']/'stage_timings.json').read_text());stages=defaultdict(list)
 for call in calls:
  assert set(call)=={'stage','seconds'} and call['stage'] in {'greedy','selection','joint_primary_or_swap','expansion','swap_proposals'} and math.isfinite(call['seconds']) and call['seconds']>=0
  stages[call['stage']].append(call['seconds'])
 paid=sum(c['seconds'] for c in calls);assert paid<=row['sequence_seconds']
 events=[json.loads(f.read_text()) for f in (out/row['name']).glob('batch*.json')]
 assert len(stages['joint_primary_or_swap'])==len(events)+sum(len(e['owner_swap']['attempts']) for e in events if e['owner_swap'] is not None)
 assert len(stages['expansion'])==sum(e['owner_repair'] is not None for e in events)
 assert len(stages['swap_proposals'])==sum(e['owner_swap'] is not None for e in events)
 summary=dict(name=row['name'],completed=row['completed'],required=row['required'],stop=row['stop'],total_seconds=row['total_seconds'],sequence_seconds=row['sequence_seconds'],top_level_stage_seconds=paid,unattributed_sequence_seconds=row['sequence_seconds']-paid,stages={k:dict(calls=len(v),seconds=sum(v),max_call_seconds=max(v,default=0),share_of_sequence=sum(v)/row['sequence_seconds']) for k,v in sorted(stages.items())})
 rows.append(summary);print(json.dumps(summary),flush=True)
assert all(sha(k)==v for k,v in bindings.items());(out/'stage_cost_report.json').write_text(json.dumps(dict(rows=rows,bindings=bindings,scope='Authenticated single-run development top-level costs. Inclusive observer costs; no nested repair/joint double count. Unattributed residual includes cache finalize and other sequence overhead. Not full physical/native audit, heldout evidence or speedup proof.'),indent=2)+'\n')
