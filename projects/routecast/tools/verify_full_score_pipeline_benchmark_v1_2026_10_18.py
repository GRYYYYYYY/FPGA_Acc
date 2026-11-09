"""Audit paired records, output hashes and setup amortization without extrapolation."""
import hashlib,json,math,statistics,subprocess
from pathlib import Path

def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 root=Path('experiments/full_score_pipeline_benchmark_v1_2026-10-18');rp=root/'results.json';pp=root/'protocol.json';r=json.loads(rp.read_text());p=json.loads(pp.read_text());assert r['status']=='pass'
 rows=[json.loads(line) for line in (root/'measurements.jsonl').read_text().splitlines()];assert rows==r['records'] and len(rows)==24
 for path,h in p['bindings'].items():assert sha(path)==h
 outputs=set();summary=[]
 for case in p['cases']:
  pairs=[]
  for repeat in range(p['repeats']):
   pair=[v for v in rows if v['case']==case and v['repeat']==repeat];assert [v['arm'] for v in pair]==(['incremental','rebuild'] if repeat%2==0 else ['rebuild','incremental'])
   values={v['arm']:v for v in pair}
   for v in pair:
    assert v['total_seconds']>0 and all(t>=0 for t in v['stages'].values())
    assert sum(v['stages'].values())<=v['total_seconds']+1e-6
    assert len(v['outputs'])==2
    for item in v['outputs']:
     path=Path(item['path']);assert path not in outputs;outputs.add(path)
     assert path.stat().st_size==item['bytes']==904438*8 and sha(path)==item['sha256']
   assert [x['sha256'] for x in values['incremental']['outputs']]==[x['sha256'] for x in values['rebuild']['outputs']]
   pairs.append(values['rebuild']['total_seconds']-values['incremental']['total_seconds'])
  selected=[v for v in rows if v['case']==case];inc=statistics.median(v['total_seconds'] for v in selected if v['arm']=='incremental');full=statistics.median(v['total_seconds'] for v in selected if v['arm']=='rebuild');initial=selected[0]['initial_cache_setup_seconds_excluded'];assert all(v['initial_cache_setup_seconds_excluded']==initial for v in selected)
  stages={arm:{key:statistics.median(v['stages'][key] for v in selected if v['arm']==arm) for key in next(v for v in selected if v['arm']==arm)['stages']} for arm in ['incremental','rebuild']}
  summary.append(dict(case=case,incremental_median_seconds=inc,rebuild_median_seconds=full,paired_savings_seconds=pairs,incremental_wins=sum(x>0 for x in pairs),initial_cache_seconds=initial,one_initialization_plus_one_update_seconds=initial+inc,arithmetic_break_even_updates_if_stationary=math.ceil(initial/(full-inc)) if full>inc else None,stage_medians_seconds=stages))
 matches=subprocess.check_output(['rg','-l','joint_full_score_state_v1|typed_NET_collision|typed_group_mean','tools','-g','*.py'],text=True).splitlines()
 consumer_bindings={str(Path(path).resolve()):sha(path) for path in matches}
 decision=dict(status='all24_frame_to_score_file_arms_verified_warm_component_gain_only',bindings={str(q.resolve()):sha(q) for q in [rp,pp,root/'measurements.jsonl',Path(__file__)]},summary=summary,verified_output_files=len(outputs),consumer_source_snapshot=consumer_bindings,consumer_evidence='Read tools/evaluate_mmc_typed_risk_matrix_v1_2026_10_18.py: binary vector manifest/read -> ranking metrics -> evaluation JSON. This benchmark writes that compatible score-file format; it does not integrate the Joint state or typed scores into a native routing decision. rg snapshot is scoped to Python tools and is not a complete cross-language dependency proof.',setup=r['setup'],interpretation='Warm offline score-file processing improves in all12paired comparisons. Initial cache construction exceeds savings from one update in every case. Break-even counts are arithmetic stationary extrapolations, not observed repeated-stream experiments or complete RouteCast net benefit.',limitations=['Only4timing repeats per exposed case, shared host and uncontrolled filesystem cache.','Output close+hash measured; no fsync/physical-disk durability claim.','Original XML parse and warm-static index load measured once; not repeated cold-start statistics.','Resident old cache is present during both arms; process memory/RSS and concurrent tenants not isolated.','Target source-path generation and native routing costs excluded from both arms.','Original prediction/native utility gates and strict-unseen requirements remain unmet.'],next_action='Stop treating score maintenance as the remaining main research bottleneck. Preserve this verified warm offline gain, then audit the upstream source-path generation/feedback pipeline and main accuracy/native utility failures to select the next algorithm experiment. Any complete time claim must include those upstream and downstream stages, cache initialization and actual update count; any predictor improvement needs frozen validation beyond these exposed cases.')
 with (root/'verification_and_decision_v1.json').open('x') as f:json.dump(decision,f,indent=2)
 print(json.dumps([{k:v for k,v in s.items() if k!='stage_medians_seconds'} for s in summary]))
if __name__=='__main__':main()
