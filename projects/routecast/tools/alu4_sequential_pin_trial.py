"""Development fixed ascending class sweep, current-background candidate repricing."""
import argparse,json,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from physical_prediction_audit import audit
from net_pressure_sketch import net_union
from costed_pin_assignment import assign_costed
from pin_assignment_optimality import verify
from feedback_scores import scores
from net_union_topology import diagnose
parser=argparse.ArgumentParser();parser.add_argument('--output',type=Path,default=Path('experiments/alu4_sequential_pin_trial_2026-10-05'));parser.add_argument('--order',choices=('ascending','descending'),default='ascending');parser.add_argument('--background',default='experiments/alu4_transfer_2026-10-05/prediction.json');parser.add_argument('--compatible-candidates',action='store_true');parser.add_argument('--tree-gate',action='store_true');args=parser.parse_args();out=args.output
if out.exists():raise ValueError('fresh output required')
files={'background':args.background,'paths':'experiments/alu4_full_weighted_pin_trial_2026-10-05/paths.json','inventory':'experiments/alu4_pin_conflict_inventory_2026-10-05/receipt.json','endpoints':'experiments/alu4_validation_capture_2026-10-05/endpoints.json','graph':'work/alu4_validation_capture_2026-10-05/rr_graph.xml'}
inputs={p:sha(p) for p in files.values()};start=time.monotonic();g=read_rr_graph(files['graph']);bg=json.loads(Path(files['background']).read_text());e=json.loads(Path(files['endpoints']).read_text());audit(g,e,bg);paths=json.loads(Path(files['paths']).read_text());inventory=json.loads(Path(files['inventory']).read_text());rows={r['connection_id']:r for r in bg['connections']};ledger=LocalBatchOccupancy(g)
for r in rows.values():assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
def export():
 return {'physical_graph_sha256':g.sha256,'connections':list(rows.values()),'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in rows.values())),'requested':len(rows),'completed':len(rows)}
base={}
for n,node in g.nodes.items():
 if node.type in {'CHANX','CHANY'}:
  loc=dict(node.location);base[n]=max(int(loc['xhigh'])-int(loc['xlow']),int(loc['yhigh'])-int(loc['ylow']))+1
out.mkdir();(out/'protocol.json').write_text(json.dumps({'input_sha256':inputs,'class_order':args.order,'compatible_candidates':args.compatible_candidates,'tree_gate':args.tree_gate,'alpha':256,'source_sha256':sha(__file__),'scope':'existing candidate library repriced against current external demand per class; no native labels'},indent=2)+'\n');(out/'source.py').write_text(Path(__file__).read_text());reports=[];all_chosen={};sweep=time.monotonic()
for cls in sorted(inventory['classes'],key=lambda c:c['sink_class'],reverse=args.order=='descending'):
 t=time.monotonic();current=export();users,demand=net_union(g,current);sink=cls['sink_class'];costs={};filtered=0
 net_rows={}
 for r in current['connections']:net_rows.setdefault(r['net_id'],[]).append(r)
 for cid in cls['request_ids']:
  net=rows[cid]['net_id'];own=users[net];options={}
  for ptc,path in paths[str(cid)]['paths'].items():
   if args.compatible_candidates:
    from net_union_commit_gate import check
    candidate={**rows[cid],'physical_edge_ids':path}
    if not check(g,{'physical_graph_sha256':g.sha256,'connections':net_rows[net]},[candidate])['accepted']:
     filtered+=1;continue
   value=0
   for eid in path:
    n=g.edges[eid].sink
    if n in base:
     c=g.nodes[n].capacity;assert c>0;d=demand.get(n,0)-int(n in own);value+=base[n]+(256*max(0,d-c+1)+c-1)//c
   options[sink,int(ptc)]=value
  costs[cid]=options
 matched=assign_costed(costs)
 if matched['status']!='matched':
  assert export()==current;assert all(sha(p)==h for p,h in inputs.items())
  (out/'rejection.json').write_text(json.dumps({'status':'compatible_candidate_assignment_infeasible','sink_class':sink,'completed_classes':len(reports),'filtered_candidates':filtered,'matching':matched,'batch_state_unchanged':True,'input_sha256':inputs,'driver_sha256':sha(__file__),'scope':'conservative compatibility with current retained paths and supplied candidates only; not proof no RR solution exists'},indent=2)+'\n');raise SystemExit(3)
 assert verify(costs,matched['assignment'])['optimal'];updates=[];staged={}
 for cid,pin in matched['assignment'].items():
  r=rows[cid];path=paths[str(cid)]['paths'][str(pin[1])];updates.append({**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':path});staged[cid]={**r,'physical_edge_ids':path,'method':'sequential_class_pin'}
 if args.tree_gate:
  from net_union_commit_gate import check
  gate=check(g,current,list(staged.values()))
  if not gate['accepted']:
   assert export()==current
   checked=audit(g,e,current);assert all(sha(p)==h for p,h in inputs.items())
   (out/'rejection.json').write_text(json.dumps({'status':'rejected_before_publication','sink_class':sink,'completed_classes':len(reports),'attempted_requests':len(updates),'gate':gate,'batch_state_unchanged':True,'physical_audit':checked,'input_sha256':inputs,'driver_sha256':sha(__file__),'gate_sha256':sha('tools/net_union_commit_gate.py'),'limitations':'prior classes committed to private experiment state; full repair not completed'},indent=2)+'\n')
   print(json.dumps({'rejected_class':sink,'completed_classes':len(reports),'rejected_nets':[r['net_id'] for r in gate['rejected_nets']]}),flush=True)
   raise SystemExit(2)
 assert ledger.update_batch(updates)==Result.COMMITTED;rows.update(staged);all_chosen.update(matched['assignment']);reports.append({'sink_class':sink,'requests':len(updates),'repriced_optimal_cost':matched['total_cost'],'wall_s':time.monotonic()-t})
 if len(reports)%25==0:print(json.dumps({'classes_completed':len(reports),'classes_total':len(inventory['classes'])}),flush=True)
sweep_s=time.monotonic()-sweep;pred=export();checked=audit(g,e,pred);assert len({tuple(p) for p in all_chosen.values()})==len(all_chosen)
selected={cid for c in inventory['classes'] for cid in c['request_ids']};assert set(all_chosen)==selected
old={r['connection_id']:r for r in bg['connections']};assert all(rows[cid]==old[cid] for cid in rows if cid not in selected)
assert all(sha(p)==h for p,h in inputs.items());(out/'prediction.json').write_text(json.dumps(pred)+'\n');(out/'assignment.json').write_text(json.dumps(all_chosen)+'\n');(out/'source.py').write_text(Path(__file__).read_text());receipt={'compatible_candidates':args.compatible_candidates,'tree_gate':args.tree_gate,'class_order':args.order,'classes':reports,'updated_requests':len(selected),'sweep_s':sweep_s,'full_wall_s':time.monotonic()-start,'scores_before':scores(g,e,bg['node_occupancy']),'scores_after':scores(g,e,pred['node_occupancy']),'topology_after':diagnose(g,pred),'physical_audit':checked,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'prediction_sha256':sha(out/'prediction.json'),'scope':'one fixed ascending-class sweep over old weighted candidates with current demand repricing; no new shortest search, native QoR or convergence proof'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps({k:receipt[k] for k in ('updated_requests','sweep_s','full_wall_s','scores_before','scores_after')}),flush=True)
