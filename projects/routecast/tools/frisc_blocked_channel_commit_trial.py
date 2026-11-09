import json,time
from pathlib import Path
from collections import Counter
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from pin_choice_catalog import PinChoiceCatalog
from net_union_commit_gate import check
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from physical_prediction_audit import audit
from feedback_scores import scores
out=Path('experiments/frisc_blocked_channel_commit_2026-10-05')
if out.exists():raise ValueError('fresh output required')
files={'graph':'work/frisc_graph_capture_2026-10-05/rr_graph.xml','prediction':'experiments/frisc_sequential_pin_compatible_round4_2026-10-05/prediction.json','candidates':'experiments/frisc_blocked_channel_candidates_2026-10-05/paths.json','endpoints':'experiments/frisc_endpoints_2026-10-05/endpoints.json'}
inputs={p:sha(p) for p in files.values()};start=time.monotonic();g=read_rr_graph(files['graph']);catalog=PinChoiceCatalog(g);bg=json.loads(Path(files['prediction']).read_text());e=json.loads(Path(files['endpoints']).read_text());audit(g,e,bg);candidates=json.loads(Path(files['candidates']).read_text());rows={r['connection_id']:r for r in bg['connections']};ledger=LocalBatchOccupancy(g)
for r in rows.values():assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
replacements={}
for cid,result in candidates.items():
 old=rows[int(cid)];w=catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);path=result['paths'][str(w['selected_ipin_ptc'])];new=catalog.witness(old['source'],old['sink'],path);assert new['selected_ipin_ptc']==w['selected_ipin_ptc'] and new['selected_opin_ptc']==w['selected_opin_ptc'];assert all(g.edges[eid].sink!=31148 for eid in path);replacements[int(cid)]={**old,'physical_edge_ids':path,'method':'blocked_channel_repair'}
out.mkdir();reports=[]
for ids in ([3097],[4884],[3097,4884]):
 staged=[replacements[c] for c in ids];gate=check(g,bg,staged);report={'connection_ids':ids,'gate':gate}
 if gate['accepted']:
  branch=ledger.fork();updates=[{**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':r['physical_edge_ids']} for r in staged];assert branch.update_batch(updates)==Result.COMMITTED
  newrows=[replacements[r['connection_id']] if r['connection_id'] in ids else r for r in bg['connections']];pred={'physical_graph_sha256':g.sha256,'connections':newrows,'node_occupancy':{str(n):v for n,v in branch.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in newrows)),'requested':len(newrows),'completed':len(newrows)};checked=audit(g,e,pred);report.update(scores=scores(g,e,pred['node_occupancy']),physical_audit=checked,blocked_channel_demand=pred['node_occupancy'].get('31148',0));file=out/('prediction_'+ '_'.join(map(str,ids))+'.json');file.write_text(json.dumps(pred)+'\n');report['prediction_sha256']=sha(file)
 reports.append(report)
assert all(sha(p)==h for p,h in inputs.items());(out/'source.py').write_text(Path(__file__).read_text());receipt={'baseline_scores':scores(g,e,bg['node_occupancy']),'reports':reports,'full_wall_s':time.monotonic()-start,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'scope':'isolated alternatives using unchanged physical input/output pins, full affected-net gate and atomic forked ledger; no native route or timing guarantee'};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps([{'ids':r['connection_ids'],'accepted':r['gate']['accepted'],'scores':r.get('scores'),'demand':r.get('blocked_channel_demand')} for r in reports]))
