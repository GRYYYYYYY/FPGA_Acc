#!/usr/bin/env python3
"""Derive small tables from immutable historical receipts and completed pilot outputs."""
from pathlib import Path
import json,csv,hashlib,shutil,statistics,collections,time
D=Path(__file__).resolve().parent;P=json.loads((D/'PILOT_PROTOCOL.json').read_text());R=Path(P['output_root'])
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def readcsv(p):return list(csv.DictReader(p.open()))
def csvout(p,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=keys);w.writeheader();w.writerows(rows)
def dump(p,d):p.write_text(json.dumps(d,indent=2,sort_keys=True)+'\n')
index=[];locals=[]
def cp(src,rel):
 target=D/'evidence'/rel;target.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(src,target)
 index.append({'relative_path':str(target.relative_to(D)),'bytes':src.stat().st_size,'sha256':sha(src),'source_path':str(src),'kind':'original','verified_this_round':True});return str(target.relative_to(D))
samples=readcsv(D/'evidence/historical_timing_samples.csv');tree=readcsv(D/'evidence/historical_preparation.csv');metrics=[];trials=[]
def timing_tree(run,case,outer,t,native,ev):
 vals={'preparation':t['preparation_wall_s'],**t['search_stage_wall_s'],'search_other':t['search_other_wall_s'],'output':t['output_wall_s'],'external_unattributed':outer-t['flow_wall_s']}
 assert min(vals.values())>=-1e-5 and abs(sum(vals.values())-outer)<1e-5
 tree.append({'run_id':run,'case':case,'stage':'outer_total','parent':'none','wall_s':outer,'exclusive_partition':False,'evidence':ev})
 for k,v in vals.items():tree.append({'run_id':run,'case':case,'stage':k,'parent':'outer_total','wall_s':v,'exclusive_partition':True,'evidence':ev})
 tree.append({'run_id':run,'case':case,'stage':'native_vpr_sum','parent':'oracle_driver','wall_s':native,'exclusive_partition':False,'evidence':ev})
 for k in ['index_build_s','cache_invalidation_s']:
  if k in t.get('mechanism_profile',{}):tree.append({'run_id':run,'case':case,'stage':k,'parent':'diagnostic_nested_across_phases','wall_s':t['mechanism_profile'][k],'exclusive_partition':False,'evidence':ev})
 return vals
# historical single-process samples are real individual timers, never cohort/2.
for row in samples:
 if row['kind']!='historical_refinement':continue
 path=D/row['evidence'];t=json.loads((path.parent/'timing.json').read_text());r=json.loads(path.read_text())
 native=sum(float(x['native_wall_s']) for x in readcsv(D/'evidence/historical_trial_index.csv') if x['design']==row['case'] and int(x['repeat'])==int(row['run_id'].rsplit('_',1)[1]))
 timing_tree(row['run_id'],row['case'],float(row['outer_wall_s']),t,native,str((path.parent/'timing.json').relative_to(D)))
# Retain every original timing sample of the historical generic/prefix comparison,
# but never mix these different source identities into the new paired estimator.
for label,name in [('historical_generic','tileplace_v4_generic_timing_summary_2026-09-29.json'),('historical_prefix','tileplace_v4_prefix_timing_diffeq_2026-09-29_summary.json')]:
 f=D/'evidence/history/supporting'/name;legacy=json.loads(f.read_text())
 for j,lr in enumerate(legacy['runs']):
  samples.append({'run_id':label+f'_{j}','case':legacy['case'],'kind':'historical_warmup' if lr['warmup'] else 'historical_timing','arm':label,'status':'completed_as_reported_in_historical_summary','returncode':lr.get('returncode','unknown_not_in_summary'),'outer_wall_s':lr['process_wall_s'],'evidence':str(f.relative_to(D)),'source_commit':'unknown','implementation_sha256':legacy['implementation_sha256']})
