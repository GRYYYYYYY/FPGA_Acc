"""Continue exact audits, then original three-control quality and independent checks."""
import concurrent.futures,json,sys,subprocess,time,traceback,os
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
root=R/'experiments/mmc_multi_NET_atomic_pair_v1_2026-10-18';audit=root/'independent_audits'
def save(status,**extra):(root/'pipeline_supervision.json').write_text(json.dumps(dict(status=status,**extra),indent=2)+'\n')
def wait_exact(identity):
 while True:
  p=Path('/proc',str(identity['pid']),'stat')
  if not p.exists():return
  try:s=p.read_text().split(') ',1)[1].split()
  except FileNotFoundError:return
  if s[19]!=identity['startticks'] or s[0]=='Z':return
  time.sleep(2)
def run(command,log):
 with log.open('x') as f:code=subprocess.call(command,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 assert code==0,(command,code)
def main():
 ids=json.loads((audit/'live_audit_processes_v1.json').read_text());stat=Path('/proc/self/stat').read_text().split(') ',1)[1].split();(root/'pipeline_live_process.json').write_text(json.dumps(dict(pid=os.getpid(),startticks=stat[19]))+'\n');save('waiting_exact_first_group_event_audit',identities=ids)
 if 'first_events'in ids:wait_exact(ids['first_events'])
 first=audit/'case_01_events_v2.json';v=json.loads(first.read_text());assert v['all_group_event_replays_pass'];save('first_group_audit_pass_remaining_two_group_audits_running')
 def event(case):return run([sys.executable,str(R/'tools/verify_mmc_atomic_pair_events_v2_2026_10_18.py'),str(root/case),str(audit/f'{case}_events_v2.json')],audit/f'{case}_events_v2.log')
 with concurrent.futures.ThreadPoolExecutor(max_workers=2) as pool:
  fs=[pool.submit(event,c) for c in ['case_02','case_03']]
  for f in concurrent.futures.as_completed(fs):f.result()
 for name in ['case02_frame','case03_frame']:
  if name in ids:wait_exact(ids[name])
 bindings=closure([Path(__file__)]);rows=[]
 for case in ['case_01','case_02','case_03']:
  paths=dict(frame=audit/f'{case}_frame.json',events=audit/f'{case}_events_v2.json')
  for kind,p in paths.items():
   v=json.loads(p.read_text());flag='all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass' if kind=='frame' else 'all_group_event_replays_pass';assert v[flag] and all(sha(k)==h for k,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
  rows.append(dict(case=case,**{k:str(p) for k,p in paths.items()}))
 ap=audit/'group_verification_v1.json';ap.write_text(json.dumps(dict(all3_frames_and_complete_group_events_pass=True,bindings=bindings,cases=rows),indent=2)+'\n');save('all3_frames_and_complete_group_audits_pass_original_three_control_quality_running')
 out=R/'experiments/mmc_atomic_pair_quality_v1_2026-10-18';out.mkdir();quality=[];bindings={**closure([Path(__file__)]),str(ap):sha(ap)}
 for case in ['case_01','case_02','case_03']:
  old=R/f'experiments/mmc_multiplacement_quality_v1_2026-10-18/{case}/protocol.json';p=json.loads(old.read_text());p['bindings'].update(closure([Path(__file__)]));p['bindings'][str(old)]=sha(old);p['atomic_group_audit']=str(ap);p['predictions']['atomic_coowner_pair_v1']=str(root/case/'sketch.json');p['primary_candidate']='atomic_coowner_pair_v1';p['primary_controls']=['raw_min_on','previous_native','native_retained_on'];p['control_name_mapping']={'original_single_NET_native_retained_on':'native_retained_on'};p['evidence_scope']='Prospectively frozen combined coowner-pair scheduling and group transaction candidate, all original budgets and cold domains/ties/K retained. Three required controls, no posthoc control or case selection. Not isolated attribution to atomicity, native equivalent search, strict unseen family or fullflow gain.';folder=out/case;folder.mkdir();(folder/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
  for script in ['evaluate_atomic_pair_quality_case_v1_2026_10_18.py','verify_atomic_pair_quality_case_v1_2026_10_18.py']:run([sys.executable,str(R/'tools'/script),str(folder)],folder/f'{script}.log')
  c=json.loads((folder/'comparison.json').read_text());v=json.loads((folder/'verification.json').read_text());assert v['status']=='pass' and v['histogram_rank_topk_mae_checks']==12 and v['primary_gate_pass']==c['primary_gate_pass'];quality.append(dict(case=case,primary_gate_pass=c['primary_gate_pass'],primary_checks=c['primary_checks']));bindings[str(folder/'verification.json')]=sha(folder/'verification.json');print('ATOMIC_PAIR_ORIGINAL_QUALITY',case,c['primary_gate_pass'],flush=True)
 decision=dict(status='registered_atomic_pair_original_three_control_gate_pass' if all(x['primary_gate_pass'] for x in quality) else 'registered_atomic_pair_original_three_control_gate_failed',bindings=bindings,cases=quality,primary='atomic_coowner_pair_v1',required_controls=['raw_min_on','previous_native','native_retained_on'],native_utility_executed=False,accepted_complete_workflow_gain=False);(root/'research_decision_v1.json').write_text(json.dumps(decision,indent=2)+'\n');save('all_models_audits_and_original_three_control_quality_complete',decision=decision['status'])
if __name__=='__main__':
 try:main()
 except Exception:save('pipeline_failed',error=traceback.format_exc());raise
