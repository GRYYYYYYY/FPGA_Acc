#!/usr/bin/env python3
"""Copy compact existing evidence, preserve all failures; no experiment execution."""
from pathlib import Path
import json,csv,hashlib,shutil
D=Path(__file__).resolve().parent;ROOT=Path('/inspire/hdd/project/siinovarch-fpga-chip/guoruiyuan-253208540291/FPGA_Acc');E=ROOT/'projects/tileplace/experiments'; C=E/'tileplace_new_cohort_2026-09-29'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def resolve(p):return ROOT/str(p).split('/FPGA_Acc/',1)[1] if '/FPGA_Acc/' in str(p) else Path(p)
def csvout(p,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
index=[]
def cp(src,rel,expected=None):
 src=resolve(src);target=D/'evidence'/rel;target.parent.mkdir(parents=True,exist_ok=True)
 assert src.stat().st_size<8*1024**2,(src,src.stat().st_size)
 digest=sha(src)
 if expected:assert digest==expected,(src,digest,expected)
 shutil.copyfile(src,target)
 index.append({'relative_path':str(target.relative_to(D)),'bytes':src.stat().st_size,'sha256':digest,'source_path':str(src),'kind':'original','verified_this_round':True,'historical_source_commit':'unknown'})
 return str(target.relative_to(D))
summary=json.loads((C/'summary.json').read_text());audit=json.loads((C/'final_audit.json').read_text())
cp(C/'summary.json','history/cohort/summary.json');cp(C/'final_audit.json','history/cohort/final_audit.json')
allcases=[];trials=[];samples=[];breakdown=[];external=[]
for c in summary['cases']:
 case=c['design'];a=next(x for x in audit['cases'] if x['design']==case)
 row={'project':'TilePlace','design':case,'seed':1,'channel_width':200,'status':c['status'],'failure_stage':c.get('failed_stage',''),'error':c.get('error',''),'source_commit':'unknown','implementation_sha256':'2fa6e2324a971d8489bba12d49115f91d0a56874c0ee5200224d72e4f8a9f689','baseline_legal':c.get('baseline',{}).get('legal','unknown'),'baseline_cpd_ns':c.get('baseline',{}).get('cpd_ns','unknown'),'baseline_wl':c.get('baseline',{}).get('wirelength','unknown'),'final_legal':c.get('final',{}).get('legal','unknown'),'final_cpd_ns':c.get('final',{}).get('cpd_ns','unknown'),'final_wl':c.get('final',{}).get('wirelength','unknown'),'native_trials':a.get('verified_native_trials',0),'historical_cohort_aggregate_s':c['end_to_end_s'],'time_scope':'prep + two repeat processes + driver overhead; NOT single-run; no divide-by-two','evidence':'evidence/history/cohort/summary.json','repeat_count':len(c.get('repeats',[]))}
 if c['status']=='fail':
  baseline_file=C/case/'baseline/baseline.json'
  if baseline_file.exists():
   b=json.loads(baseline_file.read_text());row.update(baseline_legal=b['legal'],baseline_cpd_ns=b['cpd_ns'],baseline_wl=b['wirelength'],baseline_evidence=f'evidence/history/preparation/{case}/baseline/baseline.json')
  else:row['baseline_legal']='not_completed'
  row.update(final_legal='not_run',final_cpd_ns='not_run',final_wl='not_run')
 row['cpu_refinement_executed']=c['status']=='pass'
 row['implementation_binding']='observed_in_both_repeat_reports' if c['status']=='pass' else 'planned_protocol_only_refinement_not_run'
 allcases.append(row)
 for st in c['stages']:
  breakdown.append({'run_id':case+'_historical_prep','case':case,'stage':st['name'],'parent':'historical_cohort_aggregate','wall_s':st['elapsed_s'],'status':'completed' if st['returncode']==0 else 'failed','scope':'historical stage subprocess, not new cold timer'})
 for i,rr in enumerate(c.get('repeats',[])):
  path=resolve(rr['path']);r=json.loads(path.read_text()); assert r['provenance']['implementation']['sha256']==row['implementation_sha256']
  rp=cp(path,f'history/cohort/{case}/run_{i:02}/report.json',rr['sha256'])
  cp(path.parent/'timing.json',f'history/cohort/{case}/run_{i:02}/timing.json')
  for f in path.parent.glob('*.command.json'):cp(f,f'history/cohort/{case}/run_{i:02}/'+f.name)
  for f in path.parent.glob('*.process.json'):cp(f,f'history/cohort/{case}/run_{i:02}/'+f.name)
  samples.append({'run_id':case+f'_historical_{i}','case':case,'kind':'historical_refinement','arm':'historical_prefix','status':'completed','returncode':rr['process']['returncode'],'outer_wall_s':rr['process']['elapsed_s'],'evidence':rp,'source_commit':'unknown'})
  for j,t in enumerate(r['trials']):
   native=resolve(t['closure']['report_path']);n=json.loads(native.read_text());rel=cp(native,f'history/native/{case}_{i}_{j:02}.json',t['closure']['report_sha256'])
   trials.append({'project':'TilePlace','design':case,'repeat':i,'trial':j,'seed':1,'channel_width':200,'source_commit':'unknown','implementation_sha256':row['implementation_sha256'],'accepted':t['accepted'],'decision':t['reason'],'legal':n['legal'],'returncode':n['returncode'],'wl':n['wirelength'],'cpd_ns':n['cpd_ns'],'native_wall_s':n['wall_s'],'candidate_sha256':t['candidate_place']['sha256'],'candidate_local_path':str(resolve(t['candidate_place']['path'])),'native_original_path':str(native),'native_sha256':t['closure']['report_sha256'],'evidence_path':rel,'search_report':rp})
   for value in list(n['outputs'].values())+list(n['inputs'].values()):
    f=resolve(value['path']);external.append({'path':str(f),'bytes':f.stat().st_size if f.exists() else 'unknown','sha256':value['sha256'],'hash_origin':'native receipt, phase1 accepted verification; not rehashed','reason':'raw native output retained locally'})
 if c['status']!='pass':
  for l in a['logs']:cp(l['path'],f'history/failures/{case}/'+Path(l['path']).name,l['sha256'])
  samples.append({'run_id':case+'_historical_failed_stage','case':case,'kind':'historical_failed_prep','arm':'historical','status':'failed','returncode':a['process']['returncode'],'outer_wall_s':a['process']['elapsed_s'],'evidence':'evidence/history/cohort/final_audit.json','source_commit':'unknown'})
  breakdown.append({'run_id':case+'_historical_prep','case':case,'stage':c['failed_stage'],'parent':'historical_cohort_aggregate','wall_s':a['process']['elapsed_s'],'status':'failed','scope':'failed stage retained'})
# Small preparation command/process receipts, including all failed stages.
for c in summary['cases']:
 for folder in ['baseline','inputs']:
  directory=C/c['design']/folder
  files=set(directory.glob('*.command.json'))|set(directory.glob('*.process.json'))
  if folder=='baseline':files|={directory/n for n in ['command.json','process.json','baseline.json'] if (directory/n).exists()}
  for f in sorted(files):cp(f,f"history/preparation/{c['design']}/{folder}/{f.name}")
assert len(allcases)==13 and len(trials)==404
for name in ['tileplace_v4_timing_parser_audit_2026-09-29.json','tileplace_fixed_development_audit_2026-09-29.json','tileplace_frontier_ablation_audit_2026-09-29.json','tileplace_v4_prefix_timing_comparison_2026-09-29.json','tileplace_v4_generic_timing_summary_2026-09-29.json','tileplace_feedback_rollback_regression_audit_2026-09-29.json','tileplace_feedback_rollback_fix_2026-09-29.json','tileplace_feedback_rollback_implementation_2026-09-29.json','tileplace_v4_generic_implementation_2026-09-29.json','tileplace_v4_prefix_implementation_2026-09-29.json','tileplace_new_cohort_protocol_v2_2026-09-29.json','tileplace_v4_preregistration_2026-09-03.json']:
 cp(E/name,'history/supporting/'+name)
for name in ['tileplace_v4_prefix_timing_diffeq_2026-09-29/summary.json','tileplace_frontier_ablation_2026-09-29/summary.json','tileplace_fixed_development_2026-09-29/summary.json']:
 if (E/name).exists():cp(E/name,'history/supporting/'+name.replace('/','_'))
csvout(D/'all_cases.csv',allcases);csvout(D/'evidence/historical_trial_index.csv',trials);csvout(D/'evidence/historical_timing_samples.csv',samples);csvout(D/'evidence/historical_preparation.csv',breakdown)
external={r['path']:r for r in external};csvout(D/'evidence/historical_local_artifacts.csv',list(external.values()));csvout(D/'evidence/history_copy_index.csv',index)
print('copied',len(index),'files',sum(x['bytes'] for x in index),'bytes; cases',len(allcases),'trials',len(trials))