summary=json.loads((R/'summary.json').read_text());cp(R/'summary.json','pilot/summary.json');cp(R/'pre_run.json','pilot/pre_run.json')
for row in summary['runs']:
 run=row['run_id'];w=R/run;base={'run_id':run,'case':row['case'],'kind':row['kind'],'arm':row['arm'],'pair':row['pair'],'status':row.get('status','not_started'),'returncode':row.get('returncode','unknown'),'outer_wall_s':row.get('outer_wall_s','unknown'),'offline_audit_wall_s':row.get('offline_audit_wall_s','unknown'),'exact_match':row.get('exact_match','not_applicable'),'source_commit':summary['pre_run']['pre_run_commit'],'implementation_sha256':P['implementation']['sha256'] if row['arm']!='B1' else sha(D/'baseline_smoke.py')}
 for name in ['process.json','command.json','timing.json','report.json','exact_signature.json','native_command.json']:
  if (w/name).exists():cp(w/name,f'pilot/{run}/{name}')
 for name in ['stderr.log','native.stderr.log']:
  if (w/name).exists() and (w/name).stat().st_size:cp(w/name,f'pilot/{run}/{name}')
 base['evidence']='evidence/pilot/'+run+'/process.json' if w.exists() else 'evidence/pilot/summary.json';samples.append(base)
 if row.get('status')!='completed':
  partial=[]
  for j,f in enumerate(sorted((w/'work').glob('trial_*/vpr_native_closure.json'))):
   n=json.loads(f.read_text());rel=cp(f,f'pilot/{run}/partial_native_{j:02}.json')
   entry={'run_id':run,'case':row['case'],'arm':row['arm'],'trial':f.parent.name,'accepted':'unknown_no_terminal_controller_report','reason':'partial run; do not infer final success','legal':n.get('legal'),'cpd_ns':n.get('cpd_ns'),'wl':n.get('wirelength'),'native_wall_s':n.get('wall_s'),'candidate_sha256':n.get('inputs',{}).get('golden_place',{}).get('sha256'),'evidence':rel,'native_sha256':sha(f),'partial':True}
   trials.append(entry);partial.append(entry)
   for v in list(n.get('outputs',{}).values())+list(n.get('inputs',{}).values()):
    q=Path(v['path']);locals.append({'path':str(q),'bytes':q.stat().st_size if q.exists() else 'unknown','sha256':v['sha256'],'hash_origin':'partial-run native receipt','reason':'retained local artifact, no completed flow claim'})
  if w.exists():
   case=next(c for c in P['cases'] if c['case']==row['case']);cmd=case['command_template'];baseline_path=cmd[cmd.index('--baseline-closure')+1]
   dump(D/'evidence/pilot'/run/'partial_state.json',{'status':row.get('status'),'original_legal_incumbent_path':baseline_path,'completed_native_receipts':partial,'controller_final':'unknown; no terminal report','budget_admissible_new_output':'unknown; no reconstruction of a successful timed run','raw_outputs_retained':str(w)})
  continue
 report=json.loads((w/'report.json').read_text())
 if row['arm']=='B1':
  tree+=[{'run_id':run,'case':row['case'],'stage':'outer_total','parent':'none','wall_s':row['outer_wall_s'],'exclusive_partition':False},{'run_id':run,'case':row['case'],'stage':'native_place_route_analysis','parent':'outer_total','wall_s':report['native_wall_s'],'exclusive_partition':True},{'run_id':run,'case':row['case'],'stage':'preparation_check_write_startup','parent':'outer_total','wall_s':row['outer_wall_s']-report['native_wall_s'],'exclusive_partition':True}]
  # Compact log retains command, SA evidence and native success markers. Full log hash remains in report.
  log=(w/'native.stdout.log').read_text().splitlines();keys=['Version:','Revision:','initial placement','Initial placement','Placement took','Placement cost','Final critical path','Total wirelength','consistency check','successfully routed','VPR succeeded','Placement Quench','Reading placement','Starting placement','Starting temperature','Reading constraints','No SDC','default constraints']
  excerpt='\n'.join(f'{i+1}: {l}' for i,l in enumerate(log) if any(k in l for k in keys))+'\n';(D/'evidence/pilot'/run/'native_excerpt.txt').write_text(excerpt)
  continue
 t=json.loads((w/'timing.json').read_text());native=0;accepted_native=rejected_native=0
 for j,tr in enumerate(report['trials']):
  f=Path(tr['closure']['report_path']);n=json.loads(f.read_text());assert sha(f)==tr['closure']['report_sha256'];rel=cp(f,f'pilot/{run}/native_{j:02}.json');native+=n['wall_s']
  if tr['accepted']:accepted_native+=n['wall_s']
  else:rejected_native+=n['wall_s']
  trials.append({'run_id':run,'case':row['case'],'arm':row['arm'],'trial':j,'accepted':tr['accepted'],'reason':tr['reason'],'legal':n['legal'],'cpd_ns':n['cpd_ns'],'wl':n['wirelength'],'native_wall_s':n['wall_s'],'candidate_sha256':tr['candidate_place']['sha256'],'evidence':rel,'native_sha256':sha(f)})
  for value in list(n['outputs'].values())+list(n['inputs'].values()):
   f=Path(value['path']);locals.append({'path':str(f),'bytes':f.stat().st_size if f.exists() else 'unknown','sha256':value['sha256'],'hash_origin':'new native receipt; not rehashed by packaging','reason':'raw native artifacts retained locally'})
 vals=timing_tree(run,row['case'],row['outer_wall_s'],t,native,base['evidence'].replace('process.json','timing.json'))
 oe=[e['wall_s'] for e in t['events'] if e['stage']=='oracle_driver'];assert len(oe)==len(report['trials'])
 metrics.append({**base,**vals,**t.get('mechanism_profile',{}),'native_sum_s':native,'accepted_native_s':accepted_native,'rejected_native_s':rejected_native,'rejected_oracle_driver_s':sum(v for v,tr in zip(oe,report['trials']) if not tr['accepted']),'native_fraction':native/row['outer_wall_s'],'proposal_fraction':vals['proposal']/row['outer_wall_s'],'proposal_only_infinite_speedup_upper_bound':1/(1-vals['proposal']/row['outer_wall_s']),'native_closures':report['closure_calls'],'accepted_trials':sum(tr['accepted'] for tr in report['trials']),'rejected_trials':sum(not tr['accepted'] for tr in report['trials']),'accepted_transactions':report['accepted_transactions'],'proposals_recorded':sum(x['proposals'] for x in report['phases']),'final_legal':report['final']['legal'],'final_cpd_ns':report['final']['cpd_ns'],'final_wl':report['final']['wirelength']})
