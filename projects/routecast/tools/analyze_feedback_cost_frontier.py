"""Recompute phase budgets and QoR tradeoffs from authenticated completed cohorts."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha


def main():
 base=Path('experiments');bindings={};rows=[]
 for family,summary_name in [('adder_tree','native_pressure_four_case_summary_2026-10-06'),('multiplier','multiplier_native_pressure_six_case_summary_2026-10-06')]:
  summary=base/summary_name;sr=json.loads((summary/'receipt.json').read_text());assert sr['report_sha256']==sha(summary/'report.json');report=json.loads((summary/'report.json').read_text());assert all(sha(path)==digest for path,digest in report['input_sha256'].items());bindings[str(summary/'report.json')]=sha(summary/'report.json');bindings[str(summary/'receipt.json')]=sha(summary/'receipt.json')
  for case in report['cases']:
   design=case['design']
   if family=='multiplier':trial=base/'multiplier_native_pressure_paired_cached_cohort_2026-10-06'/design
   elif design=='adder_tree_2L_032bits':trial=base/'native_pressure_paired_cached_cost_2026-10-06'
   else:trial=base/'native_pressure_paired_cached_cohort_2026-10-06'/design
   r=json.loads((trial/'receipt.json').read_text());assert r['mean_cached_pipeline_s']==case['mean_cached_pipeline_s'];bindings[str(trial/'receipt.json')]=sha(trial/'receipt.json')
   groups={mode:[v for v in r['results'] if v['mode']==mode] for mode in ('off','on')};assert all(len(v)==4 for v in groups.values())
   avg=lambda group,key:sum(v[key] for v in group)/len(group)
   overhead=avg(groups['on'],'estimator_s')+avg(groups['on'],'payload_s')
   native_saving=avg(groups['off'],'native_route_s')-avg(groups['on'],'native_route_s')
   off=avg(groups['off'],'cached_pipeline_s');on=avg(groups['on'],'cached_pipeline_s');assert on>off
   qor=case['qor'];delay_delta=qor['on']['cpd_ns']-qor['off']['cpd_ns'];wire_delta=qor['on']['wirelength']-qor['off']['wirelength']
   cycles=[]
   for cycle in (0,1):
    subset=r['results'][cycle*4:(cycle+1)*4];a=[v for v in subset if v['mode']=='off'];b=[v for v in subset if v['mode']=='on'];cycles.append({'cycle':cycle,'native_phase_saving_s':avg(a,'native_route_s')-avg(b,'native_route_s'),'pipeline_extra_s':avg(b,'cached_pipeline_s')-avg(a,'cached_pipeline_s')})
   row={'family':family,'design':design,'mean_off_s':off,'mean_on_s':on,'mean_estimator_payload_s':overhead,'mean_native_saving_s':native_saving,'overhead_alone_exceeds_full_off':overhead>off,'observed_overhead_budget_s':max(0,native_saving),'positive_native_saving_in_both_cycles':all(v['native_phase_saving_s']>0 for v in cycles),'cpd_delta_ns':delay_delta,'wirelength_delta':wire_delta,'qor_pareto_improvement':delay_delta<=0 and wire_delta<=0 and (delay_delta<0 or wire_delta<0),'cycles':cycles};rows.append(row)
 assert all(sha(path)==digest for path,digest in bindings.items())
 out=base/'feedback_two_family_cost_frontier_2026-10-06';out.mkdir();shutil.copyfile(__file__,out/'source.py')
 report={'inputs_sha256':bindings,'source_sha256':sha(__file__),'rows':rows,'family_count':2,'all_fresh_cached_on_slower':all(v['mean_on_s']>v['mean_off_s'] for v in rows),'qor_pareto_improvement_count':sum(v['qor_pareto_improvement'] for v in rows),'scope':'Post-outcome algebraic diagnostic of actual means, not a prospective gate, statistical confidence interval or measurable amortized reuse gain. Native savings are descriptive under concurrent workload; all immutable source/cohort/model scopes inherited from authenticated summaries. No strict unseen-family or hardware claim.'}
 (out/'report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'receipt.json').write_text(json.dumps({'report_sha256':sha(out/'report.json'),'all_checks_pass':True},indent=2)+'\n')
 for row in rows:print(json.dumps({k:v for k,v in row.items() if k!='cycles'}),flush=True)

if __name__=='__main__':main()
