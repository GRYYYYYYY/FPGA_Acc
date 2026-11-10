"""Small-file aggregation of completed PR0 runs; does not launch experiments."""
import csv,json,pathlib,hashlib,shutil,collections
root=pathlib.Path(__file__).resolve().parents[3];dest=root/'DAC_AUDIT/PR0';runtime=root.parent/'FPGA_Acc_PR0_RUNS_20261110';original=root.parent/'FPGA_Acc'
def writecsv(p,rows):
 if not rows:return
 with p.open('w',newline='') as f:w=csv.DictWriter(f,fieldnames=list(rows[0]),lineterminator="\n");w.writeheader();w.writerows(rows)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
rows=[];times=[];inspections=[];summary={};e=dest/'evidence';e.mkdir(exist_ok=True)
for case in ['diffeq','clma']:
 raw=list(csv.DictReader((runtime/case/'replay.csv').open()));perf=list(csv.DictReader((runtime/case/'performance.csv').open()));extra=list(csv.DictReader((runtime/case/'current_cost_inspection.csv').open()));lookup={r['query']:r for r in extra}
 for r in raw:
  z=lookup[r['query']];prefix=runtime/case/('q'+r['query']);batch=runtime/case/('batch'+r['batch']+'.resources')
  rr={'case':case,**r,'production_commit':'b32afa4303a5574dde7171b4ae6e3d07aeb8a06c','protocol_commit':'b5518828a14c61211bcd0f49600166b04ea48bcc','snapshot_sha256':sha(prefix.with_suffix('.resources')),'batch_snapshot_sha256':sha(batch),'task_sha256':sha(prefix.with_suffix('.task')),'seeds_sha256':sha(prefix.with_suffix('.seeds')),'old_path_current_cost':z['old_path_current_cost'],'S_current_cost':z['current_S_cost'],'old_path_current_cost_diff':z['current_cost_diff'],'old_path_current_capacity_legal':z['old_path_current_capacity_legal'],'terminal_scope':'partial_initial_wave_not_final_route'};rows.append(rr)
 times.extend({'case':case,**r} for r in perf);inspections.extend({'case':case,**r} for r in extra)
 for filename in ['replay.csv','performance.csv','current_cost_inspection.csv','capture_status.json']:shutil.copyfile(runtime/case/filename,e/(case+'_'+filename))
 n=[r for r in raw if r['mode']=='N'];f=[r for r in raw if r['mode']=='F'];p=[r for r in raw if r['mode']=='P'];summary[case]={'queries':len(n),'N_committed':sum(r['commit_status']=='4' for r in n),'P_committed':sum(r['commit_status']=='4' for r in p),'P_rejection_reasons':dict(collections.Counter(r['reason'] for r in p if r['commit_status']!='4')),'F_replays':sum(r['full_valid']=='0' for r in f),'N_path_differences_from_S':sum(int(r['path_diff_S']) for r in n),'N_current_cost_differences_from_S':sum(int(r['current_cost_diff']) for r in extra),'N_new_overuse_candidates':sum(r['old_path_current_capacity_legal']=='0' for r in extra),'score_unique_range':[min(int(r['score_unique']) for r in n),max(int(r['score_unique']) for r in n)],'full_dependency_range':[min(int(r['read_unique']) for r in f),max(int(r['read_unique']) for r in f)],'path_read_range':[min(int(r['read_unique']) for r in n),max(int(r['read_unique']) for r in n)],'queue_peak_max':max(int(r['queue_peak']) for r in n),'repeat_mismatches':sum(r['repeat_equal']!='1' for r in n),'state_mismatches':sum(r['state_consistent']!='1' for r in raw),'performance_ms':{}}
 for mode in 'SFPN':
  sub=[r for r in perf if r['mode']==mode];summary[case]['performance_ms'][mode]={k.removesuffix('_ns')+'_ms':sum(int(r[k]) for r in sub)/1e6 for k in ['search_total_ns','search_kernel_ns','validation_ns','commit_total_ns','commit_kernel_ns']}
writecsv(dest/'replay_cases.csv',rows);writecsv(dest/'timing_samples.csv',times);writecsv(dest/'current_cost_inspection.csv',inspections)
for name in ['witnesses.csv','shared_trunk.json']:shutil.copyfile(runtime/'counterexamples'/name,dest/'counterexamples'/name)
ledger=json.loads((runtime/'run_ledger.json').read_text());summary['resources']={'subprocess_wall_s':sum(x['wall_s'] for x in ledger),'diagnostic_wall_excluding_compiles_s':sum(x['wall_s'] for x in ledger if 'compile' not in x['name']),'max_rss_kib':max(int((runtime/(x['name']+'.time')).read_text().strip().split(',')[-1]) for x in ledger),'timeouts':sum(x['status']=='timeout' for x in ledger),'failed_subprocesses':sum(x['exit_code']!=0 for x in ledger),'note':'outer monotonic subprocess wall including compiler; peak RSS max child not sum; RLIMIT_AS 8 GiB each sequential job'}
for name in ['run_ledger.json','primary_run_ledger.json','executable_identity.json','supplement_identity.json']:shutil.copyfile(runtime/name,e/name)
for x in ledger:
 for suffix in ['time','stderr','stdout']:
  p=runtime/(x['name']+'.'+suffix)
  if p.stat().st_size:shutil.copyfile(p,e/p.name)
(dest/'summary.json').write_text(json.dumps(summary,indent=2)+'\n')
artifacts=[]
# Only newly created bounded runtime directory, never old project work trees.
for p in sorted(runtime.rglob('*')):
 if p.is_file():artifacts.append({'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'rehashed_this_run':True,'uploaded_as_binary':False,'scope':'new_PR0_only'})
writecsv(dest/'local_artifact_index.csv',artifacts)
old=[]
for matrix in ['balanced_adaptive1_matrix_2026-08-28','balanced_pathreads_matrix_2026-08-28']:
 case=original/'projects/persistroute/experiments'/matrix/'clma_seed1_cw200';paths=[case/'case_result.json',case/'run/host_result.json',case/'run/clma.accelerated_iterations.csv',case/'run/clma.performance_iterations.csv'];j=json.loads(paths[0].read_text());iters=list(csv.DictReader(paths[2].open()));host=j['stages']['hbm_cmodel'];old.append({'case':str(case),'source_commit':'unknown','executable_sha256':'unknown','exact_queue_depth':'unknown','exact_transaction_capacity':'unknown','per_query_flags':'unknown','evidence_files':[{'path':str(p),'bytes':p.stat().st_size,'sha256':sha(p),'rehashed_this_run':True} for p in paths],'host_summary':{k:host[k] for k in ['iterations','tasks','routed_tasks','searches','overused_resources','exit_status','legal','wall_s_measured','search_ms','commit_ms']},'summed_iteration_failed':sum(int(r['failed']) for r in iters),'failure_classes':{'count_overflow':'unknown','pool_overflow':'unknown','queue_overflow':'unknown','unreachable':'unknown','version_conflict':'unknown','budget_or_iteration_cap':'30_iterations' if host['exit_status']!=0 else 'not_terminal_failure'},'last_iteration':iters[-1]})
(dest/'historical_attribution.json').write_text(json.dumps(old,indent=2)+'\n')
print(json.dumps(summary,indent=2))
