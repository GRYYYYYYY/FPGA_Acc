"""Audit paired engine replays, separating traced allocation and timing evidence."""
import json,shutil
from pathlib import Path
from pre_route_endpoints import sha
root=Path('experiments/paired_feedback_2026-10-04');protocol=json.loads((root/'protocol.json').read_text());rows=[];reference=None;oracle=Path('experiments/prospective_local_feedback_v3_2026-10-04')
for entry in protocol['order']:
    p=root/entry['run_id'];config=json.loads((p/'protocol.json').read_text());r=json.loads((p/'receipt.json').read_text());d=json.loads((p/'decision.json').read_text())
    assert sha(p/'protocol.json')==r['protocol_sha256'];assert sha(p/'decision.json')==r['decision_sha256']
    for n,digest in protocol['sources_sha256'].items():assert config['source_sha256'][n]==digest
    for v in list(config['inputs'].values())+list(config['placements'].values())+[config['baseline_timing_context']]:assert sha(v['path'])==v['sha256']
    comparable={'scores':d['scores'],'selected':d['selected_candidate'],'native':r['selected_native_metrics'],'accept':r['accept']}
    if reference is None:reference=comparable
    assert reference==comparable
    for cid in range(1,9):
        for kind in ('prediction','proxy'):
            actual=json.loads((p/f'candidate_{cid}_{kind}.json').read_text());expected=json.loads((oracle/f'candidate_{cid}_{kind}.json').read_text());assert actual==expected
    rows.append({'run_id':entry['run_id'],'engine':r['engine'],'cold_s':r['cold_prepare_and_baseline_wall_s'],'eight_queries_s':r['eight_warm_queries_wall_s'],'selected_native_s':r['selected_native_launcher_wall_s'],'validation_s':r['validation_wall_s'],'peak_process_rss_kib':r['peak_process_rss_kib'],'full_experiment_s':r['full_experiment_wall_s'],'exact_archived_predictions_and_proxy':True})
byid={r['run_id']:r for r in rows};original=byid['original2'];indexed=byid['indexed2'];metrics={}
for name in ('cold_s','eight_queries_s','selected_native_s','full_experiment_s'):
    metrics[name]={'original':original[name],'indexed':indexed[name],'indexed_over_original':indexed[name]/original[name]}
memory={n:json.loads((root/f'memory_{n}.json').read_text()) for n in ('original','indexed')};allocation_delta=memory['indexed']['retained_python_allocations_bytes']-memory['original']['retained_python_allocations_bytes']
result={'protocol_sha256':sha(root/'protocol.json'),'rows':rows,'primary_pair':'indexed2 vs original2; both without concurrent RouteCast memory measurement','primary_metrics':metrics,'selected_candidate':reference['selected'],'native':reference['native'],'accept':reference['accept'],'memory':memory,'retained_search_index_delta_bytes':allocation_delta,'limitations':['known single-design candidates','shared host other workloads uncontrolled','two implementation rounds only; first original had brief concurrent memory tracing','allocation probe physical graph, timing engine quotient graph; do not equate their bytes','candidate generation and baseline STA acquisition reused','not sketch on/off net speedup; native reference already archived']}
(root/'comparison.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({k:v for k,v in result.items() if k not in ('memory','rows')}))
