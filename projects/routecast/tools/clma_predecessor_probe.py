"""Fixed first100 real clma nets: predecessor/indexed heap semantic probe."""
import json,time,shutil
from pathlib import Path
from types import SimpleNamespace
from prepared_csr import read,sha,U64
from predecessor_search import PredecessorSearch
out=Path('experiments/clma_predecessor_probe_2026-10-04')
if out.exists():raise ValueError('fresh output required')
refpath=Path('experiments/clma_full_goal_astar_2026-10-04/prediction.json');assert sha(refpath)=='e162fd20f6cd70bb2b713c57d5b607569c3d7889b596012aafa355c8958de68a'
ref=json.loads(refpath.read_text());m,f=read('experiments/clma_prepared_csr_2026-10-04/csr',ref['physical_graph_sha256'],'6b51650f3ac0ba59b39ee3b556cfa201c336691a0a88721ac21437ea0ecd36f6');ranks={n:i for i,n in enumerate(f['node_ids'])}
class Arcs:
 def __getitem__(self,node):
  rank=ranks[node]
  return ((f['edge_ids'][i],f['node_ids'][f['dest_ranks'][i]],None if f['costs'][i]==U64 else f['costs'][i]) for i in range(f['row_offsets'][rank],f['row_offsets'][rank+1]))
names=('SOURCE','SINK','OPIN','IPIN','CHANX','CHANY');nodes={n:SimpleNamespace(type=names[f['types'][r]],capacity=f['capacities'][r]) for n,r in ranks.items()};engine=PredecessorSearch(SimpleNamespace(graph=SimpleNamespace(nodes=nodes),node_budget=len(nodes),outgoing=Arcs()));groups={}
for c in ref['connections']:groups.setdefault(c['net_id'],[]).append(c)
out.mkdir();shutil.copyfile('tools/predecessor_search.py',out/'predecessor_search.py');shutil.copyfile(__file__,out/'driver.py');start=time.monotonic();results=[];count=0
for net in sorted(groups)[:100]:
 cs=groups[net];result=engine.search(cs[0]['source'],{c['sink'] for c in cs})
 for c in cs:assert list(result.paths[c['sink']])==c['physical_edge_ids'];count+=1
 results.append({'net_id':net,'settled':result.settled_nodes,'edge_visits':result.edge_visits,'peak_frontier':engine.last_peak_frontier})
(out/'results.json').write_text(json.dumps(results)+'\n');receipt={'nets':100,'connections':count,'canonical_paths_exact':True,'elapsed_s':time.monotonic()-start,'max_peak_frontier':max(x['peak_frontier'] for x in results),'sha256':{p.name:sha(p) for p in out.iterdir()},'graph_sha256':ref['physical_graph_sha256'],'context_sha256':m['context_sha256'],'reference_sha256':sha(refpath)};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
