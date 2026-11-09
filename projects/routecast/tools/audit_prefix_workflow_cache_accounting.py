"""Verify actual cross-stage reuse and an explicitly cold baseline restart."""
import json
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/owner50_prefix_acceptance_workflow_2026-10-07';r=json.loads((out/'receipt.json').read_text());p=json.loads((out/'protocol.json').read_text());assert r['complete'] and r['protocol_sha256']==sha(out/'protocol.json');assert all(sha(f)==h for f,h in p['sources'].items());events=r['cache_events'];assert events[0]['event']=='workflow_cold_start' and events[0]['stats']==dict(builds=0,hits=0,evictions=0);lookup={x['event']:x for x in events};assert lookup['baseline_cold_start']['stats']==dict(builds=0,hits=0,evictions=0)
rows=[]
for name in ('floor_preparation','floor_independent_proof','full12_prediction','all10_native_fallback','fresh_full12_cold_baseline'):
 e=lookup[name];a,b=e['before'],e['after'];assert all(b[k]>=a[k] for k in a);rows.append(dict(stage=name,builds_delta=b['builds']-a['builds'],hits_delta=b['hits']-a['hits'],before=a,after=b))
assert lookup['all10_native_fallback']['after']['builds']==lookup['all10_native_fallback']['before']['builds'];assert lookup['all10_native_fallback']['after']['hits']-lookup['all10_native_fallback']['before']['hits']==10
assert lookup['fresh_full12_cold_baseline']['before']==dict(builds=0,hits=0,evictions=0);assert lookup['fresh_full12_cold_baseline']['after']==dict(builds=3,hits=9,evictions=0)
for key,suffix in [('floor_prepare','floor'),('floor_verify','floor'),('predictor','predictor'),('fallback_trial','fallback'),('cold_trial','cold')]:
 f=ROOT/f'experiments/owner50_prefix_workflow_2026-10-07_{suffix}'/f'rr_cache_stats_{key}.json';assert f.exists();rows.append(dict(phase_stats_file=str(f),sha256=sha(f)))
(out/'cache_accounting.json').write_text(json.dumps(dict(receipt_sha256=sha(out/'receipt.json'),auditor_sha256=sha(Path(__file__)),rows=rows,scope='Actual cache event deltas prove sameprocess crossstage graphretention and10warmfallback constructors; explicit baselinecacheclear followed3build9hits, coldstartup included. Separatefloorprepare/proof statsfiles prevent overwrites. OSfile/module caches not cleared; threeentry cap not RSSbound orconcurrentpublication.'),indent=2)+'\n');print('Retained graph accounting passed')
