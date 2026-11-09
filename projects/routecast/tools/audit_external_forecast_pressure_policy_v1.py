"""Bind original predictor policy and count actual two-round events before ablation."""
import json,sys,re
from pathlib import Path
from collections import Counter
from fractions import Fraction
sys.path.insert(0,str(Path(__file__).resolve().parent/'native_resume_prototype'))
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];E=R/'experiments';P=E/'prospective_external_family_supplementary_development_v1_2026-10-19';N=E/'prospective_external_family_early_net_observer_v1_2026-10-19';D=E/'prospective_external_family_forecast_pressure_policy_audit_v1_2026-10-19'
def read(p):return json.loads(Path(p).read_text())
def main():
 D.mkdir(exist_ok=False);bindings={str(Path(__file__).resolve()):sha(__file__)};rows=[]
 for i in (1,2,3):
  case=f'w160/episode_{i:02d}';folder=P/'predictions'/case/'native_retained_on';admission=read(folder/'complete_event_audit.json');assert admission['all_original_queries_xml_fraction_rc_budgets_singleparent_and_uniqueNET_and_independent_ledgers_pass'] and all(sha(p)==h for p,h in admission['bindings'].items());protocol=read(folder/'protocol.json');receipt=read(folder/'receipt.json');assert all(sha(p)==h for p,h in receipt['bindings'].items());spec=read(P/'specifications'/case/'comparison_spec.json');endpoint=read(spec['endpoint']);fanout=Counter(q['net_id'] for q in endpoint['connections']);order=sorted(fanout,key=lambda n:(-fanout[n],n));native=[int(net) for position,net in re.findall(r'^RC_FIRST_NET_ORDER (\d+) (\d+)$',(N/case/'native.log').read_text(),re.M) if int(net) in fanout];assert order==native;current={q['connection_id']:q for q in read(folder/'initial.json')['records']};status=Counter();fallback=Counter();changed_NETs=set();commits=0;actual_change_events=0;actual_changed_CIDs=0;guard_rejected_path_change_events=0;rounds=[]
  for rnd in receipt['rounds']:
   assert rnd['affected_nets']==sorted(fanout);assert [e['net_id'] for e in rnd['events']]==sorted(fanout);rs=Counter()
   for event in rnd['events']:
    status[event['status']]+=1;rs[event['status']]+=1
    if 'fallback' in event:fallback[event['fallback']['status']]+=1
    if event['status']=='COMMITTED':
     commits+=1;assert event['prospective_overflow_delta']<=0 and Fraction(event['objective_guard']['objective_delta'])<=0;changed=sum(q['answer']['physical_edge_ids']!=current[q['connection_id']]['answer']['physical_edge_ids'] for q in event['records']);actual_changed_CIDs+=changed;actual_change_events+=changed>0
     if changed:changed_NETs.add(event['net_id'])
     for q in event['records']:current[q['connection_id']]=q
    elif 'rejected_records' in event:
     guard_rejected_path_change_events+=any(q['answer']['physical_edge_ids']!=current[q['connection_id']]['answer']['physical_edge_ids'] for q in event['rejected_records'])
   rounds.append(dict(round_index=rnd['round_index'],status_counts=dict(rs),overflow_before=rnd['overflow_before'],overflow_after=rnd['overflow_after']))
  final=read(folder/'sketch.json');assert {q['connection_id']:q for q in final['records']}==current;base=read(protocol['structural_node_base_proof']);positive_by_type=Counter()
  for group in base['groups']:
   if group['integer_base']>0:positive_by_type[group['node_type']]+=group['nodes']
  row=dict(case=case,NETs=len(fanout),connections=len(endpoint['connections']),status_counts=dict(status),fallback_status_counts=dict(fallback),nominal_COMMITTED_events=commits,actual_path_change_events=actual_change_events,actual_path_change_CID_events=actual_changed_CIDs,unique_NETs_with_any_path_change=len(changed_NETs),guard_rejected_path_change_events=guard_rejected_path_change_events,rounds=rounds,native_filtered_order_matches_descending_fanout_then_NETid=True,original_vs_native_order_position_differences=sum(a!=b for a,b in zip(sorted(fanout),order)),original_NET85_position=sorted(fanout).index(85),fanout_NET85_position=order.index(85),original_NET2_position=sorted(fanout).index(2),fanout_NET2_position=order.index(2),positive_base_nodes_by_type=dict(positive_by_type));rows.append(row)
  for p in [folder/'complete_event_audit.json',folder/'receipt.json',folder/'protocol.json',Path(protocol['structural_node_base_proof']),N/case/'native.log']:bindings[str(p)]=sha(p)
  print(json.dumps(row),flush=True)
 assert all(sha(p)==h for p,h in bindings.items());(D/'verification.json').write_text(json.dumps(dict(status='ALL3_ORIGINAL_REGISTERED_PRESSURE_POLICY_AND_ACTUAL_EVENT_COUNTS_AUDITED',rows=rows,bindings=bindings,policy_findings=['Context prices every RR capacity node; positive IPIN/SOURCE/OPIN bases present, so CHANNEL scoring is not missing pin pressure.','First feedback history addition skipped, present factor1 for both rounds, zero historical native seed; native first pass present0, second .5. Initial states differ.','Original feedback numeric NETid order differs from runtime native fanout order; all3 exact native filtered invocation sequences match descending CID-fanout then NETid.','Budget fallbacks and perNET prospective overflow and common-objective nonincrease guards remain; changing native features is a new model, not equivalence.'],scope='Event accounting validated against previously independent complete physical/event audits. Native pressure intervention local evidence does not prove which original model policy improves prediction.'),indent=2)+'\n')
if __name__=='__main__':main()
