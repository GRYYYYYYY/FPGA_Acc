#!/usr/bin/env python3
"""Read existing evidence only; never execute project tools or modify source records.
Usage: python3 DAC_AUDIT/verify_phase1.py /absolute/path/to/original/FPGA_Acc
Historical paths are mapped by their /FPGA_Acc/ suffix; expected SHA is mandatory
for a MATCH result. This is a bounded integrity audit, not a new native run.
"""
import csv, hashlib, json, sys
from pathlib import Path
from datetime import datetime, timezone
ROOT=Path(sys.argv[1]).resolve(); OUT=Path(__file__).resolve().parent
checks=[]; cache={}
def resolve(s,base=None):
 p=Path(s)
 if '/FPGA_Acc/' in str(p):return ROOT/str(p).split('/FPGA_Acc/',1)[1]
 if p.is_absolute():return p
 return (base or ROOT)/p
def check(s,expected=None,base=None):
 p=resolve(s,base); item={'original_path':str(s),'resolved_path':str(p),'expected_sha256':expected,'bytes':None,'sha256':None}
 if not p.is_file():item['status']='MISSING'
 else:
  item['bytes']=p.stat().st_size
  if item['bytes']>16*1024*1024:item['status']='DEFERRED_LARGE'
  else:
   if str(p) not in cache:cache[str(p)]=hashlib.sha256(p.read_bytes()).hexdigest()
   item['sha256']=cache[str(p)];item['status']=('MATCH' if expected==item['sha256'] else 'MISMATCH') if expected else 'HASHED_NO_PRIOR_BINDING'
 checks.append(item);return p,item

def read(s,expected=None,base=None):
 p,_=check(s,expected,base);return json.loads(p.read_text())
def refs(d):
 if isinstance(d,dict):
  for a,b in [('path','sha256'),('report_path','report_sha256'),('report','report_sha256')]:
   if isinstance(d.get(a),str) and isinstance(d.get(b),str) and len(d[b])==64:check(d[a],d[b])
  for v in d.values():refs(v)
 elif isinstance(d,list):
  for v in d:refs(v)
summary={'observed_utc':datetime.now(timezone.utc).isoformat(),'baseline_commit':'b32afa4303a5574dde7171b4ae6e3d07aeb8a06c','scope':'Existing record integrity and source inspection; no solver, simulation, native validation or formal proof executed.'}
# All thirteen cases, both repeats, all native trial receipts, candidate and final placements.
s=read('projects/tileplace/experiments/tileplace_new_cohort_2026-09-29/summary.json');a=read('projects/tileplace/experiments/tileplace_new_cohort_2026-09-29/final_audit.json');refs(a)
case_rows=[];trials=0;native_ok=0;implementations=set()
for c in s['cases']:
 refs(c)
 for rep in c['repeats']:
  r=read(rep['path'],rep['sha256']);refs(r)
  implementations.add(r['provenance']['implementation']['sha256'])
  for t in r['trials']:
   cl=t['closure'];doc=read(cl['report_path'],cl['report_sha256']);trials+=1
   native_ok+=doc.get('legal') is True and doc.get('returncode')==0
   assert doc.get('wirelength')==cl.get('wirelength') and doc.get('cpd_ns')==cl.get('cpd_ns')
 case_rows.append({'project':'TilePlace','design':c['design'],'status':c['status'],'failed_stage':c.get('failed_stage',''),'baseline_wl':c.get('baseline',{}).get('wirelength',''),'final_wl':c.get('final',{}).get('wirelength',''),'baseline_cpd_ns':c.get('baseline',{}).get('cpd_ns',''),'final_cpd_ns':c.get('final',{}).get('cpd_ns',''),'whole_cohort_case_s':c.get('end_to_end_s',''),'scope':'existing cohort incl preparation and both repeats; not one-run runtime'})
summary['tileplace_cohort']={'cases':len(case_rows),'successful_cases':s['successful_cases'],'trial_receipts_checked':trials,'native_legal_exit0_receipts':native_ok,'implementation_ids':sorted(implementations),'geomean':a['successful_subset_geomean_change_pct']}
# HLS baseline manifests and terminal logs; do not inspect waveforms or restart.
for folder in ['full_color_trial_volatile_address_stage_2026-10-04','full_color_optimized_four_rtl_2026-10-04']:
 base=ROOT/'projects/tileplace/work'/folder
 m=read(str(base/'manifest.json'))
 for name,sha in m['files'].items():check(name,sha,base)
 t=read(str(base/'rtl_attempt_01_terminal_audit.json'));check(t['log'],t['log_sha256'])
 summary[folder]={k:t.get(k) for k in ['returncode','completed_transactions','output_comparisons','full_expected_outputs_equal','terminal_cosim_pass','functional_gate_pass']}
for f in ['final_audit.json','input_identity_final_audit.json']:
 d=read('projects/tileplace/work/optimized_native_cohort_2026-10-04/'+f);refs(d)
 summary['tileplace_native_'+f]={k:d.get(k) for k in ['status','verified_native_trials','checked_color_calls','unique_frozen_inputs_verified']}
