"""Authenticate archival predictor clock boundaries without splicing new native timings."""
import pathlib,json,hashlib,math
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(8*1024*1024),b''):h.update(b)
 return h.hexdigest()
def main():
 M=R/'experiments/mmc_full_NET_tree_ensemble_v1_2026-10-19';rp=M/'receipt.json';pp=M/'protocol.json';a=json.loads(rp.read_text());p=json.loads(pp.read_text());assert a['status']=='ALL3_COMPLETE_55300_NET_ENSEMBLE_PREDICTIONS_PRODUCED';assert p['cache_key']=='NET id, source, sorted distinct sinks; exact match only';bindings={str(x):sha(x) for x in [rp,pp,pathlib.Path(__file__).resolve()]};rows=[]
 for case in p['cases']:
  f=M/case/'receipt.json';assert sha(f)==a['bindings'][str(f)];x=json.loads(f.read_text());assert x==next(y for y in a['rows'] if y['case']==case);assert x['cache_hits']+x['new_endpoint_sets']==x['NETs']==55300 and x['connections']==115572;assert 0<=x['search_seconds']+x['expectation_seconds']<=x['component_seconds'];rows.append({k:x[k] for k in ['case','cache_hits','new_endpoint_sets','search_seconds','expectation_seconds','component_seconds']});bindings[str(f)]=sha(f)
 assert sum(x['new_endpoint_sets'] for x in rows)==a['unique_NET_endpoint_sets'];nested=a['graph_setup_seconds']+sum(x['component_seconds'] for x in rows);assert nested<=a['paid_component_seconds'];gap=a['paid_component_seconds']-nested
 source=R/'tools/run_MMC_full_NET_tree_ensemble_v1_2026_10_19.py';assert sha(source)==a['bindings'][str(source)];bindings[str(source)]=sha(source)
 O=R/'experiments/mmc_first_hint_forecast_cost_scope_v2_2026-10-19';O.mkdir(exist_ok=False);result=dict(status='ARCHIVED_FORECAST_COLD_AND_CACHE_CLOCKS_AUTHENTICATED_NO_FULLFLOW_GAIN_INFERRED',cases=rows,shared_graph_setup_seconds=a['graph_setup_seconds'],archival_whole_predictor_component_seconds=a['paid_component_seconds'],outer_minus_named_nested_components_seconds=gap,unique_NET_endpoint_sets=a['unique_NET_endpoint_sets'],bindings=bindings,clock_rules=['Search and expectation clocks are inside each case component clock; do not add them again.','Graph setup and case component clocks are inside whole predictor component clock; outer gap remains explicit.','Case02/03 cache reuse requires a resident compatible graph/model context and previously paid cache construction.','Historical predictor clocks and new native component clocks are different executions, not continuous paired on/off workflows.'],unmeasured_for_future_fullworkflow=['Fresh continuous on/off boundaries with equal initial-state/cache opportunities.','Risk export/conversion and native import/hint-expiry costs in the same execution.','Prescribed model/epoch/STA updates and shared-state maintenance.','Actual final routing and symmetric physical/canonical acceptance costs.'],scope='Cost-scope authentication only. No numerical end-to-end speedup, break-even bound, amortization horizon or performance rejection inferred by splicing historical and current times. Current fixed6 first-hint utility experiment and original quality/utility/heldout gates unchanged.')
 (O/'review.json').open('x').write(json.dumps(result,indent=2)+'\n');print(result['status'],rows,flush=True)
if __name__=='__main__':main()
