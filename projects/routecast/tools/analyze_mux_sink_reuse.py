"""Retrospective sink repetition potential, never predictor inputs."""
import json
from collections import OrderedDict,Counter
from pathlib import Path
from pre_route_endpoints import sha
ROOT=Path(__file__).resolve().parents[1];file=ROOT/'experiments/mux_net_slack_online_loop_2026-10-06/w32_m2/result.json';d=json.loads(file.read_text());sinks=[];unrecorded=0
for attempt in d['attempts']:
 update=attempt['update'];events=list(update['incremental']['events'])
 if update['repair']:
  events += [e for e in update['repair']['events'] if e['type'] in ('QUERY','BUDGET_WITNESS')]
  unrecorded+=int((update['repair'].get('failure') or {}).get('status')=='NO_BOUNDED_RELAXED_WITNESS')
 sinks.extend(e['query']['sink'] for e in events)
assert len(sinks)+unrecorded==2820
rows=[]
for limit in (16,64,256,1024,4096):
 cache=OrderedDict();hits=0
 for sink in sinks:
  if sink in cache:hits+=1;cache.move_to_end(sink)
  else:
   cache[sink]=None
   if len(cache)>limit:cache.popitem(last=False)
 rows.append(dict(entries=limit,hits=hits,misses=len(sinks)-hits))
out=ROOT/'experiments/mux_owned_reverse_graph_2026-10-06/sink_reuse_diagnostic.json'
out.write_text(json.dumps(dict(source_sha256=sha(Path(__file__)),result_sha256=sha(file),recorded_queries=len(sinks),unrecorded_queries=unrecorded,unique_sinks=len(set(sinks)),lru=rows,scope='Retrospective chronological sink-only LRU simulation assuming unchanged disabled-edge mask; upper-bound reuse potential, not measured native cache or speedup. Costs/demand/labels do not enter relaxed bound, but MAX-sentinel mask changes require explicit invalidation. Never used as predictor oracle.'),indent=2)+'\n');print(len(sinks),len(set(sinks)),rows)
