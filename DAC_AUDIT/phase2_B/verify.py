"""Single-command compact evidence consistency/statistics check; no native experiments."""
from pathlib import Path
import json,csv,hashlib,statistics,sys
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent/'phase2_A/source'))
from run_v4_timing_protocol import signature,feedback_signature
from run_tileplace_v2 import acceptance_reason
read=lambda p:json.loads(p.read_text())
s=read(D/'evidence/summary.json');p=read(D/'PROTOCOL.json');supp=read(D/'evidence/supplemental_summary.json');total=s['total_subprocess_s']+sum(r.get('outer_s',0) for r in supp['runs']);assert total<=7200
for row in csv.DictReader((D/'evidence_index.csv').open()):
 f=D/row['path'];assert f.stat().st_size==int(row['bytes']);assert hashlib.sha256(f.read_bytes()).hexdigest()==row['sha256'],str(f)
for item in read(D/'source_manifest.json')['files']:assert hashlib.sha256((D/item['path']).read_bytes()).hexdigest()==item['sha256']
for item in read(D/'source_manifest.json')['reference_files']:assert hashlib.sha256((D.parent/'phase2_A/source'/item['name']).read_bytes()).hexdigest()==item['sha256']
for script,protocol in [('micro_cost.py','MICRO_PROTOCOL.json'),('fixture.py','FIXTURE_PROTOCOL.json')]:assert hashlib.sha256((D/script).read_bytes()).hexdigest()==read(D/protocol)['script_sha256']
assert read(D/'evidence/fixture/stdout.json')['status']=='pass'
assert read(D/'evidence/baseline_log_validation.json')['completed_points']==94
ref={};out=[]
for r in s['rows']:
 if r.get('status')!='completed' or r['mode'] not in ['correctness','performance']:continue
 d=D/'evidence'/r['id'];rep=read(d/'report.json');sig={'decisions':signature(rep),'feedback':feedback_signature(rep),'phases':rep['phases'],'costs':[t['transactions'] for t in rep['trials']]};assert sig==ref.setdefault((r['case'],'native'),sig)
 if r['mode']=='correctness':
  o=read(d/'observations.json');key={k:o[k] for k in ['count','counts','chunks']};assert o['count']>0;assert key==ref.setdefault((r['case'],'enumeration'),key)
for run in s['rows']:
 if run['mode']!='baseline' or run.get('status')!='completed':continue
 b=read(D/'evidence'/run['id']/'baseline.json');inc=b['b0'];case=next(c for c in p['cases'] if c['case']==run['case']);cmd=case['command_template'];place=cmd[cmd.index('--input-place')+1]
 for number,t in enumerate(b['trials'],1):
  assert t['seed']==number
  cmd=t['command'];assert cmd[cmd.index('--read_initial_place_file')+1]==place
  expected=acceptance_reason(t,inc,b['b0'])[0] and t.get('validated_s',float('inf'))<=b['budget_s']
  assert bool(t.get('accepted',False))==expected
  if expected:
   inc={k:t[k] for k in ['status','legal','cpd_ns','wirelength']};place=cmd[cmd.index('--place_file')+1]
 assert inc==b['incumbent']
for case in ['diffeq','clma']:
 arms={arm:[r['outer_s'] for r in s['rows'] if r.get('case')==case and r.get('arm')==arm and r['mode']=='performance' and r['status']=='completed'] for arm in ['R0','R1']}
 out.append({'case':case,'samples':arms,'reduction':1-statistics.median(arms['R1'])/statistics.median(arms['R0']) if all(arms.values()) else None})
print(json.dumps({'status':'pass','total_subprocess_s':total,'performance':out},indent=2))
