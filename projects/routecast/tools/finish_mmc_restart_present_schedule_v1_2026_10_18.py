"""Exact producer identity wait, all6 audits then original gates on all3 cases."""
import concurrent.futures,json,os,subprocess,sys,time,traceback
from pathlib import Path
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
E=R/'experiments';root=E/'mmc_restart_present_schedule_v1_2026-10-18'
def save(status,**kw):(root/'pipeline_supervision.json').write_text(json.dumps(dict(status=status,**kw),indent=2)+'\n')
def call(command,log):
 with log.open('x') as f:code=subprocess.call(command,cwd=R,stdout=f,stderr=subprocess.STDOUT)
 assert code==0,(command,code);return code
def main():
 live=json.loads((root/'live_process.json').read_text());pid=live['pid'];ticks=live['startticks'];save('waiting_exact_model_producer',**live)
 while not (root/'results.json').exists():
  p=Path(f'/proc/{pid}/stat');assert p.exists(),'producer missing without results';assert p.read_text().split(') ',1)[1].split()[19]==ticks,'producer identity changed';time.sleep(3)
 audit=root/'independent_audits';audit.mkdir();save('running_all6_independent_audits');commands=[]
 for case in ['case_01','case_02','case_03']:
  for kind in ['frame','events']:
   script='verify_native_endpoint_v2_feedback_frame_v1_2026_10_18.py' if kind=='frame' else 'verify_restart_present_feedback_events_v1_2026_10_18.py';output=audit/f'{case}_{kind}.json';command=[sys.executable,str(R/'tools'/script),str(root/case),'sketch',str(output)];commands.append((command,audit/f'{case}_{kind}.log'))
 with concurrent.futures.ThreadPoolExecutor(max_workers=3) as pool:
  fs=[pool.submit(call,*args) for args in commands]
  for f in concurrent.futures.as_completed(fs):f.result()
 bindings=closure([Path(__file__)])
 for p in audit.glob('*.json'):
  v=json.loads(p.read_text());assert all(sha(k)==h for k,h in v['bindings'].items());bindings.update(v['bindings']);bindings[str(p)]=sha(p)
 ap=audit/'verification.json';ap.write_text(json.dumps(dict(all3_frames_and_event_replays_pass=True,bindings=bindings),indent=2)+'\n');save('all6_audits_pass_running_original_quality')
 out=E/'mmc_restart_present_quality_v1_2026-10-18';out.mkdir();rows=[]
 for case in ['case_01','case_02','case_03']:
  old=E/f'mmc_multiplacement_quality_v1_2026-10-18/{case}/protocol.json';p=json.loads(old.read_text());p['bindings'].update(closure([Path(__file__)]));p['bindings'][str(old)]=sha(old);p['bindings'][str(ap)]=sha(ap);p['restart_schedule_audit']=str(ap);p['predictions']['restart_present_0_then_half']=str(root/case/'sketch.json');p['primary_candidate']='restart_present_0_then_half';p['evidence_scope']='Single prospectively registered present schedule intervention, exposed layouts, original labels and gates unchanged; no native utility or gain claim.';folder=out/case;folder.mkdir();(folder/'protocol.json').write_text(json.dumps(p,indent=2)+'\n')
  for script in ['evaluate_restart_present_quality_case_v1_2026_10_18.py','verify_restart_present_quality_case_v1_2026_10_18.py']:call([sys.executable,str(R/'tools'/script),str(folder)],folder/f'{script}.log')
  v=json.loads((folder/'verification.json').read_text());c=json.loads((folder/'comparison.json').read_text());assert v['status']=='pass' and v['histogram_rank_topk_mae_checks']==12 and v['primary_gate_pass']==c['primary_gate_pass'];rows.append(dict(case=case,primary_gate_pass=c['primary_gate_pass'],primary_checks=c['primary_checks']));print('RESTART_QUALITY_CASE_DONE',case,c['primary_gate_pass'],flush=True)
 decision=dict(status='registered_restart_schedule_original_gate_pass' if all(x['primary_gate_pass'] for x in rows) else 'registered_restart_schedule_original_gate_failed',cases=rows,primary='restart_present_0_then_half',native_utility_executed=False,accepted_complete_workflow_gain=False,bindings={str(ap):sha(ap),**{str(out/x['case']/'verification.json'):sha(out/x['case']/'verification.json') for x in rows}});(root/'research_decision_v1.json').write_text(json.dumps(decision,indent=2)+'\n');save('model_audits_and_original_quality_complete',decision=decision['status'])
if __name__=='__main__':
 try:main()
 except Exception:save('pipeline_failed',error=traceback.format_exc());raise