rows=[]
for case in ['diffeq','clma','spla']:
 rr=[r for r in metrics if r['case']==case and r['kind']=='measured'];arms={a:[r for r in rr if r['arm']==a] for a in 'AB'}
 row={'case':case,'exposure':'development','A_count':len(arms['A']),'B_count':len(arms['B'])}
 if arms['A'] and arms['B']:
  for a in 'AB':row[a+'_median_s']=statistics.median(r['outer_wall_s'] for r in arms[a]);row[a+'_proposal_median_s']=statistics.median(r['proposal'] for r in arms[a]);row[a+'_proposal_fraction_mean']=statistics.mean(r['proposal_fraction'] for r in arms[a])
  row['B_over_A']=row['B_median_s']/row['A_median_s'];row['exact_all']=all(r['exact_match'] for r in rr);row['cpd_ns']=arms['A'][0]['final_cpd_ns'];row['wl']=arms['A'][0]['final_wl']
  row['paired_ratios']=[next(r['outer_wall_s'] for r in arms['B'] if r['pair']==a['pair'])/a['outer_wall_s'] for a in arms['A'] if any(b['pair']==a['pair'] for b in arms['B'])]
 rows.append(row)
dump(D/'evidence/pilot/derived_summary.json',{'cases':rows,'total_process_wall_s':sum(r.get('outer_wall_s',0) for r in summary['runs']),'warmup_s':sum(r.get('outer_wall_s',0) for r in summary['runs'] if r['kind']=='warmup'),'measured_s':sum(r.get('outer_wall_s',0) for r in summary['runs'] if r['kind']=='measured'),'baseline_smoke_s':sum(r.get('outer_wall_s',0) for r in summary['runs'] if r['kind']=='baseline_smoke'),'offline_audit_s':sum(r.get('offline_audit_wall_s',0) for r in summary['runs']),'status_counts':dict(collections.Counter(r.get('status','not_started') for r in summary['runs'])),'supervisor_elapsed_s':summary['supervisor_elapsed_s']})
for trial in trials:
 case=next(c for c in P['cases'] if c['case']==trial['case'])
 trial.update(project='TilePlace',seed=case['seed'],channel_width=case['channel_width'],source_commit=summary['pre_run']['pre_run_commit'],implementation_sha256=P['implementation']['sha256'])
csvout(D/'timing_samples.csv',samples);csvout(D/'timing_breakdown.csv',tree);csvout(D/'evidence/pilot/run_metrics.csv',metrics);csvout(D/'evidence/pilot/trial_index.csv',trials);csvout(D/'evidence/pilot/local_artifacts.csv',list({r['path']:r for r in locals}.values()));csvout(D/'evidence/pilot_copy_index.csv',index)
print(json.dumps(rows,indent=2));print('total observed subprocess wall seconds',sum(r.get('outer_wall_s',0) for r in summary['runs']))
