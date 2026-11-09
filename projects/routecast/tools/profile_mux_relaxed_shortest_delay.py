"""One frozen conditional-floor query profile; diagnostic, not prospective routing."""
import cProfile,json,pstats,time
from pathlib import Path
from persistent_rc_context import PersistentRCContext
from online_conflict_core import shortest_delay
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1]
base=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06'
out=ROOT/'experiments/mux_relaxed_shortest_profile_2026-10-06';out.mkdir()
p=json.loads((base/'protocol.json').read_text());case=next(c for c in p['cases'] if (c['width'],c['index'])==(32,2));ctx=PersistentRCContext(case['target']);data=json.loads((base/'w32_m2/result.json').read_text());spec=data['allocations'][1];net=int(next(iter(spec['restrictions'])));bans=set(spec['restrictions'][str(net)]);q=next(q for q in ctx.context[5] if q['net_id']==net);profile=cProfile.Profile();start=time.perf_counter();profile.enable();r=shortest_delay(ctx,q['source'],q['sink'],bans);profile.disable();elapsed=time.perf_counter()-start
profile.dump_stats(str(out/'shortest.prof'))
with (out/'profile.txt').open('w') as f:pstats.Stats(profile,stream=f).sort_stats('cumulative').print_stats(20)
(out/'receipt.json').write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),solver_sha256=sha(ROOT/'tools/online_conflict_core.py'),baseline_result_sha256=sha(base/'w32_m2/result.json'),query=q,forbidden=sorted(bans),finite_labels=len(r['distances']),minimum=r['minimum'],elapsed_s=elapsed,files={str(out/f):sha(out/f) for f in ('shortest.prof','profile.txt')},scope='One profiled frozen conditional-floor shortest query, includes profiler overhead/context setup excluded. No outcome/certificate independence or matched lifecycle performance claim.'),indent=2)+'\n');print('profiled',len(r['distances']),'labels',elapsed,'seconds')
