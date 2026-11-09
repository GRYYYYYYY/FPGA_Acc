"""All-case cost/quality audit; failed or joint-rejected cases never discarded."""
import json,sys
from fractions import Fraction as F
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from pre_route_endpoints import sha
from native_route_work_metrics import extract
ROOT=Path(__file__).resolve().parents[2];base=ROOT/'experiments/native_resume_allfanout_cohort_2026-10-07'
pp,tp=base/'protocol.json',base/'timers.json';p,t=json.loads(pp.read_text()),json.loads(tp.read_text());assert t['protocol_sha256']==sha(pp)
assert len(t['rows'])==24 and [(r['width'],r['index'],r['mode']) for r in t['rows']]==[tuple(x) for x in p['order']]
assert sha(Path(__file__).with_name('cohort_allfanout_trial.py'))==p['producer_sha256']
bindings={str(f):sha(f) for f in (pp,tp,Path(__file__),ROOT/'tools/native_route_work_metrics.py')};runs={}
for timer in t['rows']:
 w,i,mode=timer['width'],timer['index'],timer['mode'];log=base/f'w{w}_m{i}_{mode}.log';assert sha(log)==timer['log_sha256'];bindings[str(log)]=sha(log)
 root=ROOT/f'experiments/native_resume_allfanout_w{w}_m{i}_{mode}_2026-10-07'
 if timer['exit_code']!=0:
  runs[w,i,mode]=(None,None,timer,None);continue
 rp,sp=root/'receipt.json',root/'protocol.json';r,s=json.loads(rp.read_text()),json.loads(sp.read_text());assert r['protocol_sha256']==sha(sp)
 for mapping in (r['files'],s['inputs'],s['sources'],r['canonical']['files']):
  for file,digest in mapping.items():assert sha(file)==digest;bindings[file]=digest
 assert r['canonical']['mismatches']==r['canonical']['fixups']==0 and r['all_target_endpoints_match'] and r['raw_canonical_paths_preserved'] and r['physical_audit']['overflow_units']==0
 assert sum(st['seconds'] for st in r['stages'])<=r['internal_seconds']<=timer['external_seconds']
 assert sum('native' in st for st in r['stages'])==1
 native=next(st['native'] for st in r['stages'] if 'native' in st)
 command=native['command'];assert command[command.index('--min_incremental_reroute_fanout')+1]=='0' and command[command.index('--incremental_reroute_delay_ripup')+1]=='on'
 m=extract((root/'first/run.log').read_text());assert m['routing_success'] and m['native_vpr_succeeded']
 bindings.update({str(rp):sha(rp),str(sp):sha(sp)});runs[w,i,mode]=(r,s,timer,m)
rows=[]
for w in (8,16,32):
 for i in range(4):
  a,ap,at,am=runs[w,i,'workflow'];b,bp,bt,bm=runs[w,i,'cold']
  if a is None or b is None:
   rows.append(dict(width=w,index=i,complete=False,workflow_exit_code=at['exit_code'],cold_exit_code=bt['exit_code'],workflow_seconds=at['external_seconds'],cold_seconds=bt['external_seconds'],joint_nonregression=None));continue
  shared=set(ap['inputs'])&set(bp['inputs']);assert all(ap['inputs'][file]==bp['inputs'][file] for file in shared)
  for suffix in ('target_endpoints.json','target.place','design.net','design.blif','rr_graph.xml'):assert any(file.endswith(suffix) for file in shared)
  assert len(a['physical_audit']['connections'])==len(b['physical_audit']['connections'])
  cp=F(a['cpd_ns'])<=F(b['cpd_ns']);wp=a['wirelength']<=b['wirelength']
  rows.append(dict(width=w,index=i,complete=True,connections=len(a['physical_audit']['connections']),workflow_seconds=at['external_seconds'],cold_seconds=bt['external_seconds'],ratio=at['external_seconds']/bt['external_seconds'],cpd_nonregression=cp,wire_nonregression=wp,joint_nonregression=cp and wp,cpd_pair=[a['cpd_ns'],b['cpd_ns']],wire_pair=[a['wirelength'],b['wirelength']],precritical_decision=a['feedback'],time_win=at['external_seconds']<bt['external_seconds'],workflow_work=am,cold_work=bm))
assert all(sha(file)==digest for file,digest in bindings.items())
result=dict(bindings=bindings,rows=rows,complete_cases=sum(r['complete'] for r in rows),quality_passes=sum(r['joint_nonregression'] is True for r in rows),quality_failures=sum(r['joint_nonregression'] is False for r in rows),workflow_total_seconds=sum(r['external_seconds'] for r in t['rows'] if r['mode']=='workflow'),cold_total_seconds=sum(r['external_seconds'] for r in t['rows'] if r['mode']=='cold'),scope=p['scope']+'; total includes quality-rejected proposed candidates, NOT acceptance/fallback workflow. Cannot claim saving by excluding failures or cost-free rejection; all selected paths valid, QoR failures retained. One pair per case, no stable or heldout claim.')
result['aggregate_ratio']=result['workflow_total_seconds']/result['cold_total_seconds']
(base/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
print([(r['width'],r['index'],r['joint_nonregression'],round(r.get('ratio',0),3),r.get('cpd_pair'),r.get('wire_pair')) for r in rows]);print({k:result[k] for k in ('complete_cases','quality_passes','quality_failures','aggregate_ratio')})
