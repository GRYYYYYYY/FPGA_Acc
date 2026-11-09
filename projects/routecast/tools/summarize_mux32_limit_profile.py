"""Archive profiled trace parity and disjoint exclusive-function cost groups."""
import json,pstats,shutil
from pathlib import Path
from collections import defaultdict
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];out=ROOT/'experiments/mux32_limit_profile_tree_2026-10-07';reference=ROOT/'experiments/mux32_limit_retry_tree_2026-10-07';rp=out/'receipt.json';r=json.loads(rp.read_text());v=json.loads((out/'verification.json').read_text());original=json.loads((reference/'receipt.json').read_text());assert v['receipt_sha256']==sha(rp);assert r['candidate_sha256']==original['candidate_sha256'] and r['trace']==original['trace']
profile=out/'profile.pstats';shutil.copyfile('/tmp/routecast_mux32_limit_profile.pstats',profile);stats=pstats.Stats(str(profile));groups=defaultdict(float);functions=[]
for (file,line,name),(primitive,calls,exclusive,cumulative,callers) in stats.stats.items():
 groups[file]+=exclusive
 functions.append(dict(file=file,line=line,function=name,calls=calls,exclusive_seconds=exclusive,cumulative_seconds=cumulative))
result=dict(source_sha256=sha(Path(__file__)),bindings={str(p):sha(p) for p in (rp,out/'verification.json',out/'candidate.json',reference/'receipt.json',reference/'verification.json',profile)},complete_candidate_bytes_and_all_trial_events_identical=True,profiled_producer_wall_seconds=r['producer_seconds'],profile_total_function_exclusive_seconds=stats.total_tt,exclusive_by_file=sorted((dict(file=f,seconds=t) for f,t in groups.items()),key=lambda x:-x['seconds']),top_cumulative_functions=sorted(functions,key=lambda x:-x['cumulative_seconds'])[:20],scope='Actual same9NET profile, cProfile overhead included. Exclusive groups disjoint; cumulative functions nested and must not be added. Whole candidate/trace exactly canonical-audited reference; native evidence reused for identical candidate. Not uninstrumented phase timing, stable acceleration or full-loop netgain.')
(out/'profile_summary.json').write_text(json.dumps(result,indent=2)+'\n');print(result['profiled_producer_wall_seconds']);print(result['exclusive_by_file'][:6]);print(result['top_cumulative_functions'][:8])
