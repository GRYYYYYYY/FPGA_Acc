"""One fixed prospective full model/audit fixture, before any target labels."""
import hashlib,json,subprocess,sys
from pathlib import Path
R=Path(__file__).resolve().parents[1];E=R/'experiments';O=E/'wbuart_real_feedback_pipeline_v1_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);case='w096/episode_01';ep=E/'wbuart_width_frames_v2_2026-10-20'/case/'routing_endpoints.json';node=E/'wbuart_node_bases_v1_2026-10-20/w096/verification.json';timing=E/'wbuart_frame_timings_v1_2026-10-20'/case;warm=E/'wbuart_warm_inputs_v1_2026-10-20'/case;producer=R/'tools/run_wbuart_fixed_nominal_feedback_v1.py';auditor=R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py';bindings={str(p):sha(p) for p in [Path(__file__),producer,auditor,ep,node,timing/'verification.json',E/'wbuart_feedback_factory_contract_v1_2026-10-20/verification.json']};policies=['warm_timing_frozen','warm_timing_round_updated'];(O/'protocol.json').write_text(json.dumps({'case':case,'initializers':['raw_min','native_retained'],'timing_policies':policies,'bindings':bindings,'parameters':'Existing all-NET two-round source-historyOFF model; native-anchored budgets, labels10000, prices/guards/objective unchanged. Same current initial state for both timing arms.','acceptance':'All four producer and complete per-event XML/Fraction/owner exclusion/budget/epoch/objective and round timing audits; within each initializer round0 events/state/criticality values exactly equal between timing arms.','scope':'Pipeline qualification only; no target native labels, metric fitting or promotion based on this single case. Not a full executable nine-case utility/paid-time protocol.'},indent=2)+'\n')
 from run_wbuart_fixed_nominal_feedback_v1 import predict
 rows=[]
 for init in ['raw_min','native_retained']:
  for policy in policies:
   d=O/init/policy;d.mkdir(parents=True)
   predict(ep,d,node,timing,warm/init,'all',timing_policy=policy)
   with (O/(init+'_'+policy+'_audit.log')).open('x') as f:rc=subprocess.call([sys.executable,str(auditor),str(d)],cwd=R,stdout=f,stderr=subprocess.STDOUT)
   if rc:
    (O/'failure.json').write_text(json.dumps({'initializer':init,'policy':policy,'audit_exit_status':rc,'retained_no_parameter_change':True},indent=2)+'\n');raise RuntimeError('Complete audit failed; retained')
   rows.append({'initializer':init,'timing_policy':policy,'output':str(d),'audit_exit_status':rc});print('WBUART_REAL_FEEDBACK_ARM_PASS',init,policy,flush=True)
 parity=[]
 for init in ['raw_min','native_retained']:
  a,b=[O/init/p for p in policies];ra,rb=[json.loads((p/'receipt.json').read_text()) for p in [a,b]];assert ra['rounds'][0]['events']==rb['rounds'][0]['events'];assert json.loads((a/'round0.json').read_text())==json.loads((b/'round0.json').read_text());assert json.loads((a/'timing_round0.json').read_text())['criticalities']==json.loads((b/'timing_round0.json').read_text())['criticalities'];parity.append({'initializer':init,'round0_events_state_and_criticalities_equal':True})
 for n,h in bindings.items():assert sha(Path(n))==h
 (O/'verification.json').write_text(json.dumps({'status':'ALL4_REAL_FEEDBACK_ARMS_COMPLETE_AUDIT_AND_ROUND0_POLICY_PARITY_PASS','rows':rows,'parity':parity,'new_target_route_labels':False,'strict_unseen_admitted':False,'bindings':{**bindings,**{str(Path(r['output'])/'complete_event_audit.json'):sha(Path(r['output'])/'complete_event_audit.json') for r in rows}}},indent=2)+'\n')
if __name__=='__main__':main()
