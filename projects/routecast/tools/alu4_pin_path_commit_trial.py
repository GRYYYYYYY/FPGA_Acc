"""Atomic integration of one equivalence-verified class's matched witnesses."""
import argparse,json,time
from collections import Counter,defaultdict
from pathlib import Path
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from physical_prediction_audit import audit
from feedback_scores import scores
from pin_choice_catalog import PinChoiceCatalog
parser=argparse.ArgumentParser()
parser.add_argument('--output',type=Path,default=Path('experiments/alu4_pin_path_commit_2026-10-05'))
parser.add_argument('--assignment',default='experiments/alu4_reachable_pin_trial_2026-10-05/assignment.json')
parser.add_argument('--equivalence',default='experiments/alu4_full_pin_equivalence_audit_2026-10-05/receipt.json')
parser.add_argument('--paths',default='experiments/alu4_reachable_pin_trial_2026-10-05/paths.json')
args=parser.parse_args()
out=args.output
if out.exists():raise ValueError('fresh output required')
files={'endpoints':'experiments/alu4_validation_capture_2026-10-05/endpoints.json','background':'experiments/alu4_transfer_2026-10-05/prediction.json','paths':args.paths,'assignment':args.assignment,'equivalence':args.equivalence}
inputs={p:sha(p) for p in files.values()};data={k:json.loads(Path(p).read_text()) for k,p in files.items()};e=data['endpoints'];graphfile=e['inputs']['graph']['path'];inputs[graphfile]=e['inputs']['graph']['sha256'];assert all(sha(p)==h for p,h in inputs.items())
start=time.monotonic();g=read_rr_graph(graphfile);bg=data['background'];audit(g,e,bg);catalog=PinChoiceCatalog(g);ledger=LocalBatchOccupancy(g)
t=time.monotonic()
for r in bg['connections']:assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
initialization_s=time.monotonic()-t
assignment=data['assignment'];assert assignment['status']=='matched';chosen=assignment['assignment']
from pin_commit_validation import validate
validate(chosen,data['paths'],data['equivalence']['checks'],e['connections'])
updates=[];rows=[]
for r in bg['connections']:
 cid=str(r['connection_id'])
 if cid not in chosen:rows.append(r);continue
 sink,ptc=chosen[cid];assert sink==r['sink'];path=data['paths'][cid]['paths'][str(ptc)]
 witness=catalog.witness(r['source'],r['sink'],path);assert witness['selected_ipin_ptc']==ptc
 rows.append({**r,'physical_edge_ids':path,'method':'matched_reachable_pin'})
 updates.append({**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':path})
t=time.monotonic();assert ledger.update_batch(updates)==Result.COMMITTED;commit_s=time.monotonic()-t
pred={'physical_graph_sha256':g.sha256,'connections':rows,'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in rows)),'requested':len(rows),'completed':len(rows)}
t=time.monotonic();checked=audit(g,e,pred);audit_s=time.monotonic()-t
old={r['connection_id']:r for r in bg['connections']};assert all(r==old[r['connection_id']] for r in rows if str(r['connection_id']) not in chosen)
def pin_conflicts(prediction):
 users=defaultdict(set)
 for r in prediction['connections']:
  w=catalog.witness(r['source'],r['sink'],r['physical_edge_ids']);users[w['sink_class'],w['selected_ipin_ptc']].add(r['net_id'])
 return {'global_overloaded_physical_pins':sum(len(v)>1 for v in users.values()),'global_overuse_unique_net_units':sum(max(0,len(v)-1) for v in users.values()),'target_class_overloaded_pins':sum(len(v)>1 for (sink,_),v in users.items() if sink==7653),'target_class_overuse_units':sum(max(0,len(v)-1) for (sink,_),v in users.items() if sink==7653)}
from net_union_topology import diagnose
topology={name:diagnose(g,p) for name,p in [('before',bg),('after',pred)]}
metrics={name:{'scores':scores(g,e,p['node_occupancy']),'pin_conflicts':pin_conflicts(p)} for name,p in [('before',bg),('after',pred)]}
assert metrics['after']['pin_conflicts']['target_class_overuse_units']==0
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'prediction.json').write_text(json.dumps(pred)+'\n');(out/'source').mkdir()
for name in ('alu4_pin_path_commit_trial.py','rr_local_batch_occupancy.py','rr_occupancy_golden.py','physical_prediction_audit.py','feedback_scores.py','pin_choice_catalog.py','pin_pools.py','net_union_topology.py','rr_occupancy.py','connection_golden.py','pin_commit_validation.py'):
 p=Path('tools',name)
 if p.exists():(out/'source'/name).write_text(p.read_text())
receipt={'updated_requests':len(updates),'retained_requests':len(rows)-len(updates),'initialization_s':initialization_s,'commit_s':commit_s,'independent_audit_s':audit_s,'full_wall_s':time.monotonic()-start,'metrics':metrics,'net_union_topology':topology,'physical_audit':checked,'input_sha256':inputs,'source_sha256':{p.name:sha(p) for p in (out/'source').glob('*.py')},'prediction_sha256':sha(out/'prediction.json'),'scope':'explicit matched class set pin repair in full software prediction; does not enforce channel feasibility, joint tree legality, native packed remap or timing'}
(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
