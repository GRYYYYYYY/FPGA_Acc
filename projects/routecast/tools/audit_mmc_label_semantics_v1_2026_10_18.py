"""Separate final unit-channel occupancy, span density and native work pressure."""
import json,sys
from pathlib import Path
from collections import Counter
from fractions import Fraction
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from source_binding_v2 import closure
from versioned_digest_cache_v1 import Cache

def main():
 qroot=R/'experiments/mmc_terminal_batch_quality_v1_2026-10-18';quality=qroot/'research_decision_v1.json';q=json.loads(quality.read_text());assert q['all108_full_domain_metric_vectors_independently_verified'] if 'all108_full_domain_metric_vectors_independently_verified' in q else q['status']=='all108_terminal_batch_metric_vectors_independently_verified'
 pressure=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18/guard_resource_type_diagnostic_v1.json';p=json.loads(pressure.read_text());assert p['status']=='pass'
 replay=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18/cohort_verification.json';r=json.loads(replay.read_text());assert r['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass']
 bindings={**q['bindings'],**p['bindings'],str(quality):sha(quality),str(pressure):sha(pressure),str(replay):sha(replay),**closure([Path(__file__)])}
 out=R/'experiments/mmc_label_semantics_v1_2026-10-18';out.mkdir();rows=[];cache=Cache()
 with cache.installed():
  assert all(sha(path)==h for path,h in bindings.items())
  for case in ['case_01','case_02','case_03']:
   vectors=qroot/case/'vectors.json';assert bindings[str(vectors)]==sha(vectors);v=json.loads(vectors.read_text())
   assert len(v['channels'])==258720 and all(c['capacity']==1 for c in v['channels'])
   for label in ['cold','partial_seed_default','partial_seed_firstpass_preserve']:
    concrete=Counter(c['labels'][label] for c in v['channels']);assert set(concrete)<={0,1}
    bins={tuple(c['key']):Fraction(c['labels'][label],c['capacity']) for c in v['bins']}
    ordered=sorted(bins,key=lambda n:(-bins[n],n));cut=bins[ordered[19]]
    rows.append(dict(case=case,label=label,positive_channel_universe=258720,final_channel_occupancy_histogram=dict(concrete),final_channel_overflow_units=0,concrete_top5percent_K=12936,maximum_truth_tie_size=concrete[1],concrete_truth_strictly_above_topK_cut=0,span_bins=len(bins),span_density_distinct_values=len(set(bins.values())),span_top20_cut=str(cut),span_bins_strictly_above_cut=sum(value>cut for value in bins.values()),span_bins_equal_cut=sum(value==cut for value in bins.values())))
   print('LABEL SEMANTICS',case,flush=True)
  pressures=[]
  for row in p['rows']:
   iterations=sorted((int(i),v) for i,v in row['iterations'].items());assert iterations[-1][1]['overused_RR_nodes']==0
   peak=max(iterations,key=lambda x:x[1]['overused_RR_nodes']);area=sum(v['overused_RR_nodes'] for i,v in iterations)
   assert area>0
   pressures.append(dict(case=row['case'],policy=row['arm'],iterations=len(iterations),first_iteration_overused_RR_nodes=iterations[0][1]['overused_RR_nodes'],peak_iteration=peak[0],peak_overused_RR_nodes=peak[1]['overused_RR_nodes'],last_iteration_overused_RR_nodes=0,sum_overused_node_counts_over_checkpoints=area,scope='Count of overusedRRs at audited iteration-end checkpoints only; not overflow units, accumulated perRR history, exact first_guard sole cause, cold-label pressure or a new prediction gate.'))
  assert all(sha(path)==h for path,h in bindings.items())
  with (out/'audit.json').open('x') as stream:json.dump(dict(status='pass',bindings=bindings,final_labels=rows,existing_partial_seed_policy_pressure=pressures,findings=['Final legal unit-capacity concrete labels are binary occupied/unoccupied, with a large maximum-value topK tie; fixedID overlap is an occupancy-subset comparison.','Spatial span density is a separate aggregate target and can have nonbinary values; aggregation does not retain individual track identity.','All6 archived partial-seed runs have nonzero intermediate overuse but zero final overuse. Final occupancy cannot reconstruct routing pressure history or reroute work.','These pressure traces use fixed partial-seed policies, not cold primary labels. They must not replace the existing cold quality gate.','No varied success/failure cohort, unseen-family validation or fresh full-flow gain follows from this diagnostic.'],scope='Measurement taxonomy only; old failed gates unchanged. Exact source vectors previously independently admitted; no new route label generated, native job launched or candidate selected using these diagnostics.'),stream,indent=2)

if __name__=='__main__':main()
