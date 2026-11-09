"""Authenticate exact single sink-pin corruption and actual native rejection evidence."""
import json,re
from pathlib import Path
from pre_route_endpoints import sha
from native_resume_prototype.source_binding_v2 import closure
R=Path(__file__).resolve().parents[1];E=R/'experiments';D=E/'adder_native_controlled_seed_recovery_verification_v1_2026-10-09';D.mkdir(exist_ok=False);B=E/'adder_native_controlled_seed_recovery_v1_2026-10-09';p=B/'verification.json';r=json.loads(p.read_text());bindings={**r['bindings'],str(p):sha(p),**closure([Path(__file__)])};assert all(sha(p)==h for p,h in bindings.items());rows=[]
for row in r['rows']:
 step=row['step'];original=E/f'adder_cross_place_hybrid_serialization_v1_2026-10-09/step_{step}.route';corrupt=B/f'step_{step}_corrupt.route';expected,count=re.subn(r'(SINK[^\n]*Net_pin_index:\s*)\d+',r'\g<1>2147483647',original.read_text(),count=1);assert count==1 and corrupt.read_text()==expected
 log=(B/f'step_{step}_reject/run.log').read_text();assert 'Resume invalid/duplicate sink pin (NET ' in log and 'terminate called' not in log and 'Load Timing Constraints' in log
 rejected,recovery,accepted=row['events'];assert rejected['exit_code']==1 and rejected['controlled_vpr_error'] and not rejected['loaded'] and not rejected['full_check'];assert recovery['exit_code']==accepted['exit_code']==0 and recovery['paths_equal'] and accepted['paths_equal']
 commands=[json.loads((B/f'step_{step}_{phase}/command.json').read_text()) for phase in ('reject','recover_old','accept')];assert commands[0]['command']==commands[1]['command']==commands[2]['command'];assert Path(commands[0]['seed'])==corrupt and Path(commands[2]['seed'])==original
 assert row['rejection_epoch_and_state_unchanged'] and row['old_native_reload_equal'] and row['success_epoch']==1 and row['success_matches_native_output']
 oldp=E/'adder_native_seed_recovery_v1_2026-10-09/verification.json';old=json.loads(oldp.read_text());assert all(sha(p)==h for p,h in old['bindings'].items());bindings.update(old['bindings']);bindings[str(oldp)]=sha(oldp)
 assert [x.get('cpd_ns') for x in row['events'][1:]]==[x.get('cpd_ns') for x in old['rows'][step-1]['events'][1:]]
 rows.append(dict(step=step,exact_single_sink_pin_corruption=True,unchanged_valid_native_command=True,native_sink_identity_exception_confirmed=True,termination='VPR_ERROR_EXIT_1',old_recovery_and_valid_candidate_pass=True))
assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,scope='Confirms actual controlled seed-load VPR error exit and old/candidate path-budget-CPD parity to v8; same-process rollback, iterative-route failure or durable transaction.'),indent=2)+'\n');print(json.dumps(rows,indent=2))
