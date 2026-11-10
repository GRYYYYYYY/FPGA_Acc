"""Budgeted fresh-SA incumbent loop. All accepted points pass full native checks before cutoff."""
import sys,json,time,subprocess,shutil,os,signal
from pathlib import Path
D=Path(__file__).resolve().parent;sys.path.insert(0,str(D.parent/'phase2_A/source'))
from tileplace_vpr import validate_contract,sha256
from run_vpr_closure import match
from run_tileplace_v2 import acceptance_reason
p=json.loads((D/'PROTOCOL.json').read_text());case=sys.argv[1];w=Path(sys.argv[2]);start=float(os.environ['BUDGET_START']);deadline=start+p['baseline_budgets'][case];c=next(c for c in p['cases'] if c['case']==case)['command_template'];arg=lambda f:c[c.index(f)+1]
b0=json.loads(Path(arg('--baseline-closure')).read_text());inc=b0;place=arg('--input-place');rows=[];seed=1
m=json.loads((Path(arg('--contract'))/'manifest.json').read_text())
def save():
 (w/'baseline.json').write_text(json.dumps({'case':case,'budget_s':p['baseline_budgets'][case],'b0':b0,'incumbent':inc,'trials':rows,'elapsed_s':time.monotonic()-start},indent=2))
while time.monotonic()<deadline:
 d=w/f'seed_{seed:03}';d.mkdir();shutil.copyfile(arg('--netlist'),d/'input.net')
 cmd=[arg('--vpr'),arg('--architecture'),arg('--circuit'),'--net_file',str(d/'input.net'),'--read_initial_place_file',place,'--place_file',str(d/'output.place'),'--route_file',str(d/'output.route'),'--seed',str(seed),'--num_workers','1','--route_chan_width','200','--place_algorithm','criticality_timing','--timing_analysis','on','--echo_file','on','--place','--route','--analysis']
 if 'vpr_constraints' in m['inputs']:cmd+=['--read_vpr_constraints',m['inputs']['vpr_constraints']['path']]
 r={'seed':seed,'command':cmd,'started_s':time.monotonic()-start};rows.append(r);save();t=time.monotonic()
 with (d/'stdout.log').open('w') as out,(d/'stderr.log').open('w') as err:
  q=subprocess.Popen(cmd,cwd=d,stdout=out,stderr=err,start_new_session=True)
  try:q.wait(timeout=max(.001,deadline-time.monotonic()))
  except subprocess.TimeoutExpired:
   os.killpg(q.pid,signal.SIGKILL);q.wait();r.update(status='deadline_interrupted',accepted=False,returncode=q.returncode,elapsed_s=time.monotonic()-start);save();break
 text=(d/'stdout.log').read_text()+(d/'stderr.log').read_text();r.update(returncode=q.returncode,native_s=time.monotonic()-t)
 legal=q.returncode==0 and all(x in text for x in ['Completed placement consistency check successfully.','Completed routing consistency check successfully.','Circuit successfully routed with a channel width factor','VPR succeeded'])
 r.update(status='pass' if legal else 'fail',legal=legal)
 try:
  if legal:
   validate_contract(Path(arg('--contract')),d/'output.place');r.update(cpd_ns=match(r'Final critical path delay \(least slack\):\s+([0-9.]+) ns',text,'CPD',float),wirelength=match(r'Total wirelength:\s+(\d+)',text,'WL',int))
   r['outputs']={f:{'path':str(d/f),'bytes':(d/f).stat().st_size,'sha256':sha256(d/f)} for f in ['output.place','output.route','stdout.log','stderr.log']}
   accepted,reason=acceptance_reason(r,inc,b0)
  else:accepted,reason=False,'native_failed'
 except Exception as e:accepted,reason=False,repr(e);r['legal']=False
 r['validated_s']=time.monotonic()-start;r['accepted']=accepted and r['validated_s']<=p['baseline_budgets'][case];r['reason']=reason if r['validated_s']<=p['baseline_budgets'][case] else 'validation_after_cutoff'
 if r['accepted']:inc={k:r[k] for k in ['status','legal','cpd_ns','wirelength']};place=str(d/'output.place')
 save();seed+=1
save()
