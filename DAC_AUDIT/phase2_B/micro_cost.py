"""Aggregate operation diagnostics on frozen initial real endpoint coordinates; not a flow speedup."""
import sys,json,time,statistics,resource,hashlib
from pathlib import Path
D=Path(__file__).resolve().parent;A=D.parent/'phase2_A';sys.path.insert(0,str(A/'source'));sys.path.insert(0,str(D))
from tileplace_v2 import TilePlaceV2Engine as E,V2Config
from reuse import Memo
p=json.loads((D/'PROTOCOL.json').read_text());result=[];start=time.monotonic()
for c in p['cases']:
 cmd=c['command_template'];arg=lambda f:Path(cmd[cmd.index(f)+1]);e=E(arg('--contract'),arg('--input-place'),V2Config(critical_distance_guard_q=0))
 # Use the actual initial route pressure builder, measured as diagnostic setup.
 from prepare_route_feedback import prepare
 from run_tileplace_v2 import load_feedback_from_payload
 baseline=json.loads(arg('--baseline-closure').read_text());route=Path(baseline['outputs']['route']['path']) if 'route' in baseline.get('outputs',{}) else None
 if route is None:
  for v in baseline.get('outputs',{}).values():
   if str(v['path']).endswith('.route'):route=Path(v['path']);break
 assert route is not None
 e.pressure_q16=load_feedback_from_payload(prepare(route,arg('--rr-graph')))
 pairs=[(s,t) for cc in e.connections.values() for s,t,_ in cc][:2048];assert pairs;N=20000
 keys=[(1,e.positions[s][0],e.positions[s][1],e.positions[t][0],e.positions[t][1]) for s,t in pairs];table={k:0 for k in keys};stats={}
 def bench(name,func):
  t=time.perf_counter_ns();func();stats[name]=(time.perf_counter_ns()-t)/1e9
 def loop():
  for i in range(N):s,t=pairs[i%len(pairs)]
 def keybuild():
  for i in range(N):
   s,t=pairs[i%len(pairs)];a,b=e.positions[s],e.positions[t];key=(1,a[0],a[1],b[0],b[1])
 def lookup():
  for i in range(N):value=table.get(keys[i%len(keys)])
 def calculate():
  for i in range(N):s,t=pairs[i%len(pairs)];value=E._connection_congestion(e,s,t,e.positions)
 def copies():
  for i in range(N):candidate=dict(e.positions)
 memo=Memo();memo.reset()
 def missfill():
  for s,t in pairs:memo.get(e,s,t,e.positions,E._connection_congestion)
 def hitreturn():
  for i in range(N):s,t=pairs[i%len(pairs)];memo.get(e,s,t,e.positions,E._connection_congestion)
 for name,func in [('loop_control',loop),('key_construct',keybuild),('dictionary_lookup',lookup),('prefix_scalar_compute',calculate),('position_dict_copy',copies),('memo_cold_fill',missfill),('memo_hit_path_including_key_counters_return',hitreturn)]:bench(name,func)
 # Deterministic eviction/invalidation aggregate; setup time remains in outer diagnostic charge.
 full={i:i for i in range(131072)}
 def evict():
  for i in range(2000):full.pop(next(iter(full)));full[131072+i]=i
 bench('fifo_2000_evictions',evict);bench('clear_131072_entries',full.clear)
 result.append({'case':c['case'],'N':N,'pair_count':len(pairs),'initial_position_count':len(e.positions),'seconds':stats,'memo_stats':dict(memo.stats),'pressure_edges':len(e.pressure_q16)})
print(json.dumps({'cases':result,'wall_s':time.monotonic()-start,'maxrss_kib':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'limits':'Initial real endpoint microdiagnostic; loops include Python dispatch, not a complete workload distribution. Do not multiply into full proposal or subtract diagnostic timers from performance.'},indent=2))
