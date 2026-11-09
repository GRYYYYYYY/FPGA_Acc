"""Affected whole-net recomputation vs full fixed-template rebuild."""
import hashlib,json,shutil,time
from pathlib import Path
from connectivity_trial import construct
from rr_graph import read_rr_graph
from rr_batch_occupancy import BatchOccupancy
from connection_golden import Result

out=Path('experiments/moved_net_trial_2026-10-04')
if out.exists():raise ValueError('fresh output required')
out.mkdir(parents=True);(out/'source').mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=Path('experiments/diffeq_placement_swap_2026-10-04');change=json.loads((base/'receipt.json').read_text());ep=json.loads((base/'endpoints.json').read_text());graph=Path(ep['inputs']['graph']['path']);oldpath=Path('experiments/connectivity_trial_2026-10-04/refinement_fixed.json')
names=['moved_net_trial.py','connectivity_trial.py','rr_batch_occupancy.py','rr_graph.py','rr_occupancy.py','connection_golden.py','template_connectivity.py','template_sketch.py','pin_pools.py','pin_template_trial.py','prediction_metrics.py','semantic_sketch.py','run_sketch.py']
for n in names:shutil.copyfile(Path(__file__).with_name(n),out/'source'/n)
proto={'scope':'real two-CLB swap, affected complete nets vs full fixed-template rebuild; no native route/feedback benefit claim','inputs':{k:{'path':str(p.resolve()),'sha256':sha(p)} for k,p in [('graph',graph),('endpoints',base/'endpoints.json'),('change',base/'receipt.json'),('old_paths',oldpath)]},'refinement_rounds':None,'source_sha256':{n:sha(out/'source'/n) for n in names}}
(out/'protocol.json').write_text(json.dumps(proto,indent=2)+'\n')
g=read_rr_graph(graph);old=json.loads(oldpath.read_text());ledger=BatchOccupancy(g)
for row in old['connections']:
    args={k:row[k] for k in ('connection_id','net_id','source','sink')};args['edge_ids']=row['physical_edge_ids']
    assert ledger.update(epoch=1,**args)==Result.COMMITTED
ids=set(change['affected_complete_net_connection_ids']);dirty={**ep,'connections':[r for r in ep['connections'] if r['connection_id'] in ids]}
start=time.monotonic();partial=construct(g,dirty,None);partial_wall=time.monotonic()-start
updates=[]
for row in partial['connections']:
    updates.append({**{k:row[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':row['physical_edge_ids']})
assert ledger.update_batch(updates)==Result.COMMITTED
start=time.monotonic();fresh=construct(g,ep,None);full_wall=time.monotonic()-start
for row in fresh['connections']:
    state=ledger.states[row['connection_id']][1]
    assert state.source==row['source'] and state.sink==row['sink'] and list(state.edge_ids)==list(row['physical_edge_ids'])
assert {str(n):v for n,v in ledger.occupancy.items() if v}==fresh['node_occupancy']
for name,data in [('partial',partial),('fresh',fresh)]:
    (out/f'{name}.json').write_text(json.dumps(data,indent=2)+'\n')
result={'protocol_sha256':sha(out/'protocol.json'),'changed_endpoints':len(change['changed_connection_ids']),'affected_nets':len(change['affected_net_ids']),'recomputed_connections':len(ids),'total_connections':len(ep['connections']),'all_paths_and_net_union_equal_full_rebuild':True,'partial_work':partial['work'],'full_work':fresh['work'],'partial_construct_wall_s':partial_wall,'full_construct_wall_s':full_wall,'limitations':['fixed-point pin-only compression','both paths rebuild quotient/index','ledger copy/full rebuild still required','no native route or end-to-end timing']}
(out/'receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result),flush=True)