f='projects/tileplace/work/best_dimension_guard_postroute_refine_2026-10-13/primary_independent_audit.json';d=read(f)
for name,sha in d['output_hashes'].items():check(name,sha,ROOT/Path(f).parent)
summary['tileplace_4ns']={k:d[k] for k in ['wns_ns','tns_ns','setup_failing_endpoints','period_ns','internal_timing_route_drc_pass']}
# PR current source identities vs final routed build; xclbin kept local.
d=read('projects/persistroute/experiments/u280_treeseed_hw_2026-08-29.json')
for key,f in [('search_hbm_cpp_sha256','src/search_hbm.cpp'),('accelerated_pathfinder_cpp_sha256','src/accelerated_pathfinder.cpp'),('xrt_host_cpp_sha256','host/accelerated_xrt_host.cpp'),('connectivity_cfg_sha256','connectivity.cfg')]:check('projects/persistroute/'+f,d['source_hashes'][key])
check(d['xclbin']['path'],d['xclbin']['sha256'],ROOT/'projects/persistroute')
summary['persistroute_hw_emu_rerun']=d['hw_emu_rerun']
pr=read('projects/persistroute/experiments/balanced_pathreads_extended_matrix_2026-08-29.json')['cases']
spmv=read('projects/persistroute/experiments/tree_timing_weight128_spmv_full_2026-08-29.json')['cases'][0]
pr=[c for c in pr if c['name']!='spmv']+[spmv]
summary['persistroute_native']=[]
for c in pr:
 run=resolve(c['stages']['hbm_cmodel']['command'][-1]).parent
 validation=run.parent/'native_validation/validation.json'
 v=read(str(validation),c['output_hashes']['validation.json'])
 summary['persistroute_native'].append({'case':c['name'],'legal':v['legal'],'vpr_exit_status':v['vpr_exit_status'],'wirelength':v['total_wirelength'],'cpd_ns':v['critical_path_delay_ns'],'wl_delta_percent':v['wirelength_delta_percent'],'cpd_delta_percent':v['cpd_delta_percent'],'route_tree_timing_weight_q':c['configuration'].get('route_tree_timing_weight_q',0)})
# Independent FP summaries point at original study/audit receipts.
for f in ['independent_validation_status_2026-10-13.json','tp_budget_reference_status_2026-10-13.json','tree_reuse_status_2026-10-13.json','controller_baselines_status_2026-10-13.json','rr_export_cache_status_2026-10-13.json']:
 d=read('projects/fusionpar/experiments/'+f);refs(d)
# RC ABBA binding; no graph traversal.
base=ROOT/'projects/routecast/experiments/mux_NET_shared_ABBA_2026-10-06';d=read(str(base/'verification.json'));check('receipt.json',d['receipt_sha256'],base);check('protocol.json',d['protocol_sha256'],base)
summary['routecast_abba']={k:d[k] for k in ['all_four_runs_exact_policy_parity','means_s','scope']}
d=read('projects/routecast/experiments/joint_capacity_direction_review_v2_2026-10-21/review.json')
for f,sha in d['bindings'].items():check(f,sha)
summary['routecast_joint_capacity']={'status':d['status'],'accepted_candidate':d['accepted_candidate_in_reviewed_lineage'],'deadline':d['original_window']['hard_deadline_utc']}
read('projects/routecast/experiments/mmc_multiplacement_quality_v1_2026-10-18/cohort_research_decision_v1.json')
# Latest DR authority and process identity: read-only /proc, never signal.
p=read('projects/dieroute/experiments/research_plan.json')['current_claim_matrix'];d=read(p['path'],p['sha256'],ROOT/'projects/dieroute')
summary['dieroute']={'claims':len(d['claims']),'research_complete':d['research_complete'],'gates':[{k:g[k] for k in ['id','status','requirement']} for g in d['gates']],'boot_id':Path('/proc/sys/kernel/random/boot_id').read_text().strip(),'processes':[]}
for pid,expected in [(3710767,1829055404),(3710818,1829055409),(3710835,1829055411),(3710854,1829055419),(3710864,1829055882)]:
 f=Path(f'/proc/{pid}/stat');row={'pid':pid,'expected_start_ticks':expected,'present':f.exists()}
 if f.exists():
  v=f.read_text().split(') ',1)[1].split();row.update(state=v[0],start_ticks=int(v[19]))
 summary['dieroute']['processes'].append(row)
summary['dieroute']['builder_terminal_present']=(ROOT/'projects/dieroute/work/dictionary_builder_full_capture_v3_20261107/run_builder.terminal.json').exists()
from collections import Counter
summary['integrity_counts']=dict(Counter(x['status'] for x in checks))
summary['unique_hashed_files']=len(cache)
(OUT/'PHASE1_CHECKS.json').write_text(json.dumps({'summary':summary,'checks':checks},ensure_ascii=False,indent=2)+'\n')
with (OUT/'PHASE1_CASES.csv').open('w') as f:
 w=csv.DictWriter(f,fieldnames=list(case_rows[0]));w.writeheader();w.writerows(case_rows)
print(json.dumps(summary,ensure_ascii=False,indent=2))
print('ANOMALIES',json.dumps([x for x in checks if x['status'] in ['MISSING','MISMATCH']],ensure_ascii=False)[:6000])
