"""Wait on the single audit owner, then execute fixed four-control quality gates."""
import pathlib,json,sys,subprocess,time,os
R=pathlib.Path(__file__).resolve().parents[1]
sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure

def main():
 E=R/'experiments';source=E/'mmc_soft_budget_all_NET_v1_2026-10-18';audit=source/'independent_audits/verification.json';live=json.loads((source/'independent_audits/live_process.json').read_text());out=E/'mmc_soft_budget_quality_v1_2026-10-18';out.mkdir();s=pathlib.Path('/proc/self/stat').read_text().split(') ',1)[1].split();(out/'live_process.json').write_text(json.dumps({'pid':os.getpid(),'startticks':s[19]})+'\n');registered=E/'mmc_soft_budget_all_NET_protocol_v1_2026-10-18/protocol.json';spec=json.loads(registered.read_text());assert spec['controls']==['raw_min_on','previous_native','native_retained_on','all_NET_on_original_budget'];bindings={**closure([pathlib.Path(__file__)]),str(registered):sha(registered)}
 while not audit.exists():
  try:st=pathlib.Path(f'/proc/{live["pid"]}/stat').read_text().split(') ',1)[1].split();running=st[19]==live['startticks'] and st[0]!='Z'
  except FileNotFoundError:running=False
  if not running and not audit.exists():raise RuntimeError('Audit owner stopped without terminal verification; no retry')
  time.sleep(15)
 v=json.loads(audit.read_text());assert v['all3_soft_policy_frames_and_all331800_events_pass'];assert all(sha(k)==h for k,h in v['bindings'].items());bindings[str(audit)]=sha(audit);rows=[]
 for case in spec['cases']:
  old=E/f'mmc_all_NET_feedback_quality_v1_2026-10-18/{case}/protocol.json';p=json.loads(old.read_text());p['bindings'].update(bindings);p['bindings'][str(old)]=sha(old);p['frozen_cohort_protocol']=str(registered);p['frozen_cohort_protocol_sha256']=sha(registered);p['soft_budget_audit']=str(audit);p['original_all_NET_audit']=str(E/'mmc_all_NET_feedback_v1_2026-10-18/independent_audits/verification.json');p['predictions']['all_NET_on_original_budget']=p['predictions'].pop('all_NET_on');p['predictions']['soft_budget_all_NET_on']=str(source/case/'sketch.json');p['primary_candidate']='soft_budget_all_NET_on';p['primary_controls']=spec['controls'];p['evidence_scope']='Exposed all3 development layouts, fixed2rounds allNET soft-criticality cap ablation. Four original registered controls, full positive-channel/spatial domains and original K/ties; no original budget/timing gate, unseen admission, native utility or end-to-end gain.';folder=out/case;folder.mkdir();(folder/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
  for script in ['evaluate_soft_budget_feedback_quality_case_v1_2026_10_18.py','verify_all_NET_feedback_quality_case_v1_2026_10_18.py']:
   with (folder/(script+'.log')).open('x') as log:code=subprocess.call([sys.executable,str(R/'tools'/script),str(folder)],cwd=R,stdout=log,stderr=subprocess.STDOUT)
   print('SOFT_QUALITY_STAGE',case,script,code,flush=True)
   if code!=0:raise RuntimeError((case,script,code))
  r=json.loads((folder/'comparison.json').read_text());check=json.loads((folder/'verification.json').read_text());assert check['status']=='pass' and check['histogram_rank_topk_mae_checks']==16 and check['truth_tie_interval_checks']==16;assert check['primary_gate_pass']==r['primary_gate_pass'];bindings[str(folder/'comparison.json')]=sha(folder/'comparison.json');bindings[str(folder/'verification.json')]=sha(folder/'verification.json');rows.append({'case':case,'primary_gate_pass':r['primary_gate_pass'],'primary_checks':r['primary_checks']})
  (out/'stages.json').write_text(json.dumps(rows,indent=2)+'\n')
 (out/'results.json').write_text(json.dumps({'status':'all3_fixed_four_control_quality_evaluations_independently_verified','bindings':bindings,'cases':rows,'all3_primary_gate_pass':all(r['primary_gate_pass'] for r in rows),'accepted_gain':False,'original_budget_gate_claimed':False},indent=2)+'\n');print('SOFT_QUALITY_TERMINAL',all(r['primary_gate_pass'] for r in rows),flush=True)
if __name__=='__main__':main()
