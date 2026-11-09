"""Verify profiled full12 seed bytes/forests and preserve non-additive call costs."""
import json,pstats,shutil
from pathlib import Path
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];D=R/'experiments/seed_preparation_profile_v1_2026-10-08';B=R/'experiments/retained_seed_session_cohort_v3_2026-10-08'
r=json.loads((D/'receipt.json').read_text());b=json.loads((B/'receipt.json').read_text())
for doc in (r,b):assert all(sha(f)==h for f,h in doc['bindings'].items())
assert len(r['rows'])==len(b['rows'])==12 and r['cache_stats']==b['cache_stats']
for x,y in zip(r['rows'],b['rows']):
 assert (x['width'],x['index'],x['retained'],x['released'])==(y['width'],y['index'],y['retained'],y['released'])
 assert Path(x['route']).read_bytes()==Path(y['route']).read_bytes()
 assert json.loads(Path(x['route']).with_name('forest.json').read_text())==json.loads(Path(y['route']).with_name('forest.json').read_text())
profile=D/'profile.pstats';shutil.copyfile('/tmp/routecast_seed_preparation_profile_v1.pstats',profile)
stats=pstats.Stats(str(profile));calls=[]
for (file,line,name),(primitive,total,exclusive,cumulative,callers) in stats.stats.items():
 if '/tools/' in file or name in ('Parse','feed','_parse_whole'):
  calls.append(dict(file=file,line=line,name=name,primitive_calls=primitive,total_calls=total,exclusive_seconds=exclusive,cumulative_seconds=cumulative))
hot=sorted(calls,key=lambda x:x['exclusive_seconds'],reverse=True)[:25]
selected=[x for x in calls if x['name'] in ('load_endpoints','load_complete','freeze_node','write_seed','__init__','select') and '/tools/' in x['file']]
bindings={str(p):sha(p) for p in (D/'receipt.json',B/'receipt.json',profile,Path(__file__))}
report=dict(bindings=bindings,all12_seed_bytes_and_forests_equal=True,cache_stats=r['cache_stats'],profiled_component_seconds=r['cohort_component_seconds'],profile_total_seconds=stats.total_tt,exclusive_hotspots=hot,selected_nested_calls=selected,scope='cProfile-instrumented complete12 seed preparation; exact output parity with fresh v3. Profiler overhead included, timings not comparable to uninstrumented workflow. Cumulative/nested costs overlap and must not be added; exclusive hotspots guide diagnosis only. No native rerun, original-budget acceptance or end-to-end gain.')
(D/'profile_verification.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:v for k,v in report.items() if k not in ('bindings','selected_nested_calls')},indent=2))
