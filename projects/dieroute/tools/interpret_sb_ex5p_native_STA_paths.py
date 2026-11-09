"""Record descriptive timing localization without a rerouting counterfactual."""
import hashlib,json
from pathlib import Path
R=Path(__file__).resolve().parents[1];P=R/'work/sb_ex5p_native_STA_path_alignment_20261015'
def main():
 f=P/'independent_audit.json';x=json.loads(f.read_text());assert x['status']=='three_ex5p_native_STA_reports_reproduced_and63endpoints_aligned'
 assert x['worst_paths']['baseline']['endpoint']=='out:o_41_.outpad[0]'
 rows=[]
 for v in x['comparisons']:
  assert v['candidate_critical_endpoint']['endpoint']=='out:o_56_.outpad[0]';critical=v['candidate_critical_endpoint'];arc=next(a for a in critical['common_arcs'] if a['source']=='[3355].out[0] (.names)' and a['target']=='[3663].in[1] (.names)')
  rows.append(dict(candidate=v['candidate'],higher_printed_arrival_endpoints=v['higher_printed_arrival_endpoints'],lower_printed_arrival_endpoints=v['lower_printed_arrival_endpoints'],selected_critical_endpoint=critical['endpoint'],baseline_arrival_at_this_endpoint_ns=critical['baseline_printed_arrival_ns'],candidate_arrival_at_this_endpoint_ns=critical['candidate_printed_arrival_ns'],startpoint_changed=critical['startpoint_changed'],identified_common_printed_arc=arc))
 assert [v['higher_printed_arrival_endpoints'] for v in rows]==[50,59]
 report=dict(status='ex5p_CPDrise_has_changed_selected_critical_path_and_widespread_endpoint_arrival_increases',worst_paths=x['worst_paths'],observations=rows,source_sha256={str(q):hashlib.sha256(q.read_bytes()).hexdigest() for q in [f,Path(__file__).resolve()]},next_action='Resolve the shared printed source/target arc to the corresponding native net/connection and inspect original RR paths before changing routing policy. Do not claim restoring this arc alone repairs CPD, legality, WL or SLL.',scope='One fixed ex5p development case and three fixed routes, freshly identical native reanalysis. Printed resolution1ps; exact native CPD remains original. No single-net counterfactual, causal attribution, heldout tuning, new quality pass or physical timing claim.',adopted=False,board_result=False,research_complete=False)
 with (P/'interpretation.json').open('x') as out:json.dump(report,out,indent=2);out.write('\n')
 print(report['status'])
if __name__=='__main__':main()
