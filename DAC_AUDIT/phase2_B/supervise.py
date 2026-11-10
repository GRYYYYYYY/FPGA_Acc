import os,sys,json,time,subprocess,signal,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;A=D.parent/'phase2_A';sys.path.insert(0,str(A/'source'))
from run_v4_timing_protocol import signature,feedback_signature
p=json.loads((D/'PROTOCOL.json').read_text());root=Path(p['output_root']);root.mkdir(exist_ok=False);used=0.;rows=[];refs={};blocked=set()
def dump(f,v):f.write_text(json.dumps(v,indent=2,sort_keys=True)+'\n')
commit=subprocess.check_output(['git','rev-parse','HEAD'],cwd=D,text=True).strip();remote=subprocess.check_output(['git','ls-remote','origin','refs/heads/audit/dac2027-evidence-20261110'],cwd=D,text=True).split()[0];assert commit==remote
manifest=json.loads((D/'source_manifest.json').read_text())
for f in manifest['files']:assert hashlib.sha256((D/f['path']).read_bytes()).hexdigest()==f['sha256']
dump(root/'pre_run.json',{'commit':commit,'protocol_sha256':hashlib.sha256((D/'PROTOCOL.json').read_bytes()).hexdigest(),'started_unix':time.time()})
def launch(row,cmd,limit):
 global used
 w=root/row['id'];w.mkdir();env=os.environ.copy();env.update(p['environment']);env.update(REUSE_ARM=row.get('arm','R0'),REUSE_MODE=row['mode'],REUSE_OUTPUT=str(w));t=time.monotonic();env['BUDGET_START']=str(t)
 with (w/'stdout.log').open('w') as out,(w/'stderr.log').open('w') as err:
  q=subprocess.Popen(cmd,cwd=w,env=env,stdout=out,stderr=err,start_new_session=True);ident=Path(f'/proc/{q.pid}/stat').read_text().split()[21];row.update(pid=q.pid,start_ticks=ident,command=cmd,status='running');dump(root/'progress.json',rows)
  try:q.wait(timeout=limit);state='completed' if q.returncode==0 else 'failed'
  except subprocess.TimeoutExpired:
   state='timeout'
   if q.poll() is None and Path(f'/proc/{q.pid}/stat').read_text().split()[21]==ident:os.killpg(q.pid,signal.SIGKILL)
   q.wait()
  elapsed=time.monotonic()-t;used+=elapsed;row.update(status=state,returncode=q.returncode,outer_s=elapsed)
 dump(w/'process.json',row);return w
# Unit counterexamples count toward total budget.
unit={'id':'unit','mode':'unit'};rows.append(unit);launch(unit,['/usr/bin/python3',str(D/'unit.py')],60)
if unit['status']!='completed':blocked.update(['diffeq','clma'])
for item in p['schedule']:
 row=dict(item);rows.append(row)
 reserve=550
 if row['case'] in blocked or used+900+reserve>7200:row.update(status='NOT_STARTED',reason='correctness_or_budget_stop');continue
 case=next(c for c in p['cases'] if c['case']==row['case']);w=root/row['id'];cmd=[x.replace('{run_dir}',str(w)) for x in case['command_template']];cmd[cmd.index(str(A/'source/run_tileplace_v2.py'))]=str(D/'entry.py')
 w=launch(row,cmd,900)
 if row['status']=='completed':
  r=json.loads((w/'report.json').read_text());o=json.loads((w/'observations.json').read_text());s={'decisions':signature(r),'feedback':feedback_signature(r),'phases':r['phases'],'costs':[t['transactions'] for t in r['trials']]}
  previous=refs.setdefault((row['case'],'native'),s);row['native_exact']=s==previous
  if row['mode']=='correctness':
   sig={'count':o['count'],'counts':o['counts'],'chunks':o['chunks']};prev=refs.setdefault((row['case'],'enumeration'),sig);row['enumeration_exact']=sig==prev and o['count']>0
   if not row['enumeration_exact']:
    witness={'first_different_chunk':next((i for i,(a,b) in enumerate(zip(prev['chunks'],sig['chunks'])) if a!=b),None),'reference_counts':prev['counts'],'candidate_counts':sig['counts']};dump(w/'difference.json',witness)
  if not row['native_exact'] or row.get('enumeration_exact') is False:blocked.add(row['case'])
 else:blocked.add(row['case'])
 dump(w/'process.json',row);dump(root/'progress.json',rows);print(row['id'],row['status'],round(row.get('outer_s',0),2),row.get('enumeration_exact'),flush=True)
for case,budget in p['baseline_budgets'].items():
 row={'id':case+'_native','case':case,'mode':'baseline'};rows.append(row)
 if used+budget+3>7200:row['status']='NOT_STARTED';continue
 launch(row,['taskset','-c','31','/usr/bin/python3',str(D/'baseline.py'),case,str(root/row['id'])],budget+3);dump(root/'progress.json',rows);print(row['id'],row['status'],flush=True)
dump(root/'summary.json',{'rows':rows,'total_subprocess_s':used,'blocked':sorted(blocked),'pre_run_commit':commit});print('FINISHED',used,flush=True)
