"""Frozen own-net excluded cross-net pressure, same fixed87 tree cohort."""
import json,time,shutil,os
from pathlib import Path
from collections import defaultdict
from fractions import Fraction
from rr_graph import read_rr_graph
from pre_route_endpoints import sha
from normalized_rc_base import NormalizedRCBaseSketch
from path_rc import PathRC,State
from tree_reuse import TreeReuse
from frozen_tree_pressure import FrozenTreePressure
from physical_prediction_audit import audit
from rr_occupancy import Occupancy
from connection_golden import Result
out=Path('experiments/clma_frozen_tree_pressure_2026-10-04')
if out.exists():raise ValueError('fresh output required')
prior=json.loads(Path('experiments/clma_normalized_transfer_2026-10-04/protocol.json').read_text());inputs=prior['inputs'];control=Path('experiments/clma_normalized_transfer_2026-10-04/blend_prediction.json');inputs={**inputs,'control':{'path':str(control.resolve()),'sha256':sha(control)}}
e=json.loads(Path(inputs['endpoints']['path']).read_text());groups=defaultdict(list)
for row in e['connections']:groups[row['net_id']].append(row)
selected={n:rows for n,rows in groups.items() if len(rows)>=17};assert len(selected)==87
pilot={**e,'connections':[r for n,rows in sorted(selected.items()) for r in rows]}
assert all(sha(v['path'])==v['sha256'] for v in inputs.values())
out.mkdir();(out/'source').mkdir()
for f in Path(__file__).parent.glob('*.py'):shutil.copyfile(f,out/'source'/f.name)
background=Path('experiments/clma_tree_pilot_composition_2026-10-04/prediction.json');background_receipt=json.loads((background.parent/'receipt.json').read_text());assert background_receipt['prediction_sha256']==sha(background)
inputs['background']={'path':str(background.resolve()),'sha256':sha(background)}
tree_control=Path('experiments/clma_tree_reuse_pilot_2026-10-04/prediction.json');tree_receipt=json.loads((tree_control.parent/'receipt.json').read_text());assert tree_receipt['outputs']['prediction.json']==sha(tree_control)
inputs['tree_control']={'path':str(tree_control.resolve()),'sha256':sha(tree_control)}
protocol={'inputs':inputs,'scope':'fixed previously selected clma87 fanout17+ cohort; background from full retrospective tree87+blendothers prediction, no native route labels used in predictor','selected_nets':sorted(selected),'requested':len(pilot['connections']),'sink_order':'ascending physical SINK ID','weights':'same normalized half RC+base, scale1e6','pressure':'single frozen factor1 half normalized base times max0(demand excluding own unique net union-capacity+1), channel destinations only','tree_prefix':'same rounded accumulated exact halfRC, existing base/pressure costs reused; new arcs pay fixed blend plus destination pressure','background':'immutable full design snapshot; no moving demand, history, iteration or best-round selection','all_results_gate':'full5734 physical/netunion/uniqueparent/acyclic checks; report all preset metrics regardless of sign','source_sha256':{f.name:sha(f) for f in (out/'source').glob('*.py')}}
(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');print(json.dumps({'pid':os.getpid(),'stage':'prepare','nets':87,'connections':len(pilot['connections'])}),flush=True);start=time.monotonic();g=read_rr_graph(inputs['graph']['path']);model=FrozenTreePressure(g,Path(inputs['cost_table']['path']).read_text(),g.sha256,json.loads(background.read_text()));prep=time.monotonic()-start
contexts={}
ledger=Occupancy(g);rows=[];trees={};visits=0;settled=0;start=time.monotonic()
for i,(net,cohort) in enumerate(sorted(selected.items()),1):
 sources={r['source'] for r in cohort};assert len(sources)==1;source=next(iter(sources));result,context=model.route(net,source,{r['sink'] for r in cohort});contexts[str(net)]=context;assert not result.failures
 visits+=result.edge_visits;settled+=result.settled_nodes;trees[str(net)]={'parents':result.parents,'sink_order':sorted(result.paths)}
 # Verify unique raw parent for each node on every complete source-rooted path.
 for row in cohort:
  path=result.paths[row['sink']];node=source;seen={source}
  for eid in path:
   edge=g.edges[eid];assert edge.source==node and edge.sink not in seen and result.parents[edge.sink]==eid;node=edge.sink;seen.add(node)
  assert node==row['sink'];assert ledger.update(row['connection_id'],1,net,source,node,path)==Result.COMMITTED
  rows.append({**row,'physical_edge_ids':path,'method':'tree_pressure'})
 if i%10==0:print(json.dumps({'stage':'search','completed_nets':i,'connections':len(rows),'elapsed_s':time.monotonic()-start}),flush=True)
query_s=time.monotonic()-start;pred={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'requested':len(rows),'completed':len(rows),'methods':{'tree_pressure':len(rows)}};checked=audit(g,pilot,pred)
old=json.loads(tree_control.read_text());old_rows=[r for r in old['connections'] if r['net_id'] in selected];old_ledger=Occupancy(g)
for r in old_rows:assert old_ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
control_pred={'physical_graph_sha256':g.sha256,'connections':old_rows,'node_occupancy':{str(n):v for n,v in old_ledger.occupancy.items() if v},'requested':len(old_rows),'completed':len(old_rows),'methods':{'tree_reuse':len(old_rows)}};control_audit=audit(g,pilot,control_pred)
for name,data in [('prediction.json',pred),('control_prediction.json',control_pred),('tree_parents.json',trees),('endpoints.json',pilot),('contexts.json',contexts)]: (out/name).write_text(json.dumps(data)+'\n')
assert all(sha(v['path'])==v['sha256'] for v in inputs.values());receipt={'protocol_sha256':sha(out/'protocol.json'),'preparation_s':prep,'query_ledger_s':query_s,'alpha':model.engine.alpha,'background_nets':len(model.users),'frozen_ownnet_exclusion':True,'edge_visits':visits,'settled_nodes':settled,'audit':checked,'control_audit':control_audit,'unique_parent_and_acyclic_checks':True,'inputs_unchanged':True,'outputs':{n:sha(out/n) for n in ('prediction.json','control_prediction.json','tree_parents.json','endpoints.json','contexts.json')}};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
