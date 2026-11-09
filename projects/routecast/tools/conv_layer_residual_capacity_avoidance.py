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
 rows=[r for r in json.loads((parent/'prediction.json').read_text())['connections'] if r['connection_id'] in budgets]
 screen=base/'conv_layer_fixed_pin_residual_screen_2026-10-06/report.json';screen_data=json.loads(screen.read_text());assert screen_data['inputs_sha256'][str(parent/'prediction.json')]==pr['prediction_sha256']
 own_nodes=collections.defaultdict(set);occupancy=json.loads((parent/'prediction.json').read_text())['node_occupancy']
 for row in rows:
  used=own_nodes[row['net_id']];used.add(row['source'])
  for eid in row['physical_edge_ids']:used.add(f['dest_ranks'][slots[eid]])
 out=base/'conv_layer_residual_capacity_avoidance_2026-10-06';out.mkdir();(out/'source').mkdir()
 names=['conv_layer_residual_capacity_avoidance.py','prepared_csr.py','buffered_rc_context.py','buffered_rc_node_classes.py','csr_exact_buffered_rc.py','csr_exact_budget_search.py','pre_route_endpoints.py'];sources={n:sha(Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(Path('tools')/n,out/'source'/n)
 inputs={str(p):sha(p) for p in [parent/'receipt.json',parent/'prediction.json',budget/'receipt.json',budget/'budgets.json',context/'receipt.json',parity/'receipt.json',frontier,csr/'manifest.json',screen]}
 protocol={'inputs_sha256':inputs,'source_sha256':sources,'graph':graph,'banned_channel_nodes':sorted(banned),'pareto_label_limit':m['nodes'],'objective':'minimum additive per-path channel span under exact original RC budget; shared net union assessed separately','order':'ascending CID','policy':'original SOURCE/actual OPIN/actual IPIN/SINK; original exact RC path budget; remove complete original net union; all other predicted net ownership fixed; residual capacity mandatory','scope':'single-connection budgeted channel-span Pareto diagnostic; LABEL_LIMIT is unknown, no exhaustive Pareto-capacity claim; no joint tree, STA, global occupancy acceptance or repair'}
 (out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic();statuses=collections.Counter()
 with (out/'queries.jsonl').open('w') as journal:
  for row in sorted(rows,key=lambda r:r['connection_id']):
   source=row['source'];sink=row['sink'];path=row['physical_edge_ids'];assert rc.path(source,sink,path)==budgets[row['connection_id']]
   opin=f['dest_ranks'][slots[path[0]]];ipin=f['dest_ranks'][slots[path[-2]]];assert f['types'][opin]==2 and f['types'][ipin]==3
   def allowed(node,slot):
    dest=f['dest_ranks'][slot];kind=f['types'][dest]
    if f['costs'][slot]==U64 or not f['capacities'][dest] or dest in banned:return False
    if occupancy.get(str(dest),0)-(dest in own_nodes[row['net_id']])>=f['capacities'][dest]:return False
    if node==source:return dest==opin
    if kind in (4,5):return f['types'][node] in (2,4,5)
    if kind==3:return dest==ipin and f['types'][node] in (2,4,5)
    return kind==1 and dest==sink and node==ipin
   def cost(node,slot):
    dest=f['dest_ranks'][slot]
    return max(f['xhigh'][dest]-f['xlow'][dest],f['yhigh'][dest]-f['ylow'][dest])+1 if f['types'][dest] in (4,5) else 0
   if not screen_data['whole_nets'][str(row['net_id'])]['all_fixed_pin_conditions_pass']:
    result={'status':'FIXED_PIN_CAPACITY_BLOCKED','physical_edge_ids':None,'delay':None,'cost':None}
   else:result=query(rc,source,sink,budgets[row['connection_id']],allowed,cost,max_labels=m['nodes'])
   statuses[result['status']]+=1
   if result['status']=='FOUND':
    current=source
    for eid in result['physical_edge_ids']:
     slot=slots[eid];assert f['row_offsets'][current]<=slot<f['row_offsets'][current+1] and allowed(current,slot);current=f['dest_ranks'][slot]
    assert current==sink
   if isinstance(result.get('delay'),Fraction):result['delay']=[result['delay'].numerator,result['delay'].denominator]
   record={'connection_id':row['connection_id'],'net_id':row['net_id'],'source':source,'sink':sink,'original_opin':opin,'original_ipin':ipin,'result':result};journal.write(json.dumps(record)+'\n');journal.flush();print(json.dumps({'completed':sum(statuses.values()),'total':75,'statuses':dict(statuses)}),flush=True)
 assert all(sha(p)==h for p,h in inputs.items()) and all(sha(Path('tools')/n)==h for n,h in sources.items())
 receipt={'queries':75,'statuses':dict(statuses),'wall_s':time.monotonic()-start,'protocol_sha256':sha(out/'protocol.json'),'journal_sha256':sha(out/'queries.jsonl'),'repair_committed':False,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':run()
