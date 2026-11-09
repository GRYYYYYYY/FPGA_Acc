"""Bound request guards, native rollback, and same-process epoch replay rejection."""
import json,sys,shutil,subprocess,os,re
from pathlib import Path
from collections import Counter
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_ledger_import_compact import physical_paths
R=Path(__file__).resolve().parents[2];o=R/'experiments/native_route_transaction_v6_guards_2026-10-07';o.mkdir(exist_ok=False);b=R/'experiments/native_resume_shared_cold_adder_step3_workflow_2026-10-07';base=b/'canonical';candidate=b/'exchange_native/design.route';r=json.loads((b/'receipt.json').read_text());binary=R/'build/native_route_transaction_v6_2026-10-07/routecast_transaction_vpr';graph=Path(r['canonical']['command'][r['canonical']['command'].index('--read_rr_graph')+1]);arch=Path(r['canonical']['command'][1]);cases=['commit','forced_rollback','malformed_late_net','wrong_graph','wrong_net','wrong_placement','wrong_architecture','wrong_parent','wrong_candidate','stale_epoch','epoch_overflow','negative_epoch','bad_next_epoch','wrong_version','duplicate_field','trailing_data','missing_request','quick_mode','replay'];inputs={str(p):sha(p) for p in [binary,graph,arch,candidate,b/'receipt.json',Path(__file__),*[base/f for f in ('design.blif','design.net','design.place','design.route')]]};(o/'protocol.json').write_text(json.dumps(dict(inputs=inputs,cases=cases,scope='Prepared candidate guard/import pilot; independent of any speed claim. Replay test flag resubmits exact same request in same context.'),indent=2)+'\n');rows=[];norm=lambda p:{n:Counter(seq) for n,seq in physical_paths(p).items() if seq}
for case in cases:
 w=o/case;w.mkdir()
 for f in ('design.blif','design.net','design.place','design.route'):shutil.copyfile(base/f,w/f)
 text=candidate.read_text()
 if case=='malformed_late_net':
  m=list(re.finditer(r'^Net \d+ \((.*?)\)',text,re.M))[-1];text=text[:m.start(1)]+'WRONG_NATIVE_NET'+text[m.end(1):]
 selected=w/'candidate.route';selected.write_text(text);fields=dict(epoch='0',next_epoch='1',graph='SHA256:'+sha(graph),net='SHA256:'+sha(w/'design.net'),placement='SHA256:'+sha(w/'design.place'),architecture='SHA256:'+sha(arch),parent_route='SHA256:'+sha(w/'design.route'),candidate='SHA256:'+sha(selected))
 mapping={'wrong_graph':'graph','wrong_net':'net','wrong_placement':'placement','wrong_architecture':'architecture','wrong_parent':'parent_route','wrong_candidate':'candidate'}
 if case in mapping:fields[mapping[case]]='SHA256:'+'0'*64
 if case=='stale_epoch':fields.update(epoch='1',next_epoch='2')
 if case=='epoch_overflow':fields['epoch']='18446744073709551616'
 if case=='negative_epoch':fields['epoch']='-1'
 if case=='bad_next_epoch':fields['next_epoch']='2'
 lines=['ROUTECAST_NATIVE_TX_V1',*[f'{k} {v}' for k,v in fields.items()],'END']
 if case=='wrong_version':lines[0]='UNKNOWN_TX'
 if case=='duplicate_field':lines.insert(3,'epoch 0')
 if case=='trailing_data':lines.append('extra token')
 request=w/'request.txt';request.write_text('\n'.join(lines)+'\n');cmd=list(r['canonical']['command']);cmd[0]=str(binary);env={k:v for k,v in os.environ.items() if not k.startswith('ROUTECAST_')};env.update(ROUTECAST_TX_CANDIDATE=str(selected),ROUTECAST_TX_PREFIX=str(w/'tx'))
 if case!='missing_request':env['ROUTECAST_TX_REQUEST']=str(request)
 if case=='forced_rollback':env['ROUTECAST_TX_FORCE_ROLLBACK']='1'
 if case=='replay':env['ROUTECAST_TX_TEST_REPLAY']='1'
 if case=='quick_mode':cmd[cmd.index('--check_route')+1]='quick'
 with (w/'run.log').open('w') as stream:code=subprocess.run(cmd,cwd=w,env=env,stdout=stream,stderr=subprocess.STDOUT,timeout=60).returncode
 log=(w/'run.log').read_text();assert code==0 and 'VPR succeeded' in log,(case,code,log[-1600:]);cpd=float(re.findall(r'Final critical path delay \(least slack\):\s*([0-9.]+)',log)[-1]);statuses=[]
 for index in range(2 if case=='replay' else 1):
  stem=w/f'tx.attempt{index}';status=json.loads(Path(str(stem)+'.json').read_text());statuses.append(status)
  accepted=case in ('commit','replay') and index==0;assert status['committed']==accepted
  native_attempt=accepted or case in ('forced_rollback','malformed_late_net');assert status['mutation_started']==native_attempt
  expected_epoch=1 if case=='replay' and index==1 else 0;assert status['epoch_before']==expected_epoch and status['epoch_after']==(1 if accepted else expected_epoch)
  expected=candidate if accepted or case=='replay' else base/'design.route';assert norm(Path(str(stem)+'.after.route'))==norm(expected)
  if not accepted:assert status['error'] and Path(str(stem)+'.before.route').read_bytes()==Path(str(stem)+'.after.route').read_bytes()
 assert cpd==(4.87739 if case in ('commit','replay') else 5.05896),(case,cpd)
 errors={'wrong_graph':'graph binding','wrong_net':'NET binding','wrong_placement':'placement binding','wrong_architecture':'architecture binding','wrong_parent':'parent route binding','wrong_candidate':'candidate binding','stale_epoch':'epoch transition','epoch_overflow':'epoch overflow','negative_epoch':'invalid epoch integer','bad_next_epoch':'epoch transition','wrong_version':'version','duplicate_field':'field/order','trailing_data':'request END','missing_request':'missing transaction','quick_mode':'FULL nonflat','malformed_late_net':'Net name WRONG_NATIVE_NET','forced_rollback':'forced post-validation'}
 if case in errors:assert errors[case] in statuses[0]['error'],(case,statuses)
 if case=='replay':assert 'epoch transition' in statuses[1]['error']
 rows.append(dict(case=case,exit_code=code,cpd_ns=cpd,statuses=statuses,all_expected_paths_match=True,files={str(p):sha(p) for p in w.iterdir() if p.is_file()}));print(case,cpd,[(x['committed'],x['mutation_started'],x['epoch_before'],x['epoch_after']) for x in statuses],flush=True)
assert all(sha(p)==h for p,h in inputs.items());(o/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(o/'protocol.json'),inputs=inputs,rows=rows,scope='Serial analysis-loaded nonflat context; explicit graph/NET/place/architecture/parent/candidate digest and uint64 epoch request guard. Pre-import rejection and two post-mutation rollbacks verified; same-process replay rejected after committed epoch increment. No concurrent/durable publication, arbitrary exceptions or complete pipeline speed proof.'),indent=2)+'\n')
