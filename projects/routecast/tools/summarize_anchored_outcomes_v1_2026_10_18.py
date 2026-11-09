"""Complete-key postcheck and paired development result interpretation."""
import hashlib,json,itertools
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 out=Path('experiments/mmc_anchored_outcomes_verification_v1_2026-10-18');vp=out/'verification.json';v=json.loads(vp.read_text());assert v['status']=='pass'
 for p,h in v['bindings'].items():assert sha(p)==h
 planpath=Path('experiments/mmc_anchored_NET_forecasts_verification_v1_2026-10-18/frozen_outcome_protocol_v1.json');plan=json.loads(planpath.read_text());pressure=plan['pressure'];root=Path('experiments/mmc_anchored_pressure_matrix_v1_2026-10-18');coldpath=Path('experiments/mmc_anchored_cold_quality_v1_2026-10-18/results.json');cold=json.loads(coldpath.read_text());allrows=[]
 for case in plan['cases']:
  rows=json.loads((root/(case+'.json')).read_text())['rows'];assert len(rows)==1008 and all(r['case']==case for r in rows);assert len({(r['method'],r['policy'],r['target'],r['domain']) for r in rows})==len(rows);allrows+=rows
 assert {(r['case'],r['source'],r['domain']) for r in cold['rows']}==set(itertools.product(plan['cases'],plan['sources'],plan['cold']['domains'])) and len(cold['rows'])==36
 for r in cold['rows']:assert r['method']=='anchored_group_mean__'+r['source']
 assert [c['case'] for c in cold['cases']]==plan['cases']
 for c in cold['cases']:
  assert [r['control'] for r in c['primary_checks']]==['previous_native','raw_min_on','native_retained_on']
  for r in c['primary_checks']:assert r['original_primary_control']==(r['control'] in ['previous_native','raw_min_on'])
 index={(r['case'],r['policy'],r['target'],r['domain'],r['method']):r for r in allrows}
 def changes(a,b):
  result={k:0 for k in ['up','down','equal','undefined']}
  for x,y in zip(a,b):
   if x is None or y is None:result['undefined']+=1
   elif x>y+1e-12:result['up']+=1
   elif x<y-1e-12:result['down']+=1
   else:result['equal']+=1
  return result
 comparisons={}
 specs=[('anchored_NET_collision','typed_NET_collision'),('anchored_NET_collision','observed_overflow'),('anchored_NET_collision','raw_density'),('anchored_NET_collision','pooled_density'),('anchored_group_mean','typed_group_mean')]
 for family,control in specs:
  comparison={}
  for domain in pressure['domains']:
   summary={}
   for target in pressure['targets']:
    pairs=[]
    for case,policy,source in itertools.product(plan['cases'],pressure['policies'],plan['sources']):
     baseline=source if control=='raw_density' else 'pooled_'+source if control=='pooled_density' else control+'__'+source
     pairs.append((index[case,policy,target,domain,family+'__'+source]['metrics'],index[case,policy,target,domain,baseline]['metrics']))
    summary[target]={key:changes([a[key] for a,b in pairs],[b[key] for a,b in pairs]) for key in ['spearman','precision_at_k']}
   comparison[domain]=summary
  comparisons[family+'_vs_'+control]=comparison
 primary=[]
 for case,policy,target,domain in itertools.product(plan['cases'],pressure['policies'],pressure['targets'],pressure['domains']):
  a=index[case,policy,target,domain,pressure['primary']]['metrics'];b=index[case,policy,target,domain,'typed_NET_collision__native_retained_on']['metrics'];primary.append(dict(case=case,policy=policy,target=target,domain=domain,anchored=dict(spearman=a['spearman'],precision_at_k=a['precision_at_k']),uniform=dict(spearman=b['spearman'],precision_at_k=b['precision_at_k'])))
 coldprimary=[r for r in cold['rows'] if r['method']==plan['cold']['primary']]
 receipt=dict(status='all3024_pressure_and36cold_rows_verified_no_main_promotion',bindings={str(p.resolve()):sha(p) for p in [vp,planpath,coldpath,Path(__file__)]},complete_metadata_and_control_flags_postchecked=True,new_pressure_cells=864,prior_pressure_cells_transferred=2160,cold_rows=36,cold_primary=[dict(case=c['case'],pass_gate=c['original_primary_gate_pass']) for c in cold['cases']],cold_primary_metrics=coldprimary,all_source_comparisons=comparisons,fixed_primary_pressure_comparisons=primary,decision='All original cold gates remain evaluated as specified. No fitted-weight/source selection, no calibrated pressure or unseen/native/full-flow promotion. Pressure tradeoffs are development diagnostics.',next_action='Use full reported pressure and cold comparisons to diagnose whether member-specific anchoring addresses hotspot precision without erasing rank gains. Because all fixed-k within-group transformations conserve spatial mean mass, they cannot correct spatial occupancy regressions. Further main forecasting work must model inter-group path redistribution or validate a directly useful pressure-driven decision under new frozen controls; do not keep tuning this mixture weight on exposed labels.')
 with (out/'research_decision_v1.json').open('x') as f:json.dump(receipt,f,indent=2)
 print(json.dumps(dict(cold_gates=receipt['cold_primary'],primary_cold=[dict(case=r['case'],domain=r['domain'],spearman=r['metrics']['spearman'],precision_at_k=r['metrics']['precision_at_k']) for r in coldprimary],mean_pressure_collision_vs_uniform={d:comparisons['anchored_NET_collision_vs_typed_NET_collision'][d]['mean_overflow'] for d in pressure['domains']})))
if __name__=='__main__':main()
