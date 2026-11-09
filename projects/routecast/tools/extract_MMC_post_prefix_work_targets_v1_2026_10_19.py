"""Strict post-checkpoint1 native work labels; no remaining-time inference."""
import pathlib,json,hashlib
from fractions import Fraction
R=pathlib.Path(__file__).resolve().parents[1]
def sha(p):
 h=hashlib.sha256()
 with pathlib.Path(p).open('rb') as f:
  for b in iter(lambda:f.read(2**20),b''):h.update(b)
 return h.hexdigest()
def main():
 out=R/'experiments/mmc_post_prefix_work_targets_v1_2026-10-19';out.mkdir();native=R/'experiments/mmc_native_owner_trace_replay_v2_2026-10-18';cp=native/'cohort_verification.json';cohort=json.loads(cp.read_text());assert cohort['all6_streamed_NET_ownership_checkpoints_final_unions_and_exact_counters_pass'];splitroot=R/'experiments/mmc_prefix_future_pressure_split_v1_2026-10-18';sp=splitroot/'verification.json';split=json.loads(sp.read_text());lookup={(x['case'],x['policy']):x for x in split['cases']};keys=['NET_operations','connection_operations','heap_pushes','heap_pops'];bindings={str(p):sha(p) for p in [pathlib.Path(__file__).resolve(),cp,sp]};rows=[]
 for entry in sorted(cohort['rows'],key=lambda x:(x['case'],x['arm'])):
  case,policy=entry['case'],entry['arm'];proof=pathlib.Path(entry['proof']);assert cohort['bindings'][str(proof)]==sha(proof);v=json.loads(proof.read_text());assert v['all_exact_iteration_and_aggregate_work_counters_equal'];trace=R/f'experiments/mmc_native_owner_cascade_trace_v1_2026-10-18/{case}/{policy}/owner_trace.tsv';stats=[];first_end=None;digest=hashlib.sha256()
  with trace.open('rb') as f:
   while True:
    line=f.readline()
    if not line:break
    digest.update(line)
    if line.startswith(b'S '):
     w=line.split();assert len(w)==6;it=int(w[1]);assert it==len(stats)+1;values=list(map(int,w[2:]));assert all(x>=0 for x in values) and values[3]<=values[2];stats.append(dict(iteration=it,**dict(zip(keys,values))))
     if it==1:first_end=f.tell()
  assert stats==v['iteration_stats'];assert digest.hexdigest()==v['bindings'][str(trace)]==lookup[case,policy]['source_trace_sha256'];assert first_end<=lookup[case,policy]['first_checkpoint_end_byte'];assert len(stats)>1;folder=out/f'{case}_{policy}';folder.mkdir();first=dict(schema='MMC_PREFIX1_ROUTER_WORK_V1',case=case,policy=policy,observed_iteration=1,work={k:stats[0][k] for k in keys});future=dict(schema='MMC_POST_PREFIX_ROUTER_WORK_TARGETS_V1',case=case,policy=policy,first_target_iteration=2,last_target_iteration=stats[-1]['iteration'],totals={k:sum(x[k] for x in stats[1:]) for k in keys},by_iteration=stats[1:])
  for k in keys:assert first['work'][k]+future['totals'][k]==sum(x[k] for x in stats)
  (folder/'features.json').write_text(json.dumps(first,indent=2)+'\n');(folder/'targets.json').write_text(json.dumps(future,indent=2)+'\n');pf=splitroot/f'{case}_{policy}/targets.json';pressure=json.loads(pf.read_text());assert pressure['first_target_iteration']==2 and pressure['last_target_iteration']==stats[-1]['iteration'];mass=sum(pressure['targets']['sum_checkpoint_overflow_units'].values());bindings[str(proof)]=sha(proof);bindings[str(trace)]=digest.hexdigest();bindings[str(pf)]=sha(pf);rows.append(dict(case=case,policy=policy,cutoff_iteration=1,first_work_record_end_byte=first_end,prefix_checkpoint_end_byte=lookup[case,policy]['first_checkpoint_end_byte'],future_pressure_mass_all_RR=mass,future_work=future['totals'],features_sha256=sha(folder/'features.json'),targets_sha256=sha(folder/'targets.json')));print(case,policy,future['totals']['heap_pushes'],flush=True)
 paired=[]
 for case in ['case_01','case_02','case_03']:
  off=next(x for x in rows if x['case']==case and x['policy']=='off');on=next(x for x in rows if x['case']==case and x['policy']=='on');paired.append(dict(case=case,pressure_change_fraction=str(Fraction(on['future_pressure_mass_all_RR'],off['future_pressure_mass_all_RR'])-1),work_change_fractions={k:str(Fraction(on['future_work'][k],off['future_work'][k])-1) for k in keys}))
 result=dict(status='all6_post_prefix_work_targets_exactly_match_admitted_native_counters',bindings=bindings,cases=rows,paired_policy_comparisons=paired,scope='Retrospective exposed-data label reconciliation. Features contain iteration1 counters only; targets contain iterations2throughterminal. NET/connection operations and heap counts are not unique identities, causal savings, perRR work labels or elapsed time. Pressure endpoints follow local OPIN allocation, while S counters precede it; both are strictly beyond cutoff but are different measurements.',new_native_jobs=0,trained_predictor=False,accepted_gain=False,strict_unseen_admitted=False);(out/'verification.json').write_text(json.dumps(result,indent=2)+'\n')
if __name__=='__main__':main()
