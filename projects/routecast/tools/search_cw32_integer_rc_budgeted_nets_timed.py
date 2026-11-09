"""Full fixed cohort exact connection-RC constrained congestion search."""
import json,time,shutil,os
from pathlib import Path
from fractions import Fraction
from collections import Counter,defaultdict
from prepared_csr import read,U64
from pre_route_endpoints import sha
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from csr_integer_budget_search import query
from integer_rc_context import IntegerRC
from streaming_prediction_audit import verify

def main():
 root=Path(__file__).resolve().parents[1];out=Path(os.environ['ROUTECAST_FRESH_OUTPUT']);out.mkdir();(out/'sources').mkdir()
 names=('search_cw32_integer_rc_budgeted_nets_timed.py','csr_integer_budget_search.py','integer_rc_context.py','csr_exact_buffered_rc.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','pre_route_endpoints.py','streaming_prediction_audit.py','physical_prediction_audit.py','net_union_topology.py')
 for n in names:shutil.copyfile(root/'tools'/n,out/'sources'/n)
 protocol={'cohort':[f'mult_{w}x{w}' for w in range(4,10)],'sources':{n:sha(out/'sources'/n) for n in names},'rounds':1,'order':'ascending NET/CID; staged wholeNET commit only if all connections FOUND and total uniqueNET overflow does not increase','objective':'scalar_proxy * (1+otherNET demand), nonnegative integer; full positive-capacity graph; no scalar budget','rc_budget':'fixed independent baseline exact buffered RC, integer lattice representation without rounding','max_labels_per_connection':10000,'scope':'One fixed development pass, no native timing/STA or pin assignment guarantee. LABEL_LIMIT retains old NET, is not infeasibility proof; no partial NET publication.'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');reports=[]
 for name in protocol['cohort']:
  start=time.monotonic();dest=out/name;dest.mkdir();front=root/'experiments/multiplier_family_endpoints_cw32_2026-10-06'/name;fp=json.loads((front/'protocol.json').read_text());graph=fp['inputs']['rr_graph'];ep=json.loads((front/'endpoints.json').read_text());baseline=root/'experiments/multiplier_family_predictions_cw32_2026-10-06'/name/'sparse_reset';br=json.loads((baseline/'receipt.json').read_text());assert sha(baseline/'prediction.json')==br['prediction_sha256'];old=json.loads((baseline/'prediction.json').read_text());context=root/'experiments/multiplier_cw32_exact_buffered_rc_classes_2026-10-06'/name;parity=json.loads((context/'baseline_parity.json').read_text());assert sha(context/'baseline_budgets.json')==parity['baseline_budgets_sha256'] and sha(baseline/'receipt.json')==parity['prediction_receipt_sha256'];budgets={r['connection_id']:Fraction(*r['exact_delay_s']) for r in json.loads((context/'baseline_budgets.json').read_text())};m,f=read(root/'experiments/multiplier_family_length_switch_csr_cw32_2026-10-06'/name/'csr',graph['sha256']);rc=ExactBufferedRC(f,*load(context,graph['sha256']));integer= IntegerRC(rc);edges={f['edge_ids'][slot]:(u,f['dest_ranks'][slot]) for u in range(m['nodes']) for slot in range(f['row_offsets'][u],f['row_offsets'][u+1])};groups=defaultdict(list)
  for r in old['connections']:groups[r['net_id']].append(r);assert rc.path(r['source'],r['sink'],r['physical_edge_ids'])==budgets[r['connection_id']]
  def union(rows):
   used=set()
   for r in rows:
    used.add(r['source'])
    for eid in r['physical_edge_ids']:used.update(edges[eid])
   return used
  active={r['connection_id']:r for r in old['connections']};unions={net:union(rows) for net,rows in groups.items()};occ=Counter(n for used in unions.values() for n in used);overflow=lambda values:sum(max(0,v-f['capacities'][n]) for n,v in values.items());initial=overflow(occ);decisions=[];statuses=Counter()
  with (dest/'queries.jsonl').open('w') as journal:
   for net,rows in sorted(groups.items()):
    other=occ.copy();other.subtract(unions[net]);assert all(v>=0 for v in other.values());candidate=[];allfound=True
    for r in rows:
     allowed=lambda u,slot:f['costs'][slot]!=U64 and f['capacities'][f['dest_ranks'][slot]]>0
     cost=lambda u,slot:int(f['costs'][slot])*(1+other[f['dest_ranks'][slot]])
     result=query(integer,r['source'],r['sink'],integer.encode(budgets[r['connection_id']]),allowed,cost,max_labels=10000);statuses[result['status']]+=1
     if result['status']=='FOUND':candidate.append({**r,'physical_edge_ids':result['physical_edge_ids'],'method':'rc_budgeted_net'});result['delay']=str(Fraction(result['delay'],integer.scale))
     else:allfound=False
     journal.write(json.dumps({'connection_id':r['connection_id'],'net_id':net,'result':result})+'\n');journal.flush()
    previous=overflow(occ);accepted=False;staged_overflow=None
    if allfound:
     newunion=union(candidate);staged=other.copy();staged.update(newunion);staged_overflow=overflow(staged)
     if staged_overflow<=previous:occ=staged;unions[net]=newunion;active.update({r['connection_id']:r for r in candidate});accepted=True
    decisions.append({'net_id':net,'all_found':allfound,'accepted':accepted,'previous_overflow':previous,'candidate_overflow':staged_overflow})
    print(json.dumps({'design':name,'net':net,'accepted':accepted,'overflow':overflow(occ),'queries':sum(statuses.values())}),flush=True)
  prediction={'physical_graph_sha256':graph['sha256'],'connections':[active[c] for c in sorted(active)],'node_occupancy':{str(n):v for n,v in occ.items() if v},'requested':len(active),'completed':len(active),'methods':dict(Counter(r['method'] for r in active.values()))};audit=verify(graph['path'],ep,prediction,topology=True);assert audit['all_physical_and_union_checks_passed'] and audit['all_type_overuse_units']==overflow(occ)
  for r in prediction['connections']:assert rc.path(r['source'],r['sink'],r['physical_edge_ids'])<=budgets[r['connection_id']]
  (dest/'prediction.json').write_text(json.dumps(prediction)+'\n');(dest/'audit.json').write_text(json.dumps(audit)+'\n');(dest/'decisions.json').write_text(json.dumps(decisions,indent=2)+'\n');report={'design':name,'connections':len(active),'statuses':dict(statuses),'accepted_nets':sum(r['accepted'] for r in decisions),'initial_overflow':initial,'final_overflow':overflow(occ),'all_final_rc_budgets_met':True,'wall_s':time.monotonic()-start,'prediction_sha256':sha(dest/'prediction.json'),'audit_sha256':sha(dest/'audit.json'),'queries_sha256':sha(dest/'queries.jsonl'),'decisions_sha256':sha(dest/'decisions.json')};reports.append(report);(dest/'receipt.json').write_text(json.dumps(report,indent=2)+'\n')
 assert all(sha(root/'tools'/n)==h for n,h in protocol['sources'].items());(out/'receipt.json').write_text(json.dumps({'protocol_sha256':sha(out/'protocol.json'),'results':reports},indent=2)+'\n')
if __name__=='__main__':main()
