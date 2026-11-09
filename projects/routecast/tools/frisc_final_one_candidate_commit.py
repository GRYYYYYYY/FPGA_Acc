"""Fixed ascending-net policy, atomic whole-net batches and exact global score gate."""
import json,time
from pathlib import Path
from collections import Counter,defaultdict
from pre_route_endpoints import sha
from rr_graph import read_rr_graph
from physical_prediction_audit import audit
from pin_choice_catalog import PinChoiceCatalog
from net_union_commit_gate import check
from net_union_topology import diagnose
from rr_local_batch_occupancy import LocalBatchOccupancy
from connection_golden import Result
from feedback_scores import scores
start=time.monotonic();out=Path('experiments/frisc_final_one_candidate_commit_2026-10-05')
if out.exists():raise ValueError('fresh output required')
candidate=Path('experiments/frisc_final_one_blocked_candidates_2026-10-05');receipt=json.loads((candidate/'receipt.json').read_text());base=next(p for p in receipt['input_sha256'] if 'prediction' in p)
files=[base,str(candidate/'replacements.json'),str(candidate/'receipt.json'),'work/frisc_graph_capture_2026-10-05/rr_graph.xml','experiments/frisc_endpoints_2026-10-05/endpoints.json'];inputs={p:sha(p) for p in files};g=read_rr_graph(files[3]);e=json.loads(Path(files[4]).read_text());bg=json.loads(Path(base).read_text());audit(g,e,bg);catalog=PinChoiceCatalog(g);rows={r['connection_id']:r for r in bg['connections']};replacement=json.loads((candidate/'replacements.json').read_text());groups=defaultdict(list)
for text,row in replacement.items():
 cid=int(text);old=rows[cid];a=catalog.witness(old['source'],old['sink'],old['physical_edge_ids']);b=catalog.witness(row['source'],row['sink'],row['physical_edge_ids']);assert a['selected_opin_ptc']==b['selected_opin_ptc'] and a['selected_ipin_ptc']==b['selected_ipin_ptc'];groups[row['net_id']].append(row)
ledger=LocalBatchOccupancy(g)
for r in rows.values():assert ledger.update(r['connection_id'],1,r['net_id'],r['source'],r['sink'],r['physical_edge_ids'])==Result.COMMITTED
current=bg;initial=scores(g,e,bg['node_occupancy']);now=initial;reports=[]
def key(s):return(s['predicted_channel_overuse_units'],s['channel_net_span_sum'])
for net in sorted(groups):
 staged=sorted(groups[net],key=lambda r:r['connection_id']);gate=check(g,current,staged);report={'net':net,'connection_ids':[r['connection_id'] for r in staged],'tree_accepted':gate['accepted'],'before_scores':now,'committed':False}
 if gate['accepted']:
  branch=ledger.fork();updates=[{**{k:r[k] for k in ('connection_id','net_id','source','sink')},'epoch':2,'edge_ids':r['physical_edge_ids']} for r in staged];assert branch.update_batch(updates)==Result.COMMITTED
  after=scores(g,e,{str(n):v for n,v in branch.occupancy.items() if v});report['candidate_scores']=after
  if key(after)<key(now):
   rows.update({r['connection_id']:r for r in staged});ledger=branch;now=after;report['committed']=True
   current={'physical_graph_sha256':g.sha256,'connections':list(rows.values()),'node_occupancy':{str(n):v for n,v in ledger.occupancy.items() if v},'methods':dict(Counter(r['method'] for r in rows.values())),'requested':len(rows),'completed':len(rows)}
 else:report['rejected_nets']=gate['rejected_nets']
 reports.append(report)
checked=audit(g,e,current);topology=diagnose(g,current);assert all(not r['internal_multi_incoming_nodes'] and not r['cyclic_union'] and not r['source_has_incoming'] and r['all_nodes_source_reachable'] for r in topology['nets'])
assert all(sha(p)==h for p,h in inputs.items());out.mkdir();(out/'prediction.json').write_text(json.dumps(current)+'\n');(out/'source.py').write_text(Path(__file__).read_text());r={'baseline_scores':initial,'final_scores':now,'reports':reports,'physical_audit':checked,'final_topology':topology,'input_sha256':inputs,'source_sha256':sha(out/'source.py'),'prediction_sha256':sha(out/'prediction.json'),'full_wall_s':time.monotonic()-start,'policy':'ascending net ID; all generated replacements of each net in one atomic batch; whole-net structural gate; strictly lower lexicographic (exact global channel overuse, channel span); otherwise retain current state','scope':'development instance, frozen candidates; remaining channel conflicts or native timing not implied solved'};(out/'receipt.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'baseline':initial,'final':now,'committed_nets':sum(r['committed'] for r in reports),'tree_rejected_nets':sum(not r['tree_accepted'] for r in reports),'full_wall_s':r['full_wall_s']}))
