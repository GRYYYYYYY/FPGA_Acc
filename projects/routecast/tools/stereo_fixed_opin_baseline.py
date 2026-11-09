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
 b=pathlib.Path('experiments/stereo_prospective_validation_2026-10-05');out=b/'fixed_opin_original_budget_baseline';out.mkdir();(out/'source').mkdir()
 affected=b/'additional_high_fanout_physical_audit/affected_conflict_connections.json';budgets=b/'additional_high_fanout_exact_budgets/budgets.json';witness=b/'full_path_pin_witness/witness.json';exact=b/'exact_buffered_rc_classes_v2';csr=b/'streaming_csr_class_cache_v3/csr'
 names=['stereo_fixed_opin_baseline.py','fixed_opin_search.py','csr_integer_exact_delay.py','csr_exact_buffered_rc.py','buffered_rc_context.py','buffered_rc_node_classes.py','prepared_csr.py','pre_route_endpoints.py'];sources={n:sha(pathlib.Path('tools')/n) for n in names}
 for n in names:shutil.copyfile(pathlib.Path('tools')/n,out/'source'/n)
 inputs={str(p):sha(p) for p in [affected,budgets,witness,exact/'receipt.json',csr/'manifest.json']};requests=json.loads(affected.read_text())['affected_connections'];budgetmap={r['connection_id']:Fraction(r['delay_seconds_numerator'],r['delay_seconds_denominator']) for r in json.loads(budgets.read_text())};pins={(r['connection_id'],r['role']):r['actual_pin_node'] for r in json.loads(witness.read_text())}
 protocol={'inputs':inputs,'sources':sources,'connection_ids':[r['connection_id'] for r in requests],'max_nodes':3593250,'scope':'existing OPIN/IPIN, no conflict blocks, original strict budgets; interface regression only; no repair/ownership/STA claim'};(out/'protocol.json').write_text(json.dumps(protocol,indent=2)+'\n');start=time.monotonic()
 graph=json.loads((exact/'protocol.json').read_text())['graph']['sha256'];_,f=read(csr,graph);ids,classes,switches=load(exact,graph);rc=ExactBufferedRC(f,ids,classes,switches);context=IntegerRC(rc);results=[]
 for row in requests:
  cid=row['connection_id'];source=row['source'];sink=row['sink'];opin=pins[cid,'SOURCE'];ipin=pins[cid,'SINK'];budget=budgetmap[cid];assert rc.path(source,sink,row['physical_edge_ids'])==budget
  def allowed(n,i):
   d=f['dest_ranks'][i]
   if f['capacities'][d]==0:return False
   if n==source:return d==opin
   if n==ipin:return d==sink
   return (n==opin or f['types'][n] in (TYPES['CHANX'],TYPES['CHANY'])) and (d==ipin or f['types'][d] in (TYPES['CHANX'],TYPES['CHANY']))
  result=fixed_opin_query(context,source,sink,opin,budget,allowed,max_nodes=3593250);assert result['status']=='FOUND'
  result['delay']=[result['delay'].numerator,result['delay'].denominator];result['connection_id']=cid;results.append(result);print(json.dumps({'connection_id':cid,'status':result['status'],'settled_nodes':result['settled_nodes']}),flush=True)
 assert all(sha(pathlib.Path(p))==h for p,h in inputs.items());assert all(sha(pathlib.Path('tools')/n)==h for n,h in sources.items())
 (out/'results.json').write_text(json.dumps(results,indent=2)+'\n');receipt={'queries':len(results),'all_found_within_original_budget':True,'protocol_sha256':sha(out/'protocol.json'),'results_sha256':sha(out/'results.json'),'wall_s':time.monotonic()-start,'scope':protocol['scope']};(out/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt),flush=True)
if __name__=='__main__':main()
