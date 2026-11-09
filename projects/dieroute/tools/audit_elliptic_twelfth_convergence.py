"""Explain routing convergence versus native baseline quality on frozen twelfth case."""
from pathlib import Path
import csv,hashlib,json
from decimal import Decimal
R=Path(__file__).resolve().parents[1]
def main():
 root=R/'work/width_coverage_parents_20261018';case='elliptic_28x22_cw320_seed1';parent=root/'parents'/case
 files=[parent/'route.iterations.csv',parent/'route.timing_iterations.csv',root/'recipes'/case/'pair.json',parent/'native_validation/validation.json',R/'work/width_coverage_roundtrip_20261017'/case/'native_validation/validation.json',R/'work/rr_remaining_layer_tail_variant_20261015/source/dieroute/src/wide_controller.cpp',R/'work/elliptic_twelfth_critical_path_diagnosis_20261020/audit.json',Path(__file__).resolve()]
 def rows(p):
  with p.open() as f:return list(csv.DictReader(f))
 routing=rows(files[0]);timing=rows(files[1]);recipe=json.loads(files[2].read_text());q=json.loads(files[3].read_text());base=json.loads(files[4].read_text());source=files[5].read_text()
 stop='if(all&&over==0&&!force_timing_reroute&&!supplemental)'
 assert stop in source and 'result.route_success=true;break;' in source
 assert routing[-1]['iteration']=='7' and routing[-1]['failed_connections']=='0' and routing[-1]['overused_resources']=='0'
 assert timing[-1]['critical_path_delay_ps']=='10425'
 env=recipe['steps'][0]['routing_environment'];assert env['DIEROUTE_MIN_TIMING_ITERATIONS']=='3' and env['DIEROUTE_CRITICAL_FEEDBACK_THRESHOLD_Q']=='0'
 assert q['legal'] and base['legal'];delta=(Decimal(str(q['critical_path_delay_ns']))-Decimal(str(base['critical_path_delay_ns'])))*1000;assert delta==Decimal('4.0000')
 result={'status':'frozen_congestion_convergence_does_not_enforce_baseline_native_CPD','final_routing_iteration':routing[-1],'timing_iterations':timing,'native_baseline_cpd_ns':base['critical_path_delay_ns'],'native_candidate_cpd_ns':q['critical_path_delay_ns'],'native_delta_ps':str(delta),'minimum_forced_timing_iterations':3,'threshold_feedback_enabled':False,'controller_success_condition':stop,'interpretation':'The frozen router reports success when all connections are routed, occupancy is legal, minimum timing iterations are complete and no supplemental reroute is pending. This stop condition does not compare native CPD with the frozen baseline. Native quality audit correctly rejects the resulting4ps regression; this is a missing quality guarantee in convergence, not evidence of failed native legality.','next_experiment_requirements':['Separate private protocol and source; preserve original12case outcome.','Keep complete routed trees with occupancy/sharing consistency; measure exact native CPD before publishing a candidate.','Require baseline CPD, wirelength and modeled transitions jointly; retain explicit quality failure if no admissible improvement exists.','Charge extra native STA/search time; validate across cases without claiming heldout generalization.'],'source_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest() for p in files},'adopted':False,'research_complete':False}
 out=R/'work/elliptic_twelfth_convergence_diagnosis_20261020';out.mkdir()
 with (out/'audit.json').open('x') as f:json.dump(result,f,indent=2);f.write('\n')
 print(json.dumps({k:result[k] for k in ['status','native_delta_ps','final_routing_iteration']}))
if __name__=='__main__':main()
