"""Complete12 original-budget seed serialization with one old import per graph."""
import json,time,sys
from pathlib import Path
from retained_seed_session_v1 import RetainedSeedSession
from class_cached_rc_endpoint_session_v2 import clear_cache,STATS
from pre_route_endpoints import sha
R=Path(__file__).resolve().parents[1];sys.path.insert(0,str(R/'tools/native_resume_prototype'));from source_binding_v2 import closure
D=R/'experiments/retained_seed_session_cohort_v1_2026-10-08';D.mkdir(exist_ok=False)
pp=R/'experiments/owner50_retained_rr_2026-10-07_predictor/protocol.json';p=json.loads(pp.read_text());bindings={**closure([Path(__file__)]),str(pp):sha(pp)}
(D/'protocol.json').write_text(json.dumps(dict(bindings=bindings,cases=p['cases'],scope='All12 fixed developer moves; one cold RR template and original native route/template import per width, all original budgets, no historical forest/seed production inputs. No accepted route epoch advancement.'),indent=2)+'\n')
clear_cache();start=time.perf_counter();rows=[]
for width in (8,16,32):
 cases=sorted([c for c in p['cases'] if c['width']==width],key=lambda c:c['index']);old=json.loads(Path(cases[0]['old']).read_text());route=Path(old['inputs']['graph']['path']).with_name('design.route')
 tick=time.perf_counter();session=RetainedSeedSession(cases[0]['old'],route);setup=time.perf_counter()-tick
 for c in cases:
  assert sha(c['old'])==sha(cases[0]['old'])
  tick=time.perf_counter();result=session.write_seed(c['target'],c['budget'],D/f'w{width}_m{c["index"]}');elapsed=time.perf_counter()-tick
  bindings.update(result['forest']['bindings']);bindings[result['route']]=result['route_sha256'];forest=Path(result['route']).with_name('forest.json');bindings[str(forest)]=sha(forest)
  row=dict(width=width,index=c['index'],setup_seconds=setup if c['index']==0 else 0,selection_serialization_seconds=elapsed,route=result['route'],route_sha256=result['route_sha256'],retained=len(result['forest']['retained']),released=len(result['forest']['released']),retained_nets=result['retained_nets']);rows.append(row);print(width,c['index'],'seed',row['retained'],row['released'],flush=True)
 assert session.imports==1 and session.selections==4
elapsed=time.perf_counter()-start;assert len(rows)==12 and all(sha(f)==h for f,h in bindings.items())
(D/'receipt.json').write_text(json.dumps(dict(bindings=bindings,rows=rows,protocol_sha256=sha(D/'protocol.json'),cohort_component_seconds=elapsed,cache_stats=dict(STATS),scope='One observed full12 seed component; initial cold template/import/pin/trace parse and per-target hash/selection/serialization/path replay included. Upstream input production and final receipt/external independent audit/native resume excluded; no full workflow speedup or all-budget feasibility.'),indent=2)+'\n');print('Complete12 seed session',elapsed,STATS)
