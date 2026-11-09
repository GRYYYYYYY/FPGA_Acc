"""Require exact result parity before interpreting profiled Python stages."""
import json,pstats,shutil
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux_heuristic_python_profile_2026-10-07';old=ROOT/'experiments/mux_heuristic_budget_cohort_2026-10-07/w32_m2/result.json';new=out/'w32_m2/result.json';assert old.read_bytes()==new.read_bytes();rf=out/'receipt.json';r=json.loads(rf.read_text());assert len(r['rows'])==1 and r['rows'][0]['result_sha256']==sha(new);pf=out/'profile.pstats';shutil.copyfile('/tmp/routecast_heuristic_python_profile_2026-10-07.pstats',pf);stats=pstats.Stats(str(pf));rows=[]
for (file,line,name),(primitive,calls,self_s,cumulative_s,callers) in stats.stats.items():
 if '/routecast/tools/' in file:
  rows.append(dict(file=file,line=line,function=name,primitive_calls=primitive,calls=calls,self_seconds=self_s,cumulative_seconds=cumulative_s))
rows.sort(key=lambda x:x['self_seconds'],reverse=True)
(out/'profile_summary.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),bindings={str(f):sha(f) for f in (old,new,rf,pf)},rows=rows,scope='Single cProfile observation with exact whole-result byte parity to independently audited heuristic case32m2. Profiler/concurrent workload overhead, no paired speedup or accepted-lifecycle claim. Self and cumulative times must not be summed across nesting.'),indent=2)+'\n');print(rows[:12],flush=True)
