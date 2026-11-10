#!/usr/bin/env python3
"""Finite serial supervisor. Never restarts a failed run or modifies research inputs."""
import os,sys,json,subprocess,time,signal,hashlib,copy,datetime
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D/'source'))
from run_v4_timing_protocol import signature,feedback_signature
from tileplace_vpr import sha256
p=json.loads((D/'PILOT_PROTOCOL.json').read_text());root=Path(p['output_root'])
def dump(f,d):f.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=D,text=True).strip()
assert subprocess.check_output(['git','show',commit+':DAC_AUDIT/phase2_A/PILOT_PROTOCOL.json'],cwd=D)==(D/'PILOT_PROTOCOL.json').read_bytes()
assert not subprocess.check_output(['git','status','--porcelain','--','DAC_AUDIT/phase2_A/source','DAC_AUDIT/phase2_A/run_pilot.py','DAC_AUDIT/phase2_A/baseline_smoke.py','DAC_AUDIT/phase2_A/PILOT_PROTOCOL.json'],cwd=D)
root.mkdir(exist_ok=False)
receipt={'pre_run_commit':commit,'protocol_sha256':sha256(D/'PILOT_PROTOCOL.json'),'started_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'output_root':str(root)}
dump(D/'PRE_RUN_COMMIT.json',receipt);dump(root/'pre_run.json',receipt)
rows=copy.deepcopy(p['schedule']);env=os.environ.copy();env.update(p['environment']);refs={};blocked=set();fatal=False
start=time.monotonic();deadline=start+p['pilot_wall_budget_s']
def launch(row,cmd,remaining):
 w=root/row['run_id'];w.mkdir();dump(w/'command.json',cmd)
 row.update(status='started',command=cmd,load_before=Path('/proc/loadavg').read_text().strip());dump(root/'progress.json',rows)
 with (w/'stdout.log').open('w') as out,(w/'stderr.log').open('w') as err:
  t=time.monotonic_ns();q=subprocess.Popen(cmd,cwd=w,env=env,stdout=out,stderr=err,start_new_session=True)
  ident=Path(f'/proc/{q.pid}/stat').read_text().split()[21];row.update(pid=q.pid,pgid=q.pid,start_ticks=ident)
  try:q.wait(timeout=max(.01,min(p['run_timeout_s'],remaining)));state='completed' if q.returncode==0 else 'failed'
  except subprocess.TimeoutExpired:
   state='timeout'
   # Only the group created by this supervisor, with matching PID/start identity.
   if q.poll() is None and os.getpgid(q.pid)==q.pid and Path(f'/proc/{q.pid}/stat').read_text().split()[21]==ident:
    os.killpg(q.pid,signal.SIGTERM)
    try:q.wait(timeout=3)
    except subprocess.TimeoutExpired:os.killpg(q.pid,signal.SIGKILL);q.wait()
  row.update(status=state,returncode=q.returncode,outer_wall_s=(time.monotonic_ns()-t)/1e9,load_after=Path('/proc/loadavg').read_text().strip())
 dump(w/'process.json',row);return w
for row in rows:
 if fatal or row['case'] in blocked or time.monotonic()>=deadline:
  row.update(status='not_started',reason='exactness_stop' if fatal else 'case_stopped' if row['case'] in blocked else 'pilot_budget');continue
 case=next(x for x in p['cases'] if x['case']==row['case']);w=root/row['run_id'];cmd=[x.replace('{run_dir}',str(w)) for x in case['command_template']]
 env['TILEPLACE_PRESSURE_PREFIX']='1' if row['arm']=='A' else '0'
 w=launch(row,cmd,deadline-time.monotonic())
 if row['status']=='completed':
  audit_start=time.monotonic()
  try:
   r=json.loads((w/'report.json').read_text());assert r['provenance']['implementation']['sha256']==p['implementation']['sha256'];assert r['provenance']['source_and_input_hashes_unchanged_at_completion']
   assert len(r['trials'])>0 and r['final']['legal']
   for t in r['trials']:
    assert sha256(Path(t['candidate_place']['path']))==t['candidate_place']['sha256']
    assert sha256(Path(t['closure']['report_path']))==t['closure']['report_sha256']
   s={'decisions':signature(r),'feedback':feedback_signature(r),'phases':r['phases'],'costs':[x['transactions'] for x in r['trials']],'native_legal':[x['closure']['legal'] for x in r['trials']]}
   dump(w/'exact_signature.json',s)
   previous=refs.setdefault(row['case'],s)
   row['exact_match']=s==previous;row['comparison_items']=len(r['trials']);row['final']=r['final'];row['closures']=r['closure_calls'];row['accepted_transactions']=r['accepted_transactions']
   if not row['exact_match']:fatal=True;row['correctness_error']='nonidentical signature; performance claims stopped'
  except Exception as e:fatal=True;row['correctness_error']=repr(e);row['exact_match']=False
  row['offline_audit_wall_s']=time.monotonic()-audit_start
 else:blocked.add(row['case'])
 dump(w/'process.json',row);dump(root/'progress.json',rows)
 print(row['run_id'],row['status'],round(row['outer_wall_s'],3),'exact',row.get('exact_match'),flush=True)
# One separately bounded feasibility smoke, no restart or result-based parameters.
b={'run_id':'diffeq_baseline_smoke','case':'diffeq','kind':'baseline_smoke','arm':'B1','pair':0};env.pop('TILEPLACE_PRESSURE_PREFIX',None)
w=launch(b,['taskset','-c','31','/usr/bin/python3',str(D/'baseline_smoke.py'),str(root/b['run_id'])],900)
rows.append(b);dump(root/'progress.json',rows)
dump(root/'summary.json',{'pre_run':receipt,'runs':rows,'supervisor_elapsed_s':time.monotonic()-start,'pilot_budget_s':10800,'performance_claims_stopped':fatal,'blocked_cases':sorted(blocked)})
print('FINISHED',b['status'],round(b['outer_wall_s'],3),flush=True)
