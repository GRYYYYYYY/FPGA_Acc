"""Reachable-object memory accounting plus selected high-fanout equivalence."""
from pathlib import Path
import json,gc,shutil
from collections import defaultdict
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from normalized_rc_net_pressure import NormalizedRCNetPressure
from fast_normalized_rc_net_pressure import FastNormalizedRCNetPressure
from slim_fast_normalized_rc_net_pressure import SlimFastNormalizedRCNetPressure
from model_object_size import reachable_size
out=Path('experiments/normalized_net_model_memory_v2_2026-10-04')
if out.exists():raise ValueError('fresh output required')
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
prior=json.loads(Path('experiments/normalized_rc_net_pressure_search_2026-10-04/protocol.json').read_text());inputs=prior['inputs']
protocol={'inputs':inputs,'measurement':'sys.getsizeof, reachable references deduplicated; externally retained RR graph and background prediction excluded, including their objects','scope':'object footprint not allocated/peak/RSS/process memory; native hash backing state partly opaque; no timed benchmark','query_selection':'single highest unique sink count net, tie ascending net ID, perdesign before querying','source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');receipts={}
for design,paths in inputs.items():
 assert all(sha(v['path'])==v['sha256'] for v in paths.values())
 g=read_rr_graph(paths['graph']['path']);background=json.loads(Path(paths['background']['path']).read_text());text=Path(paths['cost_table']['path']).read_text();groups=defaultdict(set);roots={}
 for r in background['connections']:groups[r['net_id']].add(r['sink']);roots[r['net_id']]=r['source']
 net=min(groups,key=lambda n:(-len(groups[n]),n));args=(g,text,g.sha256,background);records={};reference=None
 for name,kind in [('reference',NormalizedRCNetPressure),('fast',FastNormalizedRCNetPressure),('slim',SlimFastNormalizedRCNetPressure)]:
  gc.collect();owner=kind(*args);footprint=reachable_size(owner,(g,background));result,context=owner.query(net,roots[net],groups[net],True)
  canonical={'paths':{str(k):list(v) for k,v in sorted(result.paths.items())},'settled_nodes':result.settled_nodes,'budget_exhausted':result.budget_exhausted,'edge_visits':result.edge_visits,'context':context}
  if reference is None:reference=canonical
  else:assert canonical==reference
  records[name]={'reachable_python_object_bytes_excluding_inputs':footprint,'selected_full_result_and_context_exact':True};del owner;gc.collect()
 assert records['slim']['reachable_python_object_bytes_excluding_inputs']<records['fast']['reachable_python_object_bytes_excluding_inputs']
 receipts[design]={'graph_sha256':g.sha256,'graph_edges':len(g.edges),'selected_net':net,'selected_sinks':len(groups[net]),'selected_query':reference,'models':records,'inputs_unchanged':all(sha(v['path'])==v['sha256'] for v in paths.values())}
 (out/f'{design}_receipt.json').write_text(json.dumps(receipts[design],indent=2)+'\n');print(design+' '+json.dumps(records),flush=True)
(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'designs':receipts},indent=2)+'\n')
