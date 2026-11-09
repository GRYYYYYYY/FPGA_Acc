"""Frozen post-outcome 2x2 tree/budget development ablation, all cases retained."""
import json,sys,time
from pathlib import Path
from collections import defaultdict
R=Path(__file__).resolve().parents[1];sys.path[:0]=[str(R/'tools'),str(R/'tools/native_resume_prototype')]
from pre_route_endpoints import sha
from nonzero_rc_endpoint_context import load_endpoints
from tree_floor_predictor_v1 import predict,grouped_floor
from source_binding_v2 import closure
base=R/'experiments/mcnc_prospective_v1_2026-10-07';out=R/'experiments/mcnc_tree_floor_development_v1_2026-10-07';out.mkdir();inputs={}
for name in ('bigkey','dsip','misex3'):
 ep=base/name/'endpoints.json';inputs[str(ep)]=sha(ep);meta=json.loads(ep.read_text());inputs.update({v['path']:v['sha256'] for v in meta['inputs'].values()})
sources=closure([Path(__file__)]);protocol=dict(inputs=inputs,sources=sources,cases=['bigkey','dsip','misex3'],ablations=[[False,False],[False,True],[True,False],[True,True]],budget='legacy1ns or max(legacy1ns,ceil(3*unrestricted input-only floor/2)) exact lattice',tree='root-only or retained-tree multisource prefix delay; cannot enter retained nodes from a new branch',order='ascending NET/CID, no owner releases',objective='scalar minimum additive buffered RC delay, node-id tie; original weighted-label predictor is a separate archived method',scope='Post-outcome development 2x2 scalar-engine ablation, not original-policy causal replacement or heldout. Context and grouped source floors built once per design with cost separately reported, same floor data shared all four policies; no native labels read by producer, no end-to-end net-gain claim.')
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');rows=[]
for name in protocol['cases']:
 tick=time.perf_counter();graph,digest,nodes,f,rc,queries=load_endpoints(base/name/'endpoints.json');context_s=time.perf_counter()-tick;groups=defaultdict(set)
 for q in queries:groups[q['source']].add(q['sink'])
 tick=time.perf_counter();floors={}
 for source,sinks in groups.items():floors.update({(source,sink):value for sink,value in grouped_floor(f,rc,source,sinks).items()})
 floor_s=time.perf_counter()-tick;(out/(name+'_floors.json')).write_text(json.dumps([dict(source=u,sink=v,minimum_integer=d) for (u,v),d in sorted(floors.items())])+'\n')
 for tree,budget in protocol['ablations']:
  tick=time.perf_counter();r=predict(f,rc,queries,floors,tree=tree,floor_budget=budget);elapsed=time.perf_counter()-tick;r.update(graph_sha256=digest,scale=rc.scale);path=out/f'{name}_tree{int(tree)}_floor{int(budget)}.json';path.write_text(json.dumps(r)+'\n');rows.append(dict(name=name,tree=tree,floor_budget=budget,context_seconds=context_s,grouped_floor_seconds=floor_s,search_seconds=elapsed,candidate_path=str(path),candidate_sha256=sha(path),completed_connections=r['completed_connections'],required_connections=r['required_connections'],failure=r['failure']));(out/'rows.json').write_text(json.dumps(rows,indent=2)+'\n');print(name,tree,budget,r['completed_connections'],r['failure'],flush=True)
assert all(sha(p)==h for p,h in {**inputs,**sources}.items());(out/'receipt.json').write_text(json.dumps(dict(protocol_sha256=sha(out/'protocol.json'),rows=rows),indent=2)+'\n')
