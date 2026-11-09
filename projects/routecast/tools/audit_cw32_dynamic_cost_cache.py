"""Cost-read footprints for fixed topology/RC budget snapshots, not placement moves."""
import json,time,shutil
from pathlib import Path
from fractions import Fraction
from collections import defaultdict,Counter
from prepared_csr import read,U64
from pre_route_endpoints import sha
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from integer_rc_context import IntegerRC
from csr_integer_budget_search import query

def main():
 root=Path(__file__).resolve().parents[1];out=root/'experiments/multiplier_cw32_dynamic_cost_cache_2026-10-06';out.mkdir();(out/'sources').mkdir()
 for n in ('audit_cw32_dynamic_cost_cache.py','csr_integer_budget_search.py','integer_rc_context.py','csr_exact_buffered_rc.py','prepared_csr.py','pre_route_endpoints.py','buffered_rc_context.py','buffered_rc_node_classes.py'):shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'sources':{p.name:sha(p) for p in (out/'sources').iterdir()},'policy':'fixed graph, eligibility and RC budgets; query objective scalar*(1+otherNET demand); cache FOUND only; invalidate if any cost-read node demand changes; LABEL_LIMIT/UNREACHABLE recompute','scope':'Two actual initial/final predictor occupancy snapshots. No placement change or sequential incremental workload; cost footprint is more conservative than final path dependency. Full independent query replay verifies cache parity.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[]
 for name in protocol['cohort']:
  start=time.monotonic();dest=out/name;dest.mkdir();baseline=root/'experiments/multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';br=json.loads((baseline/'receipt.json').read_text());assert sha(baseline/'prediction.json')==br['prediction_sha256'];old=json.loads((baseline/'prediction.json').read_text());newroot=root/'experiments/multiplier_cw32_rc_budgeted_nets_2026-10-06'/name;nr=json.loads((newroot/'receipt.json').read_text());assert sha(newroot/'prediction.json')==nr['prediction_sha256'];new=json.loads((newroot/'prediction.json').read_text());assert old['physical_graph_sha256']==new['physical_graph_sha256'];m,f=read(root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',old['physical_graph_sha256']);context=root/'experiments/multiplier_cw32_exact_buffered_rc_classes_2026-10-06'/name;rc=IntegerRC(ExactBufferedRC(f,*load(context,old['physical_graph_sha256'])));budgets={r['connection_id']:rc.encode(Fraction(*r['exact_delay_s'])) for r in json.loads((context/'baseline_budgets.json').read_text())};edge={f['edge_ids'][i]:(u,f['dest_ranks'][i]) for u in range(m['nodes']) for i in range(f['row_offsets'][u],f['row_offsets'][u+1])}
  def state(pred):
   unions=defaultdict(set)
   for r in pred['connections']:
    unions[r['net_id']].add(r['source'])
    for eid in r['physical_edge_ids']:unions[r['net_id']].update(edge[eid])
   demand=Counter(n for nodes in unions.values() for n in nodes);assert +demand==Counter({int(k):v for k,v in pred['node_occupancy'].items()});return unions,demand
  oldu,oldo=state(old);newu,newo=state(new);retained=recomputed=changed_results=path_only_misses=0;records=[]
  for r in old['connections']:
   net=r['net_id'];a=oldo.copy();a.subtract(oldu[net]);b=newo.copy();b.subtract(newu[net]);dirty={n for n in set(a)|set(b) if a[n]!=b[n]};footprint=set();allowed=lambda u,i:f['costs'][i]!=U64 and f['capacities'][f['dest_ranks'][i]]>0
   def objective(u,i):
    n=f['dest_ranks'][i];footprint.add(n);return int(f['costs'][i])*(1+a[n])
   previous=query(rc,r['source'],r['sink'],budgets[r['connection_id']],allowed,objective,10000);affected=previous['status']!='FOUND' or bool(dirty&footprint)
   full=query(rc,r['source'],r['sink'],budgets[r['connection_id']],allowed,lambda u,i:int(f['costs'][i])*(1+b[f['dest_ranks'][i]]),10000)
   if affected:
    incremental=query(rc,r['source'],r['sink'],budgets[r['connection_id']],allowed,lambda u,i:int(f['costs'][i])*(1+b[f['dest_ranks'][i]]),10000);recomputed+=1
   else:incremental=previous;retained+=1
   assert all(incremental[k]==full[k] for k in ('status','physical_edge_ids','cost','delay'));changed=any(previous[k]!=full[k] for k in ('status','physical_edge_ids','cost','delay'));changed_results+=changed
   pathnodes={r['source']}
   for eid in previous['physical_edge_ids'] or ():pathnodes.update(edge[eid])
   if changed and not dirty&pathnodes:path_only_misses+=1
   records.append({'connection_id':r['connection_id'],'cost_read_nodes':len(footprint),'changed_other_net_nodes':len(dirty),'recomputed':affected,'result_changed':changed})
  (dest/'queries.json').write_text(json.dumps(records)+'\n');report={'design':name,'queries':len(records),'retained':retained,'recomputed':recomputed,'changed_results':changed_results,'path_only_dependency_false_negatives':path_only_misses,'full_replay_equal':True,'wall_s':time.monotonic()-start,'query_report_sha256':sha(dest/'queries.json'),'old_receipt_sha256':sha(baseline/'receipt.json'),'new_receipt_sha256':sha(newroot/'receipt.json')};reports.append(report);print(json.dumps(report),flush=True)
 assert all(sha(out/'sources'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
