"""Existing-OPIN strict original-budget real-graph interface validation."""
import json,pathlib,time,shutil
from fractions import Fraction
from prepared_csr import read,TYPES
from pre_route_endpoints import sha
from buffered_rc_context import load
from csr_exact_buffered_rc import ExactBufferedRC
from csr_integer_exact_delay import IntegerRC
from fixed_opin_search import fixed_opin_query

def main():
 b=pathlib.Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'fixed_opin_candidate_matrix';out.mkdir();(out/'source').mkdir()
 affected=b/'additional_high_fanout_physical_audit/affected_conflict_connections.json';budgets=b/'additional_high_fanout_exact_budgets/budgets.json';witness=b/'full_path_pin_witness/witness.json';exact=b/'exact_buffered_rc_classes_v2';csr=b/'streaming_csr_class_cache_v3/csr'
 names=['stereo_fixed_opin_candidate_matrix.py','fixed_opin_search.py','csr_integer_exact_delay.py','csr_exact_buffered_rc.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','pre_route_endpoints.py'];sources={n:sha(pathlib.Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(pathlib.Path('tools')/n,out/'source'/n)
 catalogpath=b/'source_opin_catalog/catalog.json';catalogreceipt=b/'source_opin_catalog/receipt.json';catalog={v['source_class']:v for v in json.loads(catalogpath.read_text())};assert sha(catalogpath)==json.loads(catalogreceipt.read_text())['catalog_sha256'];inputs={str(p):sha(p) for p in [affected,budgets,witness,exact/'receipt.json',csr/'manifest.json',catalogpath,catalogreceipt]};requests=json.loads(affected.read_text())['affected_connections'];budgetmap={r['connection_id']:Fraction(r['delay_seconds_numerator'],r['delay_seconds_denominator']) for r in json.loads(budgets.read_text())};pins={(r['connection_id'],r['role']):r['actual_pin_node'] for r in json.loads(witness.read_text())}
 protocol={'inputs':inputs,'sources':sources,'connection_ids':[r['connection_id'] for r in requests],'candidate_order':'ascending raw OPIN node ID, all class members','max_nodes':3593250,'scope':'all direct class OPINs, fixed original IPIN, no conflict blocks, original strict budgets; per-connection candidate diagnostic only; no repair/ownership/STA claim'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
 graph=json.loads((exact/'protocol.json').read_text())['graph']['sha256'];_,f=read(csr,graph);ids,classes,switches=load(exact,graph);rc=ExactBufferedRC(f,ids,classes,switches);context=IntegerRC(rc);results=[]
 for row in requests:
  cid=row['connection_id'];source=row['source'];sink=row['sink'];opin=pins[cid,'SOURCE'];ipin=pins[cid,'SINK'];budget=budgetmap[cid];assert rc.path(source,sink,row['physical_edge_ids'])==budget
  original_opin=opin
  for member in catalog[source]['pins']:
   opin=member['node'];assert any(f['dest_ranks'][i]==opin for i in range(f['row_offsets'][source],f['row_offsets'][source+1]))
   def allowed(n,i):
    d=f['dest_ranks'][i]
    if f['capacities'][d]==0:return False
    if n==source:return d==opin
    if n==ipin:return d==sink
    return (n==opin or f['types'][n] in (TYPES['CHANX'],TYPES['CHANY'])) and (d==ipin or f['types'][d] in (TYPES['CHANX'],TYPES['CHANY']))
   result=fixed_opin_query(context,source,sink,opin,budget,allowed,max_nodes=3593250)
   if opin==original_opin:assert result['status']=='FOUND'
   if result['delay'] is not None:result['delay']=[result['delay'].numerator,result['delay'].denominator]
   result.update(connection_id=cid,net_id=row['net_id'],opin=opin,original_opin=original_opin,original_budget=[budget.numerator,budget.denominator]);results.append(result)
   (out/'progress.json').write_text(json.dumps({'queries':len(results),'last_connection_id':cid,'last_opin':opin,'last_status':result['status']})+'\n')
   (out/'results.json').write_text(json.dumps(results,indent=2)+'\n')
  print(json.dumps({'connection_id':cid,'candidate_opins':len(catalog[source]['pins']),'status_counts':{status:sum(v['status']==status and v['connection_id']==cid for v in results) for status in ['FOUND','UNREACHABLE','NODE_LIMIT']}}),flush=True)
 assert all(sha(pathlib.Path(p))==h for p,h in inputs.items());assert all(sha(pathlib.Path('tools')/n)==h for n,h in sources.items())
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n');receipt={'queries':len(results),'status_counts':{status:sum(v['status']==status for v in results) for status in ['FOUND','UNREACHABLE','NODE_LIMIT']},'original_opin_baselines_found':True,'protocol_sha256':sha(out/'protocol.json'),'results_sha256':sha(out/'results.json'),'wall_s':time.monotonic()-start,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
