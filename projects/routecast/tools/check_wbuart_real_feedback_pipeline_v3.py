"""Resume terminal first producer; audit all four fixed arms without rerunning it."""
import hashlib,json,subprocess,sys
from pathlib import Path
from run_wbuart_fixed_nominal_feedback_v1 import predict
R=Path(__file__).resolve().parents[1];E=R/'experiments';O=E/'wbuart_real_feedback_pipeline_v3_2026-10-20'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def main():
 O.mkdir(exist_ok=False);case='w096/episode_01';ep=E/'wbuart_width_frames_v2_2026-10-20'/case/'routing_endpoints.json';node=E/'wbuart_node_bases_v1_2026-10-20/w096/verification.json';timing=E/'wbuart_frame_timings_v1_2026-10-20'/case;warm=E/'wbuart_warm_inputs_v1_2026-10-20'/case;producer=R/'tools/run_wbuart_fixed_nominal_feedback_v1.py';auditor=R/'tools/verify_wbuart_fixed_nominal_feedback_events_v1.py';first=E/'wbuart_real_feedback_pipeline_v2_2026-10-20/raw_min/warm_timing_frozen';firstproof=first/'complete_event_audit.json';a=json.loads(firstproof.read_text());assert a['complete_round_timing_original_XML_recurrence_component_assembly_and_setup_pass']
 for n,h in a['bindings'].items():assert sha(Path(n))==h
 bindings={str(p):sha(p) for p in [Path(__file__),producer,auditor,ep,node,timing/'verification.json',firstproof]};jobs=[]
 for init in ['raw_min','native_retained']:
  for policy in ['warm_timing_frozen','warm_timing_round_updated']:
   reuse=init=='raw_min' and policy=='warm_timing_frozen';jobs.append({'initializer':init,'policy':policy,'output':str(first if reuse else O/init/policy),'reuse_verified_terminal_first_producer':reuse})
 (O/'protocol.json').write_text(json.dumps({'case':case,'jobs':jobs,'bindings':bindings,'algorithm_parameters_unchanged':True,'scope':'All4 two-round all-NET predictor arms and complete event/timing audit. Reuse first terminal producer and its complete audit; first source elapsed cost remains paid. No target labels or performance-based selection, not complete9-case utility/paid protocol. Earlier wrapper argument/dir failures preserved; auditor receives out,name,proof path.'},indent=2)+'\n');rows=[]
 for job in jobs:
  init,policy=job['initializer'],job['policy'];d=Path(job['output'])
  if not job['reuse_verified_terminal_first_producer']:
   d.parent.mkdir(parents=True,exist_ok=True);predict(ep,d,node,timing,warm/init,'all',timing_policy=policy)
   with (O/(init+'_'+policy+'_audit.log')).open('x') as f:rc=subprocess.call([sys.executable,str(auditor),str(d),init+'_'+policy,str(d/'complete_event_audit.json')],cwd=R,stdout=f,stderr=subprocess.STDOUT)
   if rc:
    (O/'failure.json').write_text(json.dumps({'arm':job,'audit_exit_status':rc,'retain_no_parameter_change':True},indent=2)+'\n');raise RuntimeError('complete audit failed')
  proof=d/'complete_event_audit.json';assert json.loads(proof.read_text())['complete_round_timing_original_XML_recurrence_component_assembly_and_setup_pass'];rows.append(dict(job,audit=str(proof),audit_sha256=sha(proof)));print('WBUART_PIPELINE_ARM_PASS',init,policy,'reused',job['reuse_verified_terminal_first_producer'],flush=True)
 parity=[]
 for init in ['raw_min','native_retained']:
  arms=[Path(r['output']) for r in rows if r['initializer']==init];a,b=arms;ra,rb=[json.loads((d/'receipt.json').read_text()) for d in arms];assert ra['rounds'][0]['events']==rb['rounds'][0]['events'];assert json.loads((a/'round0.json').read_text())==json.loads((b/'round0.json').read_text());assert json.loads((a/'timing_round0.json').read_text())['criticalities']==json.loads((b/'timing_round0.json').read_text())['criticalities'];parity.append({'initializer':init,'round0_events_state_and_criticalities_equal':True})
 for n,h in bindings.items():assert sha(Path(n))==h
 (O/'verification.json').write_text(json.dumps({'status':'ALL4_REAL_FEEDBACK_ARMS_COMPLETE_AUDIT_AND_ROUND0_POLICY_PARITY_PASS','rows':rows,'parity':parity,'new_target_route_labels':False,'strict_unseen_admitted':False,'bindings':{**bindings,**{r['audit']:r['audit_sha256'] for r in rows}}},indent=2)+'\n')
if __name__=='__main__':main()
