"""Execute frozen feedback component arms; independent final/event audits pending."""
import json,sys,subprocess,time
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools'));from pre_route_endpoints import sha
D=R/'experiments/xtea_native_state_feedback_comparison_v2_2026-10-18';D.mkdir(exist_ok=False);P=R/'experiments/native_state_feedback_inputs_v1_2026-10-18';proof=json.loads((P/'verification.json').read_text());assert all(sha(p)==h for p,h in proof['bindings'].items());protocol=R/'experiments/xtea_native_state_feedback_protocol_v1_2026-10-18/protocol.json';pp=json.loads(protocol.read_text());assert all(sha(p)==h for p,h in pp['bindings'].items());model=R/'tools/run_native_state_retained_feedback_v2_2026_10_18.py';contract=R/'experiments/native_state_feedback_source_contract_v2_2026-10-18/verification.json';c=json.loads(contract.read_text());assert all(sha(p)==h for p,h in c['bindings'].items());bindings={**proof['bindings'],str(protocol):sha(protocol),str(P/'verification.json'):sha(P/'verification.json'),str(model):sha(model),str(contract):sha(contract),str(Path(__file__)):sha(__file__)};none=D/'none';none.mkdir()
for name in ['initial.json','floors.json','history.json']:
 with (none/name).open('xb') as f:f.write((P/'warm'/name).read_bytes())
rows=[dict(arm='none',overflow=237,scope='Unchanged staged frame; no feedback')]
for arm in ['all','local']:
 cmd=[sys.executable,str(model),str(R/'experiments/xtea_native_state_new_swap_v1_2026-10-18/demand/endpoints.json'),str(D/arm),str(P/'base/verification.json'),str(P/'timing'),str(P/'warm'),arm];tick=time.perf_counter()
 with (D/(arm+'.log')).open('x') as f:code=subprocess.call(cmd,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 with (D/(arm+'_terminal.json')).open('x') as f:json.dump(dict(exit_code=code,process_seconds=time.perf_counter()-tick),f);f.write('\n')
 if code:raise SystemExit(code)
 r=json.loads((D/arm/'receipt.json').read_text());rows.append(dict(arm=arm,rounds=[dict(round=x['round_index'],nets=len(x['events']),commits=sum(e['status']=='COMMITTED' for e in x['events']),overflow=x['overflow_after']) for x in r['rounds']],model_seconds=r['total_paid_resident_seconds']));print('COMPONENT DONE',arm,rows[-1],flush=True)
assert all(sha(p)==h for p,h in bindings.items())
with (D/'receipt.json').open('x') as f:json.dump(dict(bindings=bindings,rows=rows,independent_audits_pending=True,scope='Frozen component execution only; no target native route, final acceptance, unseen evaluation or speed claim.'),f,indent=2);f.write('\n')
