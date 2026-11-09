"""All12 combined graph/floor/current timing/static prices and real rejection cases."""
import json
from pathlib import Path
from pre_route_endpoints import sha
from load_external_design_routing_inputs_v2 import load
R=Path(__file__).resolve().parents[1]
def read(p):return json.loads(p.read_text())
def main():
 out=R/'experiments/prospective_external_family_all_frame_input_bundle_v2_2026-10-19';out.mkdir(exist_ok=False);matrix=R/'experiments/prospective_external_family_width_frame_inputs_v1_2026-10-19/verification.json';tp=R/'experiments/prospective_external_family_frame_timings_v1_2026-10-19/verification.json';bp=R/'experiments/prospective_external_family_width_node_bases_v2_2026-10-19/verification.json';fp=R/'experiments/prospective_external_family_frame_raw_floors_v2_2026-10-19/verification.json';origin=fp.with_name('independent_cache_origin_verification_v1.json');masters=[matrix,tp,bp,fp,origin]
 for p in masters:
  for f,h in read(p)['bindings'].items():assert sha(f)==h
 frames={r['case']:read(Path(r['frame_verification'])) for r in read(matrix)['rows']};timings={r['case']:r for r in read(tp)['rows']};prices={r['width']:r for r in read(bp)['rows']};floors={r['case']:r for r in read(fp)['rows']};assert set(frames)==set(timings)==set(floors) and len(frames)==12 and set(prices)=={96,128,160};rows=[];negative=[]
 def reject(label,ep,proof,td,n,scale,tag=None,graph_expected=False):
  try:load(ep,proof,td,n,scale,expected_timing_epoch=tag)
  except ValueError as err:
   if graph_expected:assert 'graph/price epoch mismatch' in str(err)
   negative.append(dict(contract=label,error=str(err)))
  else:raise AssertionError(label)
 for case,frame in frames.items():
  w=frame['width'];timing=timings[case];price=prices[w];ep=Path(frame['endpoint']);td=Path(timing['timing_directory']);proof=Path(price['verification']);tag=timing['timing_epoch_sha256'];values,c,bindings=load(ep,proof,td,frame['graph_nodes'],10**18,expected_timing_epoch=tag);assert len(values)==frame['graph_nodes'] and len(c)==15616;e=read(ep);q={a['connection_id']:a for a in e['connections']};floorproof=Path(floors[case]['verification']);fv=read(floorproof);assert fv['graph_sha256']==frame['graph_sha256'] and fv['connections']==15616 and all(sha(p)==h for p,h in fv['bindings'].items());records={a['connection_id']:a for a in map(json.loads,(floorproof.parent/'floors.jsonl').open())};assert set(records)==set(q)==set(c)
  for cid,a in records.items():
   assert all(a[k]==v for k,v in q[cid].items());assert (c[cid]['net'],c[cid]['source_rr'],c[cid]['target_rr'])==(q[cid]['net_id'],q[cid]['source'],q[cid]['sink']);assert a['minimum_integer'] is not None and a['minimum_integer']>=0
  reject(case+':wrong_node_count',ep,proof,td,frame['graph_nodes']-1,10**18,tag);reject(case+':wrong_scale',ep,proof,td,frame['graph_nodes'],10**15,tag);reject(case+':wrong_timing_epoch',ep,proof,td,frame['graph_nodes'],10**18,'0'*64)
  for other in [x for x in [96,128,160] if x!=w]:
   bad=prices[other];reject(case+f':wrong_graph_price_width{other}',ep,Path(bad['verification']),td,bad['nodes'],10**18,tag,graph_expected=True)
  if frame['frame']!='source':
   source=timings[f'w{w:03d}/source'];reject(case+':stale_source_timing',ep,proof,Path(source['timing_directory']),frame['graph_nodes'],10**18,source['timing_epoch_sha256'])
  files=[ep,proof,Path(timing['timing_verification']),floorproof];rows.append(dict(case=case,width=w,frame=frame['frame'],endpoint=str(ep),node_base_proof=str(proof),criticality_directory=str(td),timing_epoch_sha256=tag,floor_proof=str(floorproof),graph_sha256=frame['graph_sha256'],graph_nodes=len(values),connections=len(c),NETs=len({q['net_id'] for q in e['connections']}),raw_floor_scale=10**18,node_base_scale=10**18,budgets_assigned=False,bindings={str(p):sha(p) for p in files}));print('COMBINED_FRAME_INPUT_ADMITTED',case,len(values),len(c),flush=True)
 assert len(rows)==12 and len(negative)==69;old=R/'tools/run_external_native_timing_feedback_v1_2026_10_19.py';new=R/'tools/run_external_native_timing_feedback_v2_2026_10_19.py';assert new.read_text().replace('from load_external_design_routing_inputs_v2 import load as load_design_inputs','from load_external_design_routing_inputs_v1 import load as load_design_inputs')==old.read_text();paths=[*masters,R/'tools/load_external_design_routing_inputs_v2.py',R/'tools/load_external_current_initial_timing_v1.py',old,new,Path(__file__).resolve()]
 with (out/'verification.json').open('x') as f:json.dump(dict(schema='ROUTECAST_ALL_FRAME_PREDICTION_INPUTS_V2',status='ALL12_COMPLETE_GRAPH_FLOOR_CURRENT_TIMING_STATIC_PRICE_INPUTS_AND69_NEGATIVE_CONTRACTS_VERIFIED',rows=rows,negative_contracts=negative,connections_admitted=187392,predictor_algorithm_unchanged=True,predictor_execution_performed=False,bindings={str(p):sha(p) for p in paths},scope='Input adapter and proof integration only, unknown-history development cohort. All graph prices remain affine, all current timing layout-specific, no assigned budgets or native labels. Actual warm-state producers, controls, metric/K rules and complete time boundaries must be executable and frozen before routing trials.'),f,indent=2)
 print('ALL12_INPUT_BUNDLES_PASS',len(rows),len(negative),flush=True)
if __name__=='__main__':main()
