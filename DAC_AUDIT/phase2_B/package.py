"""Package only new compact receipts; never copy raw circuits/routes or the old evidence pack."""
from pathlib import Path
import csv,json,hashlib,shutil,statistics,collections
D=Path(__file__).resolve().parent;P=json.loads((D/'PROTOCOL.json').read_text());R=Path(P['output_root']);E=D/'evidence';E.mkdir(exist_ok=True)
def load(p):return json.loads(p.read_text())
def dump(p,x):p.write_text(json.dumps(x,indent=2,sort_keys=True)+'\n')
def csvout(p,rows):
 keys=list(dict.fromkeys(k for r in rows for k in r))
 with p.open('w',newline='') as f:w=csv.DictWriter(f,keys);w.writeheader();w.writerows(rows)
index=[]
def copy(f,rel):
 dest=E/rel;dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);index.append({'path':str(dest.relative_to(D)),'source_path':str(f),'bytes':f.stat().st_size,'sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
s=load(R/'summary.json');copy(R/'summary.json','summary.json');copy(R/'pre_run.json','pre_run.json');samples=[];profiles=[];cost=[];correct={};eq=[];artifacts=[]
for row in s['rows']:
 rid=row['id'];w=R/rid
 for name in ['process.json','observations.json','profile.json','report.json','timing.json','baseline.json','difference.json']:
  if (w/name).exists():copy(w/name,rid+'/'+name)
 for name in ['stdout.log','stderr.log']:
  f=w/name
  if f.exists() and f.stat().st_size and (rid=='unit' or name=='stderr.log'):
   # Text only; compact error/negative-control evidence.
   copy(f,rid+'/'+name+'.txt')
 o=load(w/'observations.json') if (w/'observations.json').exists() else {};samples.append({**{k:row.get(k,'unknown') for k in ['id','case','arm','mode','status','returncode','outer_s']},'self_peak_rss_kib':o.get('maxrss_kib','unknown'),'new_cold_s':'unknown','source_commit':s['pre_run_commit'],'effective_source_manifest_sha256':hashlib.sha256((D/'source_manifest.json').read_bytes()).hexdigest(),'native_exact':row.get('native_exact','not_checked'),'enumeration_exact':row.get('enumeration_exact','not_checked')})
 if o:
  for block in o['reuse']:
   for ep in block['epochs']:
    profiles.append({'run_id':rid,'case':row['case'],'arm':row['arm'],'mode':row['mode'],**{k:ep[k] for k in ['version','lifetime_s','distinct_keys','calls']},'before_queries':ep['roles'].get('before',0),'candidate_queries':ep['roles'].get('candidate',0),'repeat_fraction':1-ep['distinct_keys']/ep['calls'] if ep['calls'] else 'not_observed','total_stats':json.dumps(block['stats'],sort_keys=True)})
  if row['mode']=='correctness':correct[rid]={'records':o['count'],'counts':o['counts'],'chunks':o['chunks'],'native_exact':row.get('native_exact'),'enumeration_exact':row.get('enumeration_exact'),'evidence':'evidence/'+rid+'/observations.json'}
 if (w/'timing.json').exists():
  t=load(w/'timing.json');outer=row['outer_s'];parts={'preparation':t['preparation_wall_s'],**t['search_stage_wall_s'],'search_other':t['search_other_wall_s'],'write':t['output_wall_s'],'external_and_diagnostic_finalization':outer-t['flow_wall_s']}
  assert abs(sum(parts.values())-outer)<1e-5
  for stage,value in parts.items():cost.append({'run_id':rid,'scope':'full_run_exclusive','stage':stage,'seconds':value})
 if (w/'report.json').exists() and (w/'timing.json').exists():
  rep=load(w/'report.json');tim=load(w/'timing.json');oracle=[x['wall_s'] for x in tim['events'] if x['stage']=='oracle_driver'];assert len(oracle)==len(rep['trials'])
  cost.append({'run_id':rid,'scope':'nested_in_oracle_do_not_add','stage':'rejected_oracle_driver','seconds':sum(v for v,tr in zip(oracle,rep['trials']) if not tr['accepted'])})
 if (w/'profile.json').exists():
  for p in load(w/'profile.json'):
   cost.append({'run_id':rid,'scope':'first_proposal_diagnostic_function_self','stage':p['function'],'seconds':p['self_s'],'calls':p['calls'],'cumulative_s_do_not_add':p['cumulative_s'],'file':p['file'],'line':p['line']})
 for f in sorted(w.glob('work/trial_*/vpr_native_closure.json')):
  copy(f,rid+'/native/'+f.parent.name+'.json');n=load(f)
  for v in list(n.get('inputs',{}).values())+list(n.get('outputs',{}).values()):
   q=Path(v['path']);artifacts.append({'path':str(q),'bytes':q.stat().st_size if q.exists() else 'unknown','sha256':v.get('sha256','unknown'),'origin':'native receipt'})
 if row['mode']=='baseline' and (w/'baseline.json').exists():
  b=load(w/'baseline.json');eq.append({'case':row['case'],'arm':'native_fresh_SA','budget_s':b['budget_s'],'source_run':rid,'legal':b['incumbent']['legal'],'cpd_ns':b['incumbent']['cpd_ns'],'wl':b['incumbent']['wirelength'],'completed_candidates':sum(t.get('status')=='pass' and t.get('validated_s',1e9)<=b['budget_s'] for t in b['trials']),'accepted':sum(t.get('accepted',False) for t in b['trials']),'interrupted':sum(t.get('status')=='deadline_interrupted' for t in b['trials']),'charged_outer_s':row['outer_s'],'time_boundary':'outer monotonic; full validation before cutoff'})
  for t in b['trials']:
   for v in t.get('outputs',{}).values():artifacts.append({**v,'origin':'new baseline receipt'})
 if row['mode']=='performance' and row.get('status')=='completed' and row.get('native_exact'):
  rep=load(w/'report.json');budget=P['baseline_budgets'][row['case']];b0=rep['baseline'];inc=b0;count=accepted=0;offset=max(0,row['outer_s']-o['wall_s']);arrivals=[]
  for tr in rep['trials']:
   at=tr['completed_elapsed_s']+offset
   if at<=budget:
    count+=1
    if tr['accepted']:inc=tr['closure'];accepted+=1;arrivals.append({'elapsed_upper_s':at,'cpd_ns':inc['cpd_ns'],'wirelength':inc['wirelength']})
  eq.append({'case':row['case'],'arm':row['arm'],'budget_s':budget,'source_run':rid,'legal':inc['legal'],'cpd_ns':inc['cpd_ns'],'wl':inc['wirelength'],'completed_candidates':count,'accepted':accepted,'charged_outer_s':row['outer_s'],'time_boundary':'reused performance run; startup+finalization residual conservatively added to acceptance timestamp; not paired against native loop'})
  dump(E/rid/'time_quality.json',arrivals)
copy(R/'unit/stdout.log','unit_result.txt')
csvout(D/'runtime_samples.csv',samples);csvout(D/'reuse_profile.csv',profiles);csvout(D/'cost_breakdown.csv',cost);csvout(D/'equal_budget_pilot.csv',eq);dump(D/'correctness_summary.json',{'runs':correct,'unit':json.loads((R/'unit/stdout.log').read_text()),'scope':'all instrumented enumeration/decision boundaries; not arbitrary-input proof','blocked_cases':s['blocked']});csvout(E/'raw_local_artifacts.csv',list({r['path']:r for r in artifacts}.values()));csvout(E/'copied_index.csv',index)
print(json.dumps({'total_s':s['total_subprocess_s'],'status':dict(collections.Counter(r['status'] for r in s['rows'])),'equal_budget':eq},indent=2))
# Separately preregistered diagnostics share the same total budget and timing table.
supp=load(R/'supplemental_summary.json');copy(R/'supplemental_summary.json','supplemental_summary.json')
for row in supp['runs']:
 w=R/row['id'];o=load(w/'stdout.json') if row['status']=='completed' else {}
 for name in ['stdout.json','stderr.txt','process.json']:copy(w/name,row['id']+'/'+name)
 samples.append({'id':row['id'],'case':'diffeq+clma' if row['id']=='micro_cost' else 'synthetic','arm':'diagnostic','mode':'diagnostic','status':row['status'],'returncode':row['returncode'],'outer_s':row['outer_s'],'self_peak_rss_kib':o.get('maxrss_kib','unknown'),'new_cold_s':'unknown','source_commit':row['pre_run_commit'],'protocol_commit':row['protocol_commit']})
 cost.append({'run_id':row['id'],'scope':'diagnostic_outer','stage':'complete_process','seconds':row['outer_s']})
 if row['id']=='micro_cost':
  for case in o['cases']:
   for stage,seconds in case['seconds'].items():cost.append({'run_id':row['id'],'case':case['case'],'scope':'isolated_operation_diagnostic_do_not_sum','stage':stage,'seconds':seconds})
cost.append({'run_id':'unit','scope':'diagnostic_outer','stage':'complete_process','seconds':s['rows'][0]['outer_s']})
csvout(D/'runtime_samples.csv',samples);csvout(D/'cost_breakdown.csv',cost);csvout(E/'copied_index.csv',index)
correctness=load(D/'correctness_summary.json');correctness['synthetic_fixture']=load(R/'fixture/stdout.json');dump(D/'correctness_summary.json',correctness)
