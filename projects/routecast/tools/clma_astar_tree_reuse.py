"""All87 preselected high-fanout nets, fixed blend costs/ascending sink order."""
import json,time,shutil,os
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from normalized_rc_base import NormalizedRCBaseSketch
from path_rc import PathRC,State
from tree_reuse import TreeReuse
from astar_tree_reuse import AStarTreeReuse
from physical_prediction_audit import audit
from rr_occupancy import Occupancy
from connection_golden import Result
out=Path('experiments/clma_astar_tree_reuse_2026-10-04')
if out.exists():raise ValueError('fresh output required')
prior=json.loads(Path('experiments/clma_normalized_transfer_2026-10-04/protocol.json').read_text());inputs=prior['inputs'];control=Path('experiments/clma_normalized_transfer_2026-10-04/blend_prediction.json');inputs={**inputs,'control':{'path':str(control.resolve()),'sha256':sha(control)}}
e=json.loads(Path(inputs['endpoints']['path']).read_text());groups=defaultdict(list)
for row in e['connections']:groups[row['net_id']].append(row)
selected={n:rows for n,rows in groups.items() if len(rows)>=17};assert len(selected)==87
pilot={**e,'connections':[r for n,rows in sorted(selected.items()) for r in rows]}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
protocol={'probe':'largest endpoint fanout, tie ascending net ID; reference then Astar','expand_gate':'exact probe paths/parents/failures and fewer edge visits; if not, do not launch full replay','inputs':inputs,'scope':'fixed previously selected clma fanout17+ cohort, no route/timing labels in predictor; not unseen-family/native router equivalence','selected_nets':sorted(selected),'requested':len(pilot['connections']),'sink_order':'ascending physical SINK ID','weights':'same normalized half RC+base, scale1e6, no pressure change','tree_prefix':'round accumulated exact halfRC/norm*scale; existing base costs reused, new arcs frozen rounded blend weight','branch_policy':'no reentry into committed tree, unique parents, failure preserves committed branches','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps({'pid':os.getpid(),'stage':'prepare','nets':87,'connections':len(pilot['connections'])}),flush=True);start=time.monotonic();g=read_rr_graph(inputs['graph']['path']);base=NormalizedRCBaseSketch(g,Path(inputs['cost_table']['path']).read_text(),g.sha256);rc=PathRC(g)
weights=[None]*len(g.edges)
for arcs in base.outgoing.values():
 for eid,dst,w in arcs:weights[eid]=w
timing=[rc.step(State(Fraction(0),Fraction(0)),eid).delay/base.normalization*base.scale/2 for eid in range(len(g.edges))]
model=AStarTreeReuse(g,weights,timing);prep=time.monotonic()-start
probe_net=min(selected,key=lambda n:(-len(selected[n]),n));probe_rows=selected[probe_net];probe_source=probe_rows[0]['source'];probe_targets={r['sink'] for r in probe_rows}
reference=TreeReuse(g,weights,timing);probe_start=time.monotonic();ref_result=reference.route(probe_source,probe_targets);ref_s=time.monotonic()-probe_start;probe_start=time.monotonic();fast_result=model.route(probe_source,probe_targets);fast_s=time.monotonic()-probe_start
assert (ref_result.paths,ref_result.parents,ref_result.failures)==(fast_result.paths,fast_result.parents,fast_result.failures)
probe={'net_id':probe_net,'connections':len(probe_rows),'alpha':model.alpha,'reference_s':ref_s,'astar_s':fast_s,'reference_edge_visits':ref_result.edge_visits,'astar_edge_visits':fast_result.edge_visits,'exact_result':True,'expand':fast_result.edge_visits<ref_result.edge_visits};(out/'probe.json').write_text(json.dumps(probe,indent=2)+'\n');print(json.dumps(probe),flush=True);del reference
if not probe['expand']:
 (out/'termination.json').write_text(json.dumps({'reason':'pre-frozen edgework gate not met','probe_sha256':sha(out/'probe.json')},indent=2)+'\n');raise SystemExit(0)
ledger=Occupancy(g);rows=[];trees={};visits=0;settled=0;start=time.monotonic()
for i,(net,cohort) in enumerate(sorted(selected.items()),1):
 sources={r['source'] for r in cohort};assert len(sources)==1;source=next(iter(sources));result=model.route(source,{r['sink'] for r in cohort});assert not result.failures
 visits+=result.edge_visits;settled+=result.settled_nodes;trees[str(net)]={'parents':result.parents,'sink_order':sorted(result.paths)}
 # Verify unique raw parent for each node on every complete source-rooted path.
 for row in cohort:
  path=result.paths[row['sink']];node=source;seen={source}
  for eid in path:
   edge=g.edges[eid];assert edge.source==node and edge.sink not in seen and result.parents[edge.sink]==eid;node=edge.sink;seen.add(node)
  assert node==row['sink'];assert ledger.update(row['connection_id'],1,net,source,node,path)==Result.COMMITTED
  rows.append({**row,'physical_edge_ids':path,'method':'tree_reuse'})
 if i%10==0:print(json.dumps({'stage':'search','completed_nets':i,'connections':len(rows),'elapsed_s':time.monotonic()-start}),flush=True)
query_s=time.monotonic()-start;pred={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'requested':len(rows),'completed':len(rows),'methods':{'tree_reuse':len(rows)}};checked=audit(g,pilot,pred)
gold=Path('experiments/clma_tree_reuse_pilot_2026-10-04');gold_receipt=json.loads((gold/'receipt.json').read_text());gold_prediction=json.loads((gold/'prediction.json').read_text());gold_trees=json.loads((gold/'tree_parents.json').read_text())
assert gold_receipt['outputs']['prediction.json']==sha(gold/'prediction.json') and gold_receipt['outputs']['tree_parents.json']==sha(gold/'tree_parents.json')
assert json.loads(json.dumps(pred))==gold_prediction and json.loads(json.dumps(trees))==gold_trees
old=json.loads(control.read_text());old_rows=[r for r in old['connections'] if r['net_id'] in selected];old_ledger=Occupancy(g)
for r in old_rows:assert old_ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
control_pred={'physical_graph_sha256':g.sha256,'connections':old_rows,'node_occupancy':{str(n):v for n,v in old_ledger.occupancy.items() if v},'requested':len(old_rows),'completed':len(old_rows),'methods':{'blend':len(old_rows)}};control_audit=audit(g,pilot,control_pred)
for name,data in [('prediction.json',pred),('control_prediction.json',control_pred),('tree_parents.json',trees),('endpoints.json',pilot)]: (out/name).write_text(json.dumps(data)+'\n')
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());receipt={'protocol_sha256':sha(out/'protocol.json'),'preparation_s':prep,'query_ledger_s':query_s,'alpha':model.alpha,'exact_prior_prediction_and_parents':True,'probe_sha256':sha(out/'probe.json'),'edge_visits':visits,'settled_nodes':settled,'audit':checked,'control_audit':control_audit,'unique_parent_and_acyclic_checks':True,'inputs_unchanged':True,'outputs':{n:sha(out/n) for n in ('prediction.json','control_prediction.json','tree_parents.json','endpoints.json')}};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
