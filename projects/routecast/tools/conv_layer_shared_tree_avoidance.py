"""Fixed original pins, exact original budget, optimistic channel avoidance diagnostic."""
import json,time,shutil,collections
from pathlib import Path
from array import array
from fractions import Fraction
from prepared_csr import read,U64
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from csr_exact_budget_search import query
from pre_route_endpoints import sha

def run():
 base=Path('experiments');parent=base/'conv_layer_length_switch_prediction_v2_2026-10-06';csr=base/'conv_layer_length_switch_csr_2026-10-06/csr';context=base/'conv_layer_exact_buffered_rc_classes_2026-10-06';budget=base/'conv_layer_channel_frontier_exact_budgets_2026-10-06';parity=base/'conv_layer_frontier_budget_parity_2026-10-06';frontier=base/'conv_layer_channel_conflict_frontier_v2_2026-10-06/report.json'
 pp=json.loads((parent/'protocol.json').read_text());pr=json.loads((parent/'receipt.json').read_text());check=json.loads((parity/'receipt.json').read_text())
 assert check['all_original_xml_budgets_match_prepared_electrical_replay'] and check['budget_receipt_sha256']==sha(budget/'receipt.json') and check['context_receipt_sha256']==sha(context/'receipt.json') and check['prediction_receipt_sha256']==sha(parent/'receipt.json')
 assert sha(parent/'prediction.json')==pr['prediction_sha256'] and pr['protocol_sha256']==sha(parent/'protocol.json')
 selection=json.loads(frontier.read_text());assert selection['prediction_sha256']==pr['prediction_sha256'];banned={r['node'] for r in selection['resources']}
 graph=pp['inputs']['graph'];assert sha(graph['path'])==graph['sha256'];m,f=read(csr,graph['sha256']);assert sha(csr/'manifest.json')==pp['csr_manifest_sha256'];rc=ExactBufferedRC(f,*load(context,graph['sha256']))
 slots=array('Q',[0])*m['edges']
 for slot,eid in enumerate(f['edge_ids']):slots[eid]=slot
 budgets={r['connection_id']:Fraction(r['delay_seconds_numerator'],r['delay_seconds_denominator']) for r in json.loads((budget/'budgets.json').read_text())};assert set(budgets)==set(selection['whole_net_connection_ids']) and len(budgets)==75
 rows=[r for r in json.loads((parent/'prediction.json').read_text())['connections'] if r['connection_id'] in budgets and r['net_id'] in (5376,7312)]
 assert len(rows)==17
 shared_nodes=collections.defaultdict(set);shared_edges=collections.defaultdict(set)
 out=base/'conv_layer_shared_tree_avoidance_2026-10-06';out.mkdir();(out/'source').mkdir()
 names=['conv_layer_shared_tree_avoidance.py','prepared_csr.py','buffered_rc_context.py','buffered_rc_node_classes.py','csr_exact_buffered_rc.py','csr_exact_budget_search.py','pre_route_endpoints.py'];sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 inputs={str(p):sha(p) for p in [parent/'receipt.json',parent/'prediction.json',budget/'receipt.json',budget/'budgets.json',context/'receipt.json',parity/'receipt.json',frontier,csr/'manifest.json',base/'conv_layer_avoidance_span_lower_bounds_2026-10-06/report.json',base/'conv_layer_avoidance_span_lower_bounds_2026-10-06/receipt.json']}
 protocol={'inputs_sha256':inputs,'source_sha256':sources,'graph':graph,'banned_channel_nodes':sorted(banned),'pareto_label_limit':m['nodes'],'objective':'greedy minimum incremental net-union channel span per connection under original exact RC budget; existing shared tree has zero incremental objective','order':'ascending CID','policy':'original SOURCE/actual OPIN/actual IPIN/SINK; original exact RC path budget; all other occupancy relaxed; nets 5376/7312 selected by prior lower-bound diagnostic; ascending CID greedy shared tree; entering existing tree only on an existing tree edge','scope':'development greedy shared-tree diagnostic; LABEL_LIMIT unknown; not global joint-tree optimum, occupancy acceptance, STA or repair'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();statuses=collections.Counter()
 with (out/'queries.jsonl').open('w') as journal:
  for row in sorted(rows,key=lambda r:r['connection_id']):
   source=row['source'];sink=row['sink'];path=row['physical_edge_ids'];assert rc.path(source,sink,path)==budgets[row['connection_id']]
   opin=f['dest_ranks'][slots[path[0]]];ipin=f['dest_ranks'][slots[path[-2]]];assert f['types'][opin]==2 and f['types'][ipin]==3
   prior_nodes=shared_nodes[row['net_id']];prior_edges=shared_edges[row['net_id']]
   def allowed(node,slot):
    dest=f['dest_ranks'][slot];kind=f['types'][dest]
    if f['costs'][slot]==U64 or not f['capacities'][dest] or dest in banned:return False
    if dest in prior_nodes and f['edge_ids'][slot] not in prior_edges:return False
    if node==source:return dest==opin
    if kind in (4,5):return f['types'][node] in (2,4,5)
    if kind==3:return dest==ipin and f['types'][node] in (2,4,5)
    return kind==1 and dest==sink and node==ipin
   def cost(node,slot):
    dest=f['dest_ranks'][slot]
    return max(f['xhigh'][dest]-f['xlow'][dest],f['yhigh'][dest]-f['ylow'][dest])+1 if f['types'][dest] in (4,5) and dest not in prior_nodes else 0
   result=query(rc,source,sink,budgets[row['connection_id']],allowed,cost,max_labels=m['nodes']);statuses[result['status']]+=1
   if result['status']=='FOUND':
    current=source
    for eid in result['physical_edge_ids']:
     slot=slots[eid];assert f['row_offsets'][current]<=slot<f['row_offsets'][current+1] and allowed(current,slot);current=f['dest_ranks'][slot]
    assert current==sink
    current=source;added={source}
    for eid in result['physical_edge_ids']:current=f['dest_ranks'][slots[eid]];added.add(current)
    actual_increment=sum(max(f['xhigh'][n]-f['xlow'][n],f['yhigh'][n]-f['ylow'][n])+1 for n in added-prior_nodes if f['types'][n] in (4,5))
    assert actual_increment==result['cost']
    prior_nodes.update(added);prior_edges.update(result['physical_edge_ids'])
   if isinstance(result.get('delay'),Fraction):result['delay']=[result['delay'].numerator,result['delay'].denominator]
   record={'connection_id':row['connection_id'],'net_id':row['net_id'],'source':source,'sink':sink,'original_opin':opin,'original_ipin':ipin,'result':result};journal.write(json.dumps(record)+'\n');journal.flush();print(json.dumps({'completed':sum(statuses.values()),'total':17,'statuses':dict(statuses)}),flush=True)
 assert all(sha(p)==h for p,h in inputs.items()) and all(sha(Path('tools')/n)==h for n,h in sources.items())
 receipt={'queries':17,'statuses':dict(statuses),'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'journal_sha256':sha(out/'queries.jsonl'),'repair_committed':False,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
