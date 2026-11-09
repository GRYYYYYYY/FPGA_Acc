"""Changed-candidate commit and two real post-mutation rollback cases."""
import json,sys,shutil,subprocess,os,re,time
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_route_transaction_2026-10-07';o.mkdir(exist_ok=False);b=R/'experiments/native_resume_shared_cold_adder_step3_workflow_2026-10-07';binary=R/'build/native_route_transaction_2026-10-07/routecast_transaction_vpr';r=json.loads((b/'receipt.json').read_text());base=b/'canonical';candidate=b/'exchange_native/design.route';inputs={str(p):sha(p) for p in [binary,candidate,b/'receipt.json',Path(__file__),*[base/f for f in ('design.blif','design.net','design.place','design.route')]]};(o/'protocol.json').write_text(json.dumps(dict(inputs=inputs,cases=['commit','forced_rollback','malformed_late_net'],scope='Prepared archived candidate; same-process FULL import and rollback pilot, no fresh feedback/candidate generation or full net-gain cost.'),indent=2)+'\n');rows=[];norm=lambda p:{n:Counter(paths) for n,paths in physical_paths(p).items() if paths}
assert norm(base/'design.route')!=norm(candidate)
for case in ('commit','forced_rollback','malformed_late_net'):
 w=o/case;w.mkdir()
 for f in ('design.blif','design.net','design.place','design.route'):shutil.copyfile(base/f,w/f)
 selected=w/'candidate.route';text=candidate.read_text()
 if case=='malformed_late_net':
  matches=list(re.finditer(r'^Net \d+ \((.*?)\)',text,re.M));assert len(matches)>1;last=matches[-1];text=text[:last.start(1)]+'WRONG_NATIVE_NET'+text[last.end(1):]
 selected.write_text(text);cmd=list(r['canonical']['command']);cmd[0]=str(binary);env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_TX_CANDIDATE=str(selected),ROUTECAST_TX_PREFIX=str(w/'tx'))
 if case=='forced_rollback':env['ROUTECAST_TX_FORCE_ROLLBACK']='1'
 begin=time.perf_counter()
 with (w/'run.log').open('w') as stream:code=subprocess.run(cmd,cwd=w,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
 log=(w/'run.log').read_text();assert code==0 and 'VPR succeeded' in log,(case,code,log[-2000:]);status=json.loads((w/'tx.json').read_text());cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);expected=candidate if case=='commit' else base/'design.route';assert norm(w/'tx.after.route')==norm(expected)
 if case=='commit':assert status['committed'] and cpd==float(r['cpd_ns'])
 else:
  assert not status['committed'] and status['error'];assert (w/'tx.before.route').read_bytes()==(w/'tx.after.route').read_bytes();assert cpd==5.05896
 rows.append(dict(case=case,exit_code=code,cpd_ns=cpd,status=status,seconds=time.perf_counter()-begin,expected_physical_paths_exact=True,files={str(p):sha(p) for p in w.iterdir() if p.is_file()}));print(case,cpd,status,flush=True)
assert all(sha(p)==h for p,h in inputs.items());(o/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(o/'protocol.json'),inputs=inputs,rows=rows,scope='Live route context imported changed complete candidate and updated final STA in one native process; rollback serialized paths/CPD verified after forced rejection and late parse failure. Explicit context-field snapshot, not concurrency/durable epoch service, not all exception/global allocator state proof or complete speed comparison.'),indent=2)+'\n')
